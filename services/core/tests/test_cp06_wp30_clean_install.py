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
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            return tuple(
                tuple(tuple(row) for row in connection.execute(text(f"SELECT * FROM {table} ORDER BY 1")).fetchall())
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
    engine.dispose()


def test_backup_restore_downgrade_reupgrade_preserves_old_history(tmp_path: Path) -> None:
    db_path = tmp_path / "wp30.db"
    backup_path = tmp_path / "wp30.before-head.db"
    _upgrade(db_path, "0001")
    _seed_legacy_history(db_path)
    before = _history(db_path)

    shutil.copy2(db_path, backup_path)
    _upgrade(db_path, "head")
    assert _version(db_path) == "0002"
    assert _history(db_path) == before

    alembic_cmd.downgrade(_alembic_config(db_path), "0001")
    assert _version(db_path) == "0001"
    assert _history(db_path) == before

    shutil.copy2(backup_path, db_path)
    assert _version(db_path) == "0001"
    _upgrade(db_path, "head")
    assert _version(db_path) == "0002"
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
