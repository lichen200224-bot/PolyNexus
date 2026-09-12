"""G17 Alembic authority and isolated backup/restore acceptance tests."""
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


def _app_with_database(monkeypatch, db_path: Path):
    from polynexus_core.app import create_app
    from polynexus_core.persistence.database import dispose_engine

    dispose_engine()
    monkeypatch.setenv("POLYNEXUS_DATABASE_URL", f"sqlite:///{db_path}")
    return create_app(), dispose_engine


def test_startup_rejects_an_unversioned_database(tmp_path: Path, monkeypatch) -> None:
    app, dispose_engine = _app_with_database(
        monkeypatch, tmp_path / "unversioned.db"
    )
    try:
        with pytest.raises(RuntimeError, match="Alembic"):
            with TestClient(app):
                pass
    finally:
        dispose_engine()


def test_startup_rejects_a_non_head_database(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "non-head.db"
    _upgrade(db_path, "0001")
    app, dispose_engine = _app_with_database(monkeypatch, db_path)
    try:
        with pytest.raises(RuntimeError, match="not at the Alembic head"):
            with TestClient(app):
                pass
    finally:
        dispose_engine()


def test_isolated_backup_restore_and_reupgrade_preserve_history(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "legacy.db"
    backup_path = tmp_path / "legacy.before-migration.db"
    _upgrade(db_path, "0001")
    _seed_legacy_history(db_path)
    before = _history(db_path)

    shutil.copy2(db_path, backup_path)
    _upgrade(db_path, "head")
    assert _version(db_path) == "0003"
    _assert_ordering_metadata(db_path, "run-g17", "event-g17")
    assert _history(db_path) == before
    assert _snapshot_exists(db_path)

    # Restore the pre-migration bytes, then prove the same database can be
    # upgraded again without losing old projects, runs, events, or evidence.
    shutil.copy2(backup_path, db_path)
    assert _version(db_path) == "0001"
    assert _metadata_schema(db_path) == {"runs": {}, "run_events": {}}
    assert _history(db_path) == before

    _upgrade(db_path, "head")
    assert _version(db_path) == "0003"
    _assert_ordering_metadata(db_path, "run-g17", "event-g17")
    assert _history(db_path) == before
    assert _snapshot_exists(db_path)


def _seed_legacy_history(db_path: Path) -> None:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO projects (id, name, description, created_at) "
                "VALUES (:id, :name, NULL, :created_at)"
            ),
            {
                "id": "proj-g17",
                "name": "G17 legacy project",
                "created_at": "2026-09-01 00:00:00.000000",
            },
        )
        connection.execute(
            text(
                "INSERT INTO tasks (id, project_id, title, workflow_id, "
                "workflow_version, mode, context_package_id, created_at) "
                "VALUES (:id, :project_id, :title, :workflow_id, 1, 'REVIEW', "
                "NULL, :created_at)"
            ),
            {
                "id": "task-g17",
                "project_id": "proj-g17",
                "title": "G17 legacy task",
                "workflow_id": "review-minimal",
                "created_at": "2026-09-01 00:00:01.000000",
            },
        )
        connection.execute(
            text(
                "INSERT INTO runs (id, task_id, workflow_id, workflow_version, "
                "context_package_id, execution_target, resume_mode, state, "
                "runtime_ref, created_at, updated_at) VALUES "
                "('run-g17', 'task-g17', 'review-minimal', 1, 'cp-g17', "
                "'LOCAL', 'NONE', 'COMPLETED', NULL, "
                "'2026-09-01 00:00:02.000000', '2026-09-01 00:00:03.000000')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO run_events (id, run_id, from_state, to_state, "
                "occurred_at, reason) VALUES "
                "('event-g17', 'run-g17', 'CREATED', 'STARTING', "
                "'2026-09-01 00:00:02.500000', NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO evidence (id, task_id, run_id, actor_id, source, "
                "type, status, artifact_refs, metadata_json, observed_at) "
                "VALUES ('evidence-g17', 'task-g17', 'run-g17', 'system:g17', "
                "'g17-test', 'RUNTIME_EVIDENCE', 'OBSERVED', '[]', '{}', "
                "'2026-09-01 00:00:04.000000')"
            )
        )
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
                tuple(
                    tuple(row)
                    for row in connection.execute(
                        text(f"SELECT {legacy_columns.get(table, '*')} FROM {table} ORDER BY 1")
                    ).fetchall()
                )
                for table in ("projects", "tasks", "runs", "run_events", "evidence")
            )
    finally:
        engine.dispose()


def _version(db_path: Path) -> str | None:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            return connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one_or_none()
    finally:
        engine.dispose()


def _snapshot_exists(db_path: Path) -> bool:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            return (
                connection.execute(
                    text(
                        "SELECT 1 FROM run_binding_snapshots "
                        "WHERE run_id = 'run-g17'"
                    )
                ).scalar_one_or_none()
                == 1
            )
    finally:
        engine.dispose()


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
