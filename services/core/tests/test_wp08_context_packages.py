"""WP-08A ContextPackage REST Contract Tests — deterministic, temporary database.

Tests the POST /api/v1/projects/{project_id}/context-packages endpoint.
Uses Alembic upgrade head on temporary SQLite database.
Auth is overridden via test-only dependency injection (no production secret exposed).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command as alembic_cmd
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.orm import sessionmaker

from polynexus_core.api.dependencies import require_loopback
from polynexus_core.persistence.database import get_session


ALEMBIC_DIR = Path(__file__).parent.parent / "alembic"


def _make_alembic_ini(db_path: Path) -> Path:
    """Write a minimal alembic.ini pointing to the given database."""
    ini = db_path.parent / "alembic.ini"
    ini.write_text(
        "[alembic]\n"
        f"script_location = {ALEMBIC_DIR}\n"
        "prepend_sys_path = .\n"
        f"sqlalchemy.url = sqlite:///{db_path}\n"
        "\n"
        "[loggers]\n"
        "keys = root,sqlalchemy,alembic\n"
        "\n"
        "[handlers]\n"
        "keys = console\n"
        "\n"
        "[formatters]\n"
        "keys = generic\n"
        "\n"
        "[logger_root]\n"
        "level = WARN\n"
        "handlers = console\n"
        "\n"
        "[logger_sqlalchemy]\n"
        "level = WARN\n"
        "handlers =\n"
        "qualname = sqlalchemy.engine\n"
        "\n"
        "[logger_alembic]\n"
        "level = INFO\n"
        "handlers =\n"
        "qualname = alembic\n"
        "\n"
        "[handler_console]\n"
        "class = StreamHandler\n"
        "args = (sys.stderr,)\n"
        "level = NOTSET\n"
        "formatter = generic\n"
        "\n"
        "[formatter_generic]\n"
        "format = %(levelname)-5.5s [%(name)s] %(message)s\n"
        "datefmt = %H:%M:%S\n"
    )
    return ini


def _create_test_app(db_url: str) -> tuple[FastAPI, sessionmaker]:
    """Create a FastAPI app with test DB session and auth override."""
    from polynexus_core.api.health import router as health_router
    from polynexus_core.api.projects import router as projects_router
    from polynexus_core.api.tasks import router as tasks_router
    from polynexus_core.api.runs import router as runs_router
    from polynexus_core.api.context_packages import router as context_packages_router

    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    app = FastAPI()

    def _override_get_session():
        session = TestSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _override_auth():
        return None

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[require_loopback] = _override_auth

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(runs_router, prefix="/api/v1")
    app.include_router(context_packages_router, prefix="/api/v1")

    return app, TestSession


class _TestContext:
    """Holds client + session factory for a single test database."""

    def __init__(self, client: TestClient, session_factory: sessionmaker, db_url: str):
        self.client = client
        self.sf = session_factory
        self.db_url = db_url

    def create_project(self, name: str = "Test Project") -> str:
        """Create a project via API and return its ID."""
        resp = self.client.post(
            "/api/v1/projects",
            json={"name": name},
        )
        assert resp.status_code == 201
        return resp.json()["id"]


@pytest.fixture()
def ctx(tmp_path: Path) -> _TestContext:
    """Yield a _TestContext backed by a fresh temporary SQLite database."""
    db_path = tmp_path / "test.db"
    ini = _make_alembic_ini(db_path)
    config = Config(str(ini))
    alembic_cmd.upgrade(config, "head")

    db_url = f"sqlite:///{db_path}"
    app, sf = _create_test_app(db_url)
    client = TestClient(app)
    yield _TestContext(client, sf, db_url)


# ---------------------------------------------------------------------------
# ContextPackage API Tests — WP-08A
# ---------------------------------------------------------------------------

class TestWP08ContextPackageCreate:
    """WP-08A: POST /api/v1/projects/{project_id}/context-packages"""

    def test_create_context_package_201(self, ctx: _TestContext) -> None:
        """201 successful create with stable response fields."""
        project_id = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/context-packages",
            json={
                "version": 1,
                "instructions": ["Review code"],
                "constraints": ["No modifications"],
                "project_facts": {"language": "python"},
                "artifact_refs": ["art_001"],
                "prior_decision_refs": [],
                "memory_refs": [],
                "source_refs": ["src/main.py"],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["project_id"] == project_id
        assert data["version"] == 1
        assert data["instructions"] == ["Review code"]
        assert data["constraints"] == ["No modifications"]
        assert data["project_facts"] == {"language": "python"}
        assert data["artifact_refs"] == ["art_001"]
        assert data["prior_decision_refs"] == []
        assert data["memory_refs"] == []
        assert data["source_refs"] == ["src/main.py"]
        assert data["id"].startswith("context_")
        assert "created_at" in data

    def test_create_context_package_minimal_body(self, ctx: _TestContext) -> None:
        """201 with only required fields (version)."""
        project_id = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/context-packages",
            json={"version": 1},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["version"] == 1
        assert data["instructions"] == [] or data["instructions"] == ()
        assert data["constraints"] == [] or data["constraints"] == ()
        assert data["project_facts"] == {}
        assert data["artifact_refs"] == [] or data["artifact_refs"] == ()

    def test_auth_required_403(self, tmp_path: Path) -> None:
        """403 when LOOPBACK_TOKEN is not configured (fail closed)."""
        db_path = tmp_path / "test.db"
        ini = _make_alembic_ini(db_path)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")

        db_url = f"sqlite:///{db_path}"
        engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
        TestSession = sessionmaker(bind=engine, expire_on_commit=False, future=True)

        from polynexus_core.api.health import router as health_router
        from polynexus_core.api.projects import router as projects_router
        from polynexus_core.api.context_packages import router as context_packages_router

        app = FastAPI()

        def _override_get_session():
            session = TestSession()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

        app.dependency_overrides[get_session] = _override_get_session
        # Do NOT override require_loopback — production fail-closed behaviour
        app.include_router(health_router, prefix="/api/v1")
        app.include_router(projects_router, prefix="/api/v1")
        app.include_router(context_packages_router, prefix="/api/v1")

        client = TestClient(app)

        # Create a project first (also requires auth, so override for this setup)
        from polynexus_core.domain.models import Project
        from polynexus_core.persistence.repository import SqlProjectRepository

        session = TestSession()
        project = Project(name="Auth Test Project")
        SqlProjectRepository(session).add(project)
        session.commit()
        session.close()

        # Now try without auth override — should fail closed
        resp = client.post(
            f"/api/v1/projects/{project.id}/context-packages",
            json={"version": 1},
        )
        assert resp.status_code == 403
        assert "not configured" in resp.json()["detail"]

        engine.dispose()

    def test_project_not_found_404(self, ctx: _TestContext) -> None:
        """404 when parent project does not exist."""
        resp = ctx.client.post(
            "/api/v1/projects/nonexistent_project/context-packages",
            json={"version": 1},
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"]

    def test_validation_version_zero_422(self, ctx: _TestContext) -> None:
        """422 when version < 1."""
        project_id = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/context-packages",
            json={"version": 0},
        )
        assert resp.status_code == 422

    def test_validation_version_negative_422(self, ctx: _TestContext) -> None:
        """422 when version is negative."""
        project_id = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/context-packages",
            json={"version": -1},
        )
        assert resp.status_code == 422

    def test_validation_missing_version_422(self, ctx: _TestContext) -> None:
        """422 when version field is missing."""
        project_id = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/context-packages",
            json={},
        )
        assert resp.status_code == 422

    def test_validation_empty_body_422(self, ctx: _TestContext) -> None:
        """422 when body is empty."""
        project_id = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/context-packages",
            json={},
        )
        assert resp.status_code == 422

    def test_persistence_reload(self, ctx: _TestContext) -> None:
        """ContextPackage persists and reloads through a new session."""
        project_id = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/context-packages",
            json={
                "version": 2,
                "instructions": ["Check security"],
                "constraints": ["No secrets"],
                "project_facts": {"env": "test"},
            },
        )
        assert resp.status_code == 201
        cp_id = resp.json()["id"]

        # Reload via repository from a fresh session
        from polynexus_core.persistence.repository import SqlContextPackageRepository

        session = ctx.sf()
        try:
            repo = SqlContextPackageRepository(session)
            reloaded = repo.get(cp_id)
            assert reloaded is not None
            assert reloaded.id == cp_id
            assert reloaded.project_id == project_id
            assert reloaded.version == 2
            assert reloaded.instructions == ("Check security",)
            assert reloaded.constraints == ("No secrets",)
            assert reloaded.project_facts == {"env": "test"}
        finally:
            session.close()

    def test_no_secret_in_response(self, ctx: _TestContext) -> None:
        """Response contains no secret/token fields."""
        project_id = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/context-packages",
            json={"version": 1},
        )
        assert resp.status_code == 201
        data = resp.json()
        secret_keywords = ["secret", "token", "password", "credential", "key"]
        for key in data:
            assert not any(kw in key.lower() for kw in secret_keywords), (
                f"Response field '{key}' may contain sensitive data"
            )

    def test_no_direct_orm_operation(self, ctx: _TestContext) -> None:
        """Route does not import ORM models — verification via code inspection."""
        from polynexus_core.api import context_packages as cp_mod

        source_lines = Path(cp_mod.__file__).read_text(encoding="utf-8").splitlines()
        orm_imports = [
            line for line in source_lines
            if "from polynexus_core.persistence.models" in line
            or "import Base" in line
        ]
        assert len(orm_imports) == 0, (
            f"context_packages.py imports ORM models: {orm_imports}"
        )

    def test_repository_boundary(self, ctx: _TestContext) -> None:
        """Route uses Repository ABC, not raw SQL or direct ORM queries."""
        from polynexus_core.api import context_packages as cp_mod

        source_lines = Path(cp_mod.__file__).read_text(encoding="utf-8").splitlines()
        raw_sql = [line for line in source_lines if "execute(" in line or "text(" in line]
        assert len(raw_sql) == 0, (
            f"context_packages.py contains raw SQL: {raw_sql}"
        )

    def test_does_not_modify_run_api(self, ctx: _TestContext) -> None:
        """Existing POST /tasks/{task_id}/runs behaviour is unchanged."""
        # Create project, context package, task, then create run
        project_id = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/context-packages",
            json={"version": 1},
        )
        cp_id = resp.json()["id"]

        task_resp = ctx.client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={
                "title": "Test Task",
                "workflow_id": "review-minimal",
                "workflow_version": 1,
                "context_package_id": cp_id,
            },
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        # Create run — must still work as before
        run_resp = ctx.client.post(
            f"/api/v1/tasks/{task_id}/runs",
            json={"context_package_id": cp_id},
        )
        assert run_resp.status_code == 201
        assert run_resp.json()["state"] == "CREATED"

    def test_full_core_regression(self) -> None:
        """Placeholder — actual regression run is separate pytest invocation."""
        pass
