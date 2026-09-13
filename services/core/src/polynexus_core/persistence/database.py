from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from polynexus_core.persistence.models import Base

_engine = None
_session_factory = None
_ALEMBIC_DIR = Path(__file__).resolve().parents[3] / "alembic"
_SCHEMA_NOT_AT_HEAD = "Database schema is not at the Alembic head"
_SCHEMA_VERSION_UNAVAILABLE = "Database schema version could not be verified"
_RELATIONSHIP_INTEGRITY_FAILED = "Database relationship integrity audit failed"


@dataclass(frozen=True)
class RelationshipViolation:
    """One public-safe relationship violation found by the read-only audit."""

    source_table: str
    source_identity: str
    relation: str
    target_table: str
    target_identity: str | None


@dataclass(frozen=True)
class RelationshipAudit:
    """Read-only SQLite FK and application-owned relationship audit result."""

    foreign_key_violations: tuple[RelationshipViolation, ...]
    application_violations: tuple[RelationshipViolation, ...]

    @property
    def clean(self) -> bool:
        return not self.foreign_key_violations and not self.application_violations


_APPLICATION_RELATION_QUERIES = (
    (
        "tasks",
        "context_package_id",
        "context_packages",
        """
        SELECT task.id, task.context_package_id
        FROM tasks AS task
        LEFT JOIN context_packages AS context
          ON context.id = task.context_package_id
        WHERE task.context_package_id IS NOT NULL
          AND (context.id IS NULL OR context.project_id != task.project_id)
        """,
    ),
    (
        "runs",
        "context_package_id",
        "context_packages",
        """
        SELECT run.id, run.context_package_id
        FROM runs AS run
        JOIN tasks AS task ON task.id = run.task_id
        LEFT JOIN context_packages AS context
          ON context.id = run.context_package_id
        WHERE context.id IS NULL OR context.project_id != task.project_id
        """,
    ),
    (
        "artifacts",
        "task_id",
        "tasks",
        """
        SELECT artifact.id, artifact.task_id
        FROM artifacts AS artifact
        LEFT JOIN tasks AS task ON task.id = artifact.task_id
        WHERE artifact.task_id IS NOT NULL
          AND (task.id IS NULL OR task.project_id != artifact.project_id)
        """,
    ),
    (
        "artifacts",
        "run_id",
        "runs",
        """
        SELECT artifact.id, artifact.run_id
        FROM artifacts AS artifact
        LEFT JOIN runs AS run ON run.id = artifact.run_id
        LEFT JOIN tasks AS task ON task.id = run.task_id
        WHERE artifact.run_id IS NOT NULL
          AND (
            run.id IS NULL
            OR task.project_id != artifact.project_id
            OR (artifact.task_id IS NOT NULL AND artifact.task_id != run.task_id)
          )
        """,
    ),
    (
        "findings",
        "run_id",
        "runs",
        """
        SELECT finding.id, finding.run_id
        FROM findings AS finding
        LEFT JOIN runs AS run ON run.id = finding.run_id
        WHERE run.id IS NULL OR run.task_id != finding.task_id
        """,
    ),
    (
        "evidence",
        "run_id",
        "runs",
        """
        SELECT evidence.id, evidence.run_id
        FROM evidence AS evidence
        LEFT JOIN runs AS run ON run.id = evidence.run_id
        WHERE run.id IS NULL OR run.task_id != evidence.task_id
        """,
    ),
)

_RUN_RESULT_REFERENCE_SPECS = (
    ("result_finding_ids", "findings"),
    ("result_evidence_ids", "evidence"),
    ("result_artifact_ids", "artifacts"),
)


def init_engine(database_url: str | None = None) -> None:
    global _engine, _session_factory
    if database_url is None:
        database_url = "sqlite:///poly.db"
    is_sqlite = make_url(database_url).get_backend_name() == "sqlite"
    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if is_sqlite else {},
        future=True,
    )
    if _engine.dialect.name == "sqlite":
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)


def create_all() -> None:
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    Base.metadata.create_all(_engine)


def verify_schema_head() -> None:
    """Fail closed unless the initialized engine is at the Alembic head.

    Application startup never upgrades or creates schema implicitly.  The
    migration authority is discovered from the repository's Alembic script
    directory and compared with the single revision recorded in the target
    database.  All failures use bounded, public-safe messages.
    """
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")

    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        if not _ALEMBIC_DIR.is_dir():
            raise RuntimeError(_SCHEMA_VERSION_UNAVAILABLE)
        alembic_config = Config()
        alembic_config.set_main_option("script_location", str(_ALEMBIC_DIR))
        heads = tuple(ScriptDirectory.from_config(alembic_config).get_heads())
        if len(heads) != 1:
            raise RuntimeError(_SCHEMA_VERSION_UNAVAILABLE)

        if "alembic_version" not in inspect(_engine).get_table_names():
            raise RuntimeError(_SCHEMA_NOT_AT_HEAD)
        with _engine.connect() as connection:
            revisions = tuple(
                connection.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalars().all()
            )
        if revisions != heads:
            raise RuntimeError(_SCHEMA_NOT_AT_HEAD)
    except RuntimeError:
        raise
    except Exception:
        raise RuntimeError(_SCHEMA_VERSION_UNAVAILABLE) from None


def schema_head_status() -> bool:
    """Return only a safe schema-head result for internal diagnostics.

    The detailed startup gate remains ``verify_schema_head``.  This probe is
    intentionally boolean so Doctor cannot expose database URLs, filesystem
    paths, Alembic internals, or driver errors in its bounded report.
    """
    try:
        verify_schema_head()
    except Exception:
        return False
    return True


def audit_relationships() -> RelationshipAudit:
    """Inspect SQLite relationships without repairing or deleting any rows.

    The audit combines SQLite's authoritative ``foreign_key_check`` with the
    application-owned references that intentionally have no database FK.  It
    performs no backup and no repair: callers must take an external backup
    before using the result in any recovery workflow.
    """
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    if _engine.dialect.name != "sqlite":
        raise RuntimeError("Relationship audit is available only for SQLite")

    with _engine.connect() as connection:
        foreign_key_violations = tuple(
            RelationshipViolation(
                source_table=str(row[0]),
                source_identity=str(row[1]),
                relation=f"sqlite-fk:{row[3]}",
                target_table=str(row[2]),
                target_identity=None,
            )
            for row in connection.exec_driver_sql("PRAGMA foreign_key_check").all()
        )
        tables = set(inspect(connection).get_table_names())
        application_violations: list[RelationshipViolation] = []
        for source_table, relation, target_table, query in _APPLICATION_RELATION_QUERIES:
            if source_table not in tables or target_table not in tables:
                continue
            application_violations.extend(
                RelationshipViolation(
                    source_table=source_table,
                    source_identity=str(row[0]),
                    relation=relation,
                    target_table=target_table,
                    target_identity=None if row[1] is None else str(row[1]),
                )
                for row in connection.exec_driver_sql(query).all()
            )
        if "runs" in tables:
            application_violations.extend(
                _audit_run_result_references(connection, tables)
            )

    return RelationshipAudit(
        foreign_key_violations=foreign_key_violations,
        application_violations=tuple(application_violations),
    )


def _audit_run_result_references(connection, tables: set[str]) -> list[RelationshipViolation]:
    """Validate serialized RunResult IDs and their Run/Task ownership."""
    violations: list[RelationshipViolation] = []
    target_rows: dict[str, dict[str, tuple[str | None, str | None]]] = {}
    for _, target_table in _RUN_RESULT_REFERENCE_SPECS:
        if target_table not in tables:
            target_rows[target_table] = {}
            continue
        rows = connection.exec_driver_sql(
            f"SELECT id, task_id, run_id FROM {target_table}"
        ).all()
        target_rows[target_table] = {
            str(row[0]): (
                None if row[1] is None else str(row[1]),
                None if row[2] is None else str(row[2]),
            )
            for row in rows
        }

    run_rows = connection.exec_driver_sql(
        "SELECT id, task_id, result_finding_ids, result_evidence_ids, "
        "result_artifact_ids FROM runs"
    ).all()
    for row in run_rows:
        run_id = str(row[0])
        task_id = str(row[1])
        for index, (relation, target_table) in enumerate(
            _RUN_RESULT_REFERENCE_SPECS,
            start=2,
        ):
            try:
                references = json.loads(row[index])
            except (TypeError, ValueError, json.JSONDecodeError):
                references = None
            if (
                not isinstance(references, list)
                or any(not isinstance(item, str) or not item for item in references)
                or len(references) != len(set(references))
            ):
                violations.append(
                    RelationshipViolation(
                        source_table="runs",
                        source_identity=run_id,
                        relation=relation,
                        target_table=target_table,
                        target_identity=None,
                    )
                )
                continue
            for reference in references:
                ownership = target_rows[target_table].get(reference)
                if ownership != (task_id, run_id):
                    violations.append(
                        RelationshipViolation(
                            source_table="runs",
                            source_identity=run_id,
                            relation=relation,
                            target_table=target_table,
                            target_identity=reference,
                        )
                    )
    return violations


def relationship_integrity_status() -> bool:
    """Return a bounded readiness signal without exposing row identities."""
    try:
        return audit_relationships().clean
    except Exception:
        return False


def verify_relationship_integrity() -> None:
    """Fail startup closed when durable relationships cannot be trusted."""
    try:
        clean = audit_relationships().clean
    except Exception:
        raise RuntimeError(_RELATIONSHIP_INTEGRITY_FAILED) from None
    if not clean:
        raise RuntimeError(_RELATIONSHIP_INTEGRITY_FAILED)


def drop_all() -> None:
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    Base.metadata.drop_all(_engine)


def get_session() -> Generator[Session, None, None]:
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized. Call init_engine() first.")
    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_engine():
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine() first.")
    return _engine


def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _session_factory = None
