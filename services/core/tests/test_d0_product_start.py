"""Bounded D0 startup, SQLite-integrity, and layered-health acceptance tests."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest
from alembic import command as alembic_cmd
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import polynexus_core.api.dependencies as dependencies_module
import polynexus_core.persistence.database as database_module
from polynexus_core.app import create_app
from polynexus_core.persistence.database import (
    audit_relationships,
    dispose_engine,
    get_engine,
    init_engine,
    verify_relationship_integrity,
)


def _upgrade_to_head(db_path: Path) -> None:
    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).parent.parent / "alembic")
    )
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    alembic_cmd.upgrade(config, "head")


@pytest.fixture(autouse=True)
def _dispose_global_engine():
    dispose_engine()
    yield
    dispose_engine()


def test_sqlite_fk_is_enabled_per_connection_without_forcing_wal(tmp_path: Path) -> None:
    db_path = tmp_path / "ordinary.db"
    _upgrade_to_head(db_path)

    init_engine(f"sqlite:///{db_path}")
    engine = get_engine()
    for _ in range(2):
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
            assert connection.exec_driver_sql("PRAGMA journal_mode").scalar_one() != "wal"

    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO tasks "
                    "(id, project_id, title, workflow_id, workflow_version, mode, created_at) "
                    "VALUES ('task-dangling', 'missing', 'bad', 'review-minimal', 1, "
                    "'REVIEW', CURRENT_TIMESTAMP)"
                )
            )


def test_in_memory_sqlite_fk_is_enabled() -> None:
    init_engine("sqlite:///:memory:")
    with get_engine().connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1


def test_non_sqlite_url_is_not_classified_by_filename(monkeypatch) -> None:
    captured: dict[str, object] = {}
    fake_engine = SimpleNamespace(
        dialect=SimpleNamespace(name="postgresql"),
        dispose=lambda: None,
    )

    def _fake_create_engine(url, **kwargs):
        captured.update(url=url, **kwargs)
        return fake_engine

    monkeypatch.setattr(database_module, "create_engine", _fake_create_engine)
    init_engine("postgresql://localhost/database-with-sqlite.db")

    assert captured["connect_args"] == {}


def test_relationship_audit_detects_fk_damage_without_mutating(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-fk-damage.db"
    _upgrade_to_head(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO tasks "
            "(id, project_id, title, workflow_id, workflow_version, mode, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            ("task-dangling", "project-missing", "legacy", "review-minimal", 1, "REVIEW"),
        )
        connection.commit()
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()

    init_engine(f"sqlite:///{db_path}")
    audit = audit_relationships()
    after = hashlib.sha256(db_path.read_bytes()).hexdigest()

    assert not audit.clean
    assert any(
        item.source_table == "tasks" and item.target_table == "projects"
        for item in audit.foreign_key_violations
    )
    assert before == after
    with sqlite3.connect(db_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM tasks WHERE id = 'task-dangling'"
        ).fetchone() == (1,)
    with pytest.raises(RuntimeError, match="relationship integrity audit failed"):
        verify_relationship_integrity()


def test_relationship_audit_detects_application_reference_without_deleting(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "legacy-application-damage.db"
    _upgrade_to_head(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "INSERT INTO projects (id, name, created_at) "
            "VALUES ('project-1', 'Project', CURRENT_TIMESTAMP)"
        )
        connection.execute(
            "INSERT INTO tasks "
            "(id, project_id, title, workflow_id, workflow_version, mode, created_at) "
            "VALUES ('task-1', 'project-1', 'Task', 'review-minimal', 1, "
            "'REVIEW', CURRENT_TIMESTAMP)"
        )
        connection.execute(
            "INSERT INTO runs "
            "(id, task_id, workflow_id, workflow_version, context_package_id, "
            "execution_target, resume_mode, state, created_at, updated_at) "
            "VALUES ('run-1', 'task-1', 'review-minimal', 1, 'context-missing', "
            "'LOCAL', 'NONE', 'CREATED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
        connection.commit()

    init_engine(f"sqlite:///{db_path}")
    audit = audit_relationships()

    assert not audit.clean
    assert any(
        item.source_table == "runs"
        and item.relation == "context_package_id"
        and item.target_identity == "context-missing"
        for item in audit.application_violations
    )
    with get_engine().connect() as connection:
        assert connection.execute(
            text("SELECT COUNT(*) FROM runs WHERE id = 'run-1'")
        ).scalar_one() == 1


def test_health_reports_layers_and_never_claims_unobserved_readiness(
    monkeypatch, tmp_path: Path
) -> None:
    db_path = tmp_path / "health.db"
    _upgrade_to_head(db_path)
    monkeypatch.setenv("POLYNEXUS_DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setattr(dependencies_module, "_LOOPBACK_TOKEN", "d0-test-token")

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["readiness"] == "partial"
    assert body["layers"]["process"]["status"] == "ready"
    assert body["layers"]["schema"]["status"] == "ready"
    assert body["layers"]["database_integrity"]["status"] == "ready"
    assert body["layers"]["core"]["status"] == "ready"
    assert body["layers"]["api_auth"]["status"] == "ready"
    assert body["layers"]["web_client"]["status"] == "unknown"
    assert body["layers"]["runtime"]["status"] == "unknown"


def test_health_is_not_ready_without_schema_or_auth(monkeypatch) -> None:
    monkeypatch.setattr(dependencies_module, "_LOOPBACK_TOKEN", "")
    init_engine("sqlite:///:memory:")

    from polynexus_core.api.health import health

    body = health()
    assert body["readiness"] == "not_ready"
    assert body["layers"]["schema"]["status"] == "not_ready"
    assert body["layers"]["api_auth"]["status"] == "not_ready"
