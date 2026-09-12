"""WP-23 isolated SQLite backup/restore and Alembic round-trip evidence."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from alembic import command as alembic_command
from alembic.config import Config
from sqlalchemy import create_engine, text

from polynexus_core.persistence.backup import (
    BackupRestoreError,
    create_sqlite_backup,
    restore_sqlite_backup,
)


ALEMBIC_DIR = Path(__file__).parent.parent / "alembic"


def _alembic_config(db_path: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(ALEMBIC_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def _upgrade(db_path: Path, revision: str) -> None:
    alembic_command.upgrade(_alembic_config(db_path), revision)


def _downgrade(db_path: Path, revision: str) -> None:
    alembic_command.downgrade(_alembic_config(db_path), revision)


def _history(db_path: Path) -> tuple[tuple[str, tuple[str, ...]], ...]:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            return tuple(
                (
                    table,
                    tuple(
                        row[0]
                        for row in connection.execute(
                            text(f"SELECT id FROM {table} ORDER BY id")
                        ).fetchall()
                    ),
                )
                for table in ("projects", "tasks", "runs", "run_events", "evidence")
            )
    finally:
        engine.dispose()


def _version(db_path: Path) -> str:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            return connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
    finally:
        engine.dispose()


def _seed_legacy_history(db_path: Path) -> None:
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO projects (id, name, description, created_at) "
                "VALUES ('proj-wp23', 'WP23 project', NULL, "
                "'2026-09-01 00:00:00.000000')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO tasks (id, project_id, title, workflow_id, "
                "workflow_version, mode, context_package_id, created_at) "
                "VALUES ('task-wp23', 'proj-wp23', 'WP23 task', "
                "'review-minimal', 1, 'REVIEW', NULL, "
                "'2026-09-01 00:00:01.000000')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO runs (id, task_id, workflow_id, workflow_version, "
                "context_package_id, execution_target, resume_mode, state, "
                "runtime_ref, created_at, updated_at) VALUES "
                "('run-wp23', 'task-wp23', 'review-minimal', 1, 'cp-wp23', "
                "'LOCAL', 'NONE', 'COMPLETED', NULL, "
                "'2026-09-01 00:00:02.000000', "
                "'2026-09-01 00:00:03.000000')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO run_events (id, run_id, from_state, to_state, "
                "occurred_at, reason) VALUES ('event-wp23', 'run-wp23', "
                "'CREATED', 'STARTING', '2026-09-01 00:00:02.500000', NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO evidence (id, task_id, run_id, actor_id, source, "
                "type, status, artifact_refs, metadata_json, observed_at) "
                "VALUES ('evidence-wp23', 'task-wp23', 'run-wp23', "
                "'system:wp23', 'wp23-test', 'RUNTIME_EVIDENCE', 'OBSERVED', "
                "'[]', '{}', '2026-09-01 00:00:04.000000')"
            )
        )
    engine.dispose()


def test_backup_restore_round_trip_preserves_legacy_history(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    backup_path = tmp_path / "legacy.before-migration.db"
    _upgrade(db_path, "0001")
    _seed_legacy_history(db_path)
    before = _history(db_path)

    receipt = create_sqlite_backup(db_path, backup_path)
    assert receipt.operation == "BACKUP"
    assert receipt.integrity == "ok"
    assert receipt.size_bytes > 0
    assert len(receipt.sha256) == 64

    _upgrade(db_path, "head")
    assert _version(db_path) == "0003"
    assert _history(db_path) == before

    _downgrade(db_path, "0001")
    assert _version(db_path) == "0001"
    assert _history(db_path) == before

    restored = restore_sqlite_backup(backup_path, db_path)
    assert restored.operation == "RESTORE"
    assert _version(db_path) == "0001"
    assert _history(db_path) == before

    _upgrade(db_path, "head")
    assert _version(db_path) == "0003"
    assert _history(db_path) == before
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    try:
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT 1 FROM run_binding_snapshots WHERE run_id = 'run-wp23'")
            ).scalar_one() == 1
    finally:
        engine.dispose()


def test_backup_rejects_non_temporary_database(tmp_path: Path) -> None:
    outside_temp = Path.cwd() / "wp23-not-a-real-database.db"
    with pytest.raises(BackupRestoreError) as error:
        create_sqlite_backup(outside_temp, tmp_path / "backup.db")
    assert error.value.code == "backup_not_isolated"


def test_backup_rejects_corrupt_sqlite(tmp_path: Path) -> None:
    source = tmp_path / "corrupt.db"
    source.write_bytes(b"not a sqlite database")
    with pytest.raises(BackupRestoreError) as error:
        create_sqlite_backup(source, tmp_path / "backup.db")
    assert error.value.code == "backup_integrity_failed"


def test_backup_receipt_does_not_include_database_path(tmp_path: Path) -> None:
    db_path = tmp_path / "small.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
        connection.commit()
    receipt = create_sqlite_backup(db_path, tmp_path / "small.backup")
    assert "small.db" not in repr(receipt)
    assert str(tmp_path) not in repr(receipt)
