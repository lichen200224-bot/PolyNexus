"""CP06 WP30 isolated migration, restore, and clean-install acceptance tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from alembic import command as alembic_cmd
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text


ALEMBIC_DIR = Path(__file__).parent.parent / "alembic"


def _alembic_config(db_path: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def _upgrade(db_path: Path, revision: str) -> None:
    alembic_cmd.upgrade(_alembic_config(db_path), revision)


def _version(db_path: Path) -> str | None:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            return connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    finally:
        engine.dispose()


def _history(db_path: Path) -> tuple[tuple[tuple[object, ...], ...], ...]:
    legacy_columns = {
        "runs": "id,task_id,workflow_id,workflow_version,context_package_id,execution_target,resume_mode,state,runtime_ref,created_at,updated_at,result_status,result_summary,result_finding_ids,result_evidence_ids,result_artifact_ids",
        "run_events": "id,run_id,from_state,to_state,occurred_at,reason",
    }
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            return tuple(
                tuple(tuple(row) for row in connection.execute(text(f"SELECT {legacy_columns.get(table, '*')} FROM {table} ORDER BY 1")).fetchall())
                for table in ("projects", "tasks", "runs", "run_events", "evidence")
            )
    finally:
        engine.dispose()


def _seed_legacy_history(db_path: Path) -> None:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO projects (id, name, description, created_at) "
                "VALUES ('proj-wp30', 'WP30 legacy project', NULL, '2026-09-01 00:00:00.000000')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO tasks (id, project_id, title, workflow_id, workflow_version, mode, context_package_id, created_at) "
                "VALUES ('task-wp30', 'proj-wp30', 'WP30 legacy task', 'review-minimal', 1, 'REVIEW', NULL, '2026-09-01 00:00:01.000000')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO runs (id, task_id, workflow_id, workflow_version, context_package_id, execution_target, resume_mode, state, runtime_ref, created_at, updated_at) "
                "VALUES ('run-wp30', 'task-wp30', 'review-minimal', 1, 'cp-wp30', 'LOCAL', 'NONE', 'COMPLETED', NULL, '2026-09-01 00:00:02.000000', '2026-09-01 00:00:03.000000')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO run_events (id, run_id, from_state, to_state, occurred_at, reason) "
                "VALUES ('event-wp30', 'run-wp30', 'CREATED', 'STARTING', '2026-09-01 00:00:02.500000', NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO evidence (id, task_id, run_id, actor_id, source, type, status, artifact_refs, metadata_json, observed_at) "
                "VALUES ('evidence-wp30', 'task-wp30', 'run-wp30', 'system:wp30', 'wp30-test', 'RUNTIME_EVIDENCE', 'OBSERVED', '[]', '{}', '2026-09-01 00:00:04.000000')"
            )
        )
        connection.exec_driver_sql("INSERT INTO context_packages(id,project_id,version,created_at) VALUES('cp-wp30','proj-wp30',1,'2026-01-01')")
    engine.dispose()


def test_backup_restore_downgrade_reupgrade_preserves_old_history(tmp_path: Path) -> None:
    db_path = tmp_path / "wp30.db"
    backup_path = tmp_path / "wp30.before-head.db"
    _upgrade(db_path, "0001")
    _seed_legacy_history(db_path)
    before = _history(db_path)

    # Preserve the historical 0003 downgrade/reupgrade contract exactly.
    # D1a head/restore is exercised separately in test_d1a_migration_restore.
    shutil.copy2(db_path, backup_path)
    _upgrade(db_path, "0003")
    assert _version(db_path) == "0003"
    _assert_ordering_metadata(db_path, "run-wp30", "event-wp30")
    assert _history(db_path) == before

    alembic_cmd.downgrade(_alembic_config(db_path), "0001")
    assert _version(db_path) == "0001"
    assert _metadata_schema(db_path) == {"runs": {}, "run_events": {}}
    assert _history(db_path) == before

    shutil.copy2(backup_path, db_path)
    assert _version(db_path) == "0001"
    assert _metadata_schema(db_path) == {"runs": {}, "run_events": {}}
    _upgrade(db_path, "0003")
    assert _version(db_path) == "0003"
    _assert_ordering_metadata(db_path, "run-wp30", "event-wp30")
    assert _history(db_path) == before


def test_clean_unversioned_database_is_rejected_by_application_startup(tmp_path: Path, monkeypatch) -> None:
    from polynexus_core.app import create_app
    from polynexus_core.persistence.database import dispose_engine

    dispose_engine()
    db_path = tmp_path / "wp30-clean.db"
    monkeypatch.setenv("POLYNEXUS_DATABASE_URL", f"sqlite:///{db_path}")
    app = create_app()
    try:
        with pytest.raises(RuntimeError, match="Alembic"):
            with TestClient(app):
                pass
    finally:
        dispose_engine()


def _metadata_schema(db_path: Path) -> dict:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            return {
                table: {row[1]: (row[2], row[3], row[4])
                        for row in connection.exec_driver_sql(f"PRAGMA table_info({table})")
                        if row[1] in names}
                for table, names in {
                    "runs": {"next_event_sequence"},
                    "run_events": {"event_sequence", "sequence_legacy_backfill"},
                }.items()
            }
    finally:
        engine.dispose()


def _assert_ordering_metadata(db_path: Path, run_id: str, event_id: str) -> None:
    # SQLite type, NOT NULL flag and server default are all exact expectations.
    assert _metadata_schema(db_path) == {
        "runs": {"next_event_sequence": ("INTEGER", 1, "0")},
        "run_events": {"event_sequence": ("INTEGER", 1, None),
                       "sequence_legacy_backfill": ("BOOLEAN", 1, "0")},
    }
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            assert connection.exec_driver_sql(
                "SELECT id,next_event_sequence FROM runs ORDER BY id"
            ).all() == [(run_id, 1)]
            assert connection.exec_driver_sql(
                "SELECT id,run_id,event_sequence,sequence_legacy_backfill "
                "FROM run_events ORDER BY run_id,event_sequence"
            ).all() == [(event_id, run_id, 1, 1)]
    finally:
        engine.dispose()


@pytest.mark.parametrize("revision, expected", [("0003", "0003"), ("head", "0010")])
def test_clean_head_ordering_defaults_and_required_sequence(tmp_path: Path, revision, expected) -> None:
    from sqlalchemy.exc import IntegrityError

    db_path = tmp_path / "fresh-ordering.db"
    _upgrade(db_path, revision)
    assert _version(db_path) == expected
    assert _metadata_schema(db_path) == {
        "runs": {"next_event_sequence": ("INTEGER", 1, "0")},
        "run_events": {"event_sequence": ("INTEGER", 1, None),
                       "sequence_legacy_backfill": ("BOOLEAN", 1, "0")},
    }
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql(
                "INSERT INTO projects(id,name,created_at) VALUES ('p','fresh','2026-09-12')")
            connection.exec_driver_sql(
                "INSERT INTO tasks(id,project_id,title,workflow_id,workflow_version,mode,created_at) "
                "VALUES ('t','p','fresh','review-minimal',1,'REVIEW','2026-09-12')")
            connection.exec_driver_sql(
                "INSERT INTO runs(id,task_id,workflow_id,workflow_version,context_package_id,"
                "execution_target,resume_mode,state,created_at,updated_at) "
                "VALUES ('r','t','review-minimal',1,'cp','LOCAL','NONE','CREATED','2026-09-12','2026-09-12')")
            assert connection.exec_driver_sql(
                "SELECT next_event_sequence FROM runs WHERE id='r'").scalar_one() == 0
            for invalid in [
                "UPDATE runs SET next_event_sequence=NULL WHERE id='r'",
                "INSERT INTO run_events(id,run_id,from_state,to_state,occurred_at) "
                "VALUES ('missing','r','CREATED','STARTING','2026-09-12')",
                "INSERT INTO run_events(id,run_id,from_state,to_state,occurred_at,event_sequence,sequence_legacy_backfill) "
                "VALUES ('null','r','CREATED','STARTING','2026-09-12',1,NULL)",
            ]:
                with pytest.raises(IntegrityError):
                    with connection.begin_nested():
                        connection.exec_driver_sql(invalid)
            # Exercise the production atomic allocation shape and server flag default.
            high = connection.exec_driver_sql(
                "UPDATE runs SET next_event_sequence=next_event_sequence+1 WHERE id='r' "
                "RETURNING next_event_sequence").scalar_one()
            assert high == 1
            connection.exec_driver_sql(
                "INSERT INTO run_events(id,run_id,from_state,to_state,occurred_at,event_sequence) "
                "VALUES ('new','r','CREATED','STARTING','2026-09-12',?)", (high,))
            assert connection.exec_driver_sql(
                "SELECT event_sequence,sequence_legacy_backfill FROM run_events WHERE id='new'"
            ).one() == (1, 0)
    finally:
        engine.dispose()
