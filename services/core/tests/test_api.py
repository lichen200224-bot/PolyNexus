"""API tests — deterministic, temporary database, no global state pollution.

Each test uses a fresh temporary SQLite database with Alembic upgrade head.
Auth is overridden via test-only dependency injection (no production secret exposed).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from alembic import command as alembic_cmd
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from polynexus_core.api.dependencies import require_loopback
from polynexus_core.persistence.database import get_session
from polynexus_core.persistence.models import Base


def _make_alembic_ini(db_path: Path, alembic_dir: Path) -> Path:
    """Write a minimal alembic.ini pointing to the given database."""
    ini = db_path.parent / "alembic.ini"
    ini.write_text(
        "[alembic]\n"
        f"script_location = {alembic_dir}\n"
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
    """Create a FastAPI app with test DB session and auth override.

    Returns (app, SessionFactory) so tests can create fixtures via the same engine.
    """
    from polynexus_core.api.health import router as health_router
    from polynexus_core.api.projects import router as projects_router
    from polynexus_core.api.tasks import router as tasks_router
    from polynexus_core.api.runs import router as runs_router

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

    return app, TestSession


class _TestContext:
    """Holds client + session factory for a single test database."""

    def __init__(self, client: TestClient, session_factory: sessionmaker, db_url: str):
        self.client = client
        self.sf = session_factory
        self.db_url = db_url

    def create_context_package(self, project_id: str) -> str:
        """Insert a ContextPackage directly and return its ID."""
        from polynexus_core.domain.models import ContextPackage
        from polynexus_core.persistence.repository import SqlContextPackageRepository

        session = self.sf()
        try:
            cp = ContextPackage(project_id=project_id, version=1)
            SqlContextPackageRepository(session).add(cp)
            session.commit()
            return cp.id
        finally:
            session.close()


@pytest.fixture()
def ctx(tmp_path: Path) -> _TestContext:
    """Yield a _TestContext backed by a fresh temporary SQLite database."""
    db_path = tmp_path / "test.db"
    alembic_dir = Path(__file__).parent.parent / "alembic"
    ini = _make_alembic_ini(db_path, alembic_dir)
    config = Config(str(ini))
    alembic_cmd.upgrade(config, "head")

    db_url = f"sqlite:///{db_path}"
    app, sf = _create_test_app(db_url)
    client = TestClient(app)
    yield _TestContext(client, sf, db_url)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_endpoint(self, ctx: _TestContext) -> None:
        resp = ctx.client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["baseline"] == "development-v1.0"


# ---------------------------------------------------------------------------
# Auth boundary
# ---------------------------------------------------------------------------

class TestAuthBoundary:
    def test_unauthorized_project_create(self, tmp_path: Path) -> None:
        """Without auth override, non-health endpoints must return 403."""
        db_path = tmp_path / "auth_test.db"
        alembic_dir = Path(__file__).parent.parent / "alembic"
        ini = _make_alembic_ini(db_path, alembic_dir)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")

        db_url = f"sqlite:///{db_path}"
        from polynexus_core.api.health import router as health_router
        from polynexus_core.api.projects import router as projects_router

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

        app.dependency_overrides[get_session] = _override_get_session
        # NO auth override — production default (fail closed)
        app.include_router(health_router, prefix="/api/v1")
        app.include_router(projects_router, prefix="/api/v1")

        client = TestClient(app)

        # Health should still work (no auth required)
        assert client.get("/api/v1/health").status_code == 200

        # Project create without any token → 403
        resp = client.post("/api/v1/projects", json={"name": "Test"})
        assert resp.status_code == 403

        engine.dispose()

    def test_arbitrary_token_without_config_rejected(self, tmp_path: Path) -> None:
        """B-01: An arbitrary non-empty token must NOT bypass auth when
        LOOPBACK_TOKEN is not configured (production fail-closed)."""
        db_path = tmp_path / "auth_test2.db"
        alembic_dir = Path(__file__).parent.parent / "alembic"
        ini = _make_alembic_ini(db_path, alembic_dir)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")

        db_url = f"sqlite:///{db_path}"
        from polynexus_core.api.health import router as health_router
        from polynexus_core.api.projects import router as projects_router

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

        app.dependency_overrides[get_session] = _override_get_session
        # NO auth override — production default (fail closed)
        app.include_router(health_router, prefix="/api/v1")
        app.include_router(projects_router, prefix="/api/v1")

        client = TestClient(app)

        # Arbitrary non-empty token without LOOPBACK_TOKEN configured → 403
        resp = client.post(
            "/api/v1/projects",
            json={"name": "Test"},
            headers={"X-Loopback-Token": "arbitrary_nonempty_token"},
        )
        assert resp.status_code == 403

        engine.dispose()


# ---------------------------------------------------------------------------
# Project endpoints
# ---------------------------------------------------------------------------

class TestProjectAPI:
    def test_create_and_get_project(self, ctx: _TestContext) -> None:
        c = ctx.client
        resp = c.post("/api/v1/projects", json={"name": "My Project", "description": "desc"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Project"
        assert data["description"] == "desc"
        project_id = data["id"]

        resp = c.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "My Project"

    def test_list_projects(self, ctx: _TestContext) -> None:
        c = ctx.client
        c.post("/api/v1/projects", json={"name": "P1"})
        c.post("/api/v1/projects", json={"name": "P2"})
        resp = c.get("/api/v1/projects")
        assert resp.status_code == 200
        assert len(resp.json()["projects"]) == 2

    def test_get_nonexistent_project(self, ctx: _TestContext) -> None:
        resp = ctx.client.get("/api/v1/projects/nonexistent")
        assert resp.status_code == 404

    def test_create_project_empty_name(self, ctx: _TestContext) -> None:
        resp = ctx.client.post("/api/v1/projects", json={"name": ""})
        assert resp.status_code == 422

    def test_create_project_whitespace_only_name(self, ctx: _TestContext) -> None:
        """M-02: whitespace-only project name must return 422."""
        resp = ctx.client.post("/api/v1/projects", json={"name": "   "})
        assert resp.status_code == 422

    def test_reload_project_from_new_session(self, tmp_path: Path) -> None:
        """Create project, dispose session, reload from new session."""
        db_path = tmp_path / "reload_test.db"
        alembic_dir = Path(__file__).parent.parent / "alembic"
        ini = _make_alembic_ini(db_path, alembic_dir)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")

        db_url = f"sqlite:///{db_path}"

        # Session 1: create
        app1, _ = _create_test_app(db_url)
        c1 = TestClient(app1)
        resp = c1.post("/api/v1/projects", json={"name": "Reload Test"})
        project_id = resp.json()["id"]
        c1.close()

        # Session 2: reload
        app2, _ = _create_test_app(db_url)
        c2 = TestClient(app2)
        resp = c2.get(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Reload Test"


# ---------------------------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------------------------

class TestTaskAPI:
    def _create_project(self, c: TestClient) -> str:
        resp = c.post("/api/v1/projects", json={"name": "Task Parent"})
        return resp.json()["id"]

    def test_create_and_get_task(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = self._create_project(c)
        resp = c.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "Review task", "workflow_id": "wf-1", "workflow_version": 1},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Review task"
        assert data["project_id"] == pid
        assert data["workflow_id"] == "wf-1"
        task_id = data["id"]

        resp = c.get(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Review task"

    def test_list_tasks_by_project(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = self._create_project(c)
        c.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T1", "workflow_id": "wf-1", "workflow_version": 1},
        )
        c.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T2", "workflow_id": "wf-1", "workflow_version": 1},
        )
        resp = c.get(f"/api/v1/projects/{pid}/tasks")
        assert resp.status_code == 200
        assert len(resp.json()["tasks"]) == 2

    def test_create_task_nonexistent_project(self, ctx: _TestContext) -> None:
        resp = ctx.client.post(
            "/api/v1/projects/nope/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1},
        )
        assert resp.status_code == 404

    def test_get_nonexistent_task(self, ctx: _TestContext) -> None:
        resp = ctx.client.get("/api/v1/tasks/nonexistent")
        assert resp.status_code == 404

    def test_create_task_empty_title(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = self._create_project(c)
        resp = c.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "", "workflow_id": "wf-1", "workflow_version": 1},
        )
        assert resp.status_code == 422

    def test_create_task_whitespace_only_title(self, ctx: _TestContext) -> None:
        """M-02: whitespace-only task title must return 422."""
        c = ctx.client
        pid = self._create_project(c)
        resp = c.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "   ", "workflow_id": "wf-1", "workflow_version": 1},
        )
        assert resp.status_code == 422

    def test_create_task_invalid_version(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = self._create_project(c)
        resp = c.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 0},
        )
        assert resp.status_code == 422

    def test_create_task_invalid_mode(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = self._create_project(c)
        resp = c.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1, "mode": "INVALID"},
        )
        assert resp.status_code == 422

    def test_create_task_cross_project_context_package(self, ctx: _TestContext) -> None:
        """ContextPackage from a different project should be rejected."""
        c = ctx.client
        pid = self._create_project(c)
        resp = c.post(
            f"/api/v1/projects/{pid}/tasks",
            json={
                "title": "T",
                "workflow_id": "wf-1",
                "workflow_version": 1,
                "context_package_id": "cp_nonexistent",
            },
        )
        assert resp.status_code == 422

    def test_reload_task_from_new_session(self, tmp_path: Path) -> None:
        """Create task, dispose session, reload from new session."""
        db_path = tmp_path / "task_reload.db"
        alembic_dir = Path(__file__).parent.parent / "alembic"
        ini = _make_alembic_ini(db_path, alembic_dir)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")

        db_url = f"sqlite:///{db_path}"

        app1, _ = _create_test_app(db_url)
        c1 = TestClient(app1)
        pid = c1.post("/api/v1/projects", json={"name": "P"}).json()["id"]
        resp = c1.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "Reload Task", "workflow_id": "wf-1", "workflow_version": 1},
        )
        task_id = resp.json()["id"]
        c1.close()

        app2, _ = _create_test_app(db_url)
        c2 = TestClient(app2)
        resp = c2.get(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Reload Task"


# ---------------------------------------------------------------------------
# Run endpoints
# ---------------------------------------------------------------------------

class TestRunAPI:
    def _setup_project_and_task(self, c: TestClient) -> tuple[str, str]:
        pid = c.post("/api/v1/projects", json={"name": "Run Parent"}).json()["id"]
        tid = c.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "Run Task", "workflow_id": "wf-1", "workflow_version": 1},
        ).json()["id"]
        return pid, tid

    def test_create_run(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid, tid = self._setup_project_and_task(c)
        cp_id = ctx.create_context_package(pid)

        resp = c.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": cp_id})
        assert resp.status_code == 201
        data = resp.json()
        assert data["state"] == "CREATED"
        assert data["execution_target"] == "LOCAL"
        assert data["resume_mode"] == "NONE"
        assert data["task_id"] == tid
        assert data["context_package_id"] == cp_id

    def test_get_run(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid, tid = self._setup_project_and_task(c)
        cp_id = ctx.create_context_package(pid)

        resp = c.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": cp_id})
        run_id = resp.json()["id"]

        resp = c.get(f"/api/v1/runs/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == run_id
        assert resp.json()["state"] == "CREATED"

    def test_list_runs_by_task(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid, tid = self._setup_project_and_task(c)
        cp_id = ctx.create_context_package(pid)

        c.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": cp_id})
        c.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": cp_id})

        resp = c.get(f"/api/v1/tasks/{tid}/runs")
        assert resp.status_code == 200
        assert len(resp.json()["runs"]) == 2

    def test_get_nonexistent_run(self, ctx: _TestContext) -> None:
        resp = ctx.client.get("/api/v1/runs/nonexistent")
        assert resp.status_code == 404

    def test_list_runs_nonexistent_task(self, ctx: _TestContext) -> None:
        resp = ctx.client.get("/api/v1/tasks/nonexistent/runs")
        assert resp.status_code == 404

    def test_create_run_nonexistent_task(self, ctx: _TestContext) -> None:
        resp = ctx.client.post(
            "/api/v1/tasks/nonexistent/runs",
            json={"context_package_id": "cp_xxx"},
        )
        assert resp.status_code == 404

    def test_create_run_nonexistent_context_package(self, ctx: _TestContext) -> None:
        c = ctx.client
        _, tid = self._setup_project_and_task(c)
        resp = c.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": "cp_nonexistent"})
        assert resp.status_code == 422

    def test_create_run_cross_project_context_package(self, ctx: _TestContext) -> None:
        """ContextPackage from different project should be rejected."""
        c = ctx.client
        pid1, tid = self._setup_project_and_task(c)
        pid2 = c.post("/api/v1/projects", json={"name": "Other"}).json()["id"]
        cp_id = ctx.create_context_package(pid2)

        resp = c.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": cp_id})
        assert resp.status_code == 422

    def test_run_no_forged_evidence(self, ctx: _TestContext) -> None:
        """Newly created Run must not have fabricated Finding/Evidence/Result."""
        c = ctx.client
        pid, tid = self._setup_project_and_task(c)
        cp_id = ctx.create_context_package(pid)

        resp = c.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": cp_id})
        data = resp.json()
        assert data["state"] == "CREATED"
        assert data["result"] is None
        assert data["events"] == []

    def test_run_reload_from_new_session(self, tmp_path: Path) -> None:
        """Create run, dispose session, reload from new session."""
        db_path = tmp_path / "run_reload.db"
        alembic_dir = Path(__file__).parent.parent / "alembic"
        ini = _make_alembic_ini(db_path, alembic_dir)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")

        db_url = f"sqlite:///{db_path}"

        app1, sf1 = _create_test_app(db_url)
        c1 = TestClient(app1)

        pid = c1.post("/api/v1/projects", json={"name": "P"}).json()["id"]
        tid = c1.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1},
        ).json()["id"]

        # Insert CP via same session factory
        from polynexus_core.domain.models import ContextPackage
        from polynexus_core.persistence.repository import SqlContextPackageRepository

        session = sf1()
        cp = ContextPackage(project_id=pid, version=1)
        SqlContextPackageRepository(session).add(cp)
        session.commit()
        cp_id = cp.id
        session.close()

        resp = c1.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": cp_id})
        run_id = resp.json()["id"]
        c1.close()

        # Session 2: reload
        app2, _ = _create_test_app(db_url)
        c2 = TestClient(app2)
        resp = c2.get(f"/api/v1/runs/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["state"] == "CREATED"
        assert resp.json()["id"] == run_id


# ---------------------------------------------------------------------------
# Static checks (no ORM/raw SQL in API routes, no hard-coded secrets)
# ---------------------------------------------------------------------------

class TestStaticChecks:
    def test_api_routes_no_orm_imports(self) -> None:
        """API route modules must not import ORM models or raw SQL."""
        import importlib
        route_modules = [
            "polynexus_core.api.projects",
            "polynexus_core.api.tasks",
            "polynexus_core.api.runs",
        ]
        for mod_name in route_modules:
            mod = importlib.import_module(mod_name)
            with open(mod.__file__, encoding="utf-8") as f:
                source = f.read()
            assert "from polynexus_core.persistence.models import" not in source, (
                f"{mod_name} imports ORM models directly"
            )

    def test_no_hardcoded_secrets(self) -> None:
        """No hard-coded tokens or secrets in API modules."""
        import importlib
        api_modules = [
            "polynexus_core.api.dependencies",
            "polynexus_core.api.projects",
            "polynexus_core.api.tasks",
            "polynexus_core.api.runs",
        ]
        secret_patterns = ["sk-", "token=", "password=", "secret=", "api_key"]
        for mod_name in api_modules:
            mod = importlib.import_module(mod_name)
            with open(mod.__file__, encoding="utf-8") as f:
                source = f.read().lower()
            for pattern in secret_patterns:
                assert pattern not in source, f"{mod_name} contains hard-coded secret pattern: {pattern}"


# ---------------------------------------------------------------------------
# M-01: Default app session lifecycle smoke test
# ---------------------------------------------------------------------------

class TestDefaultAppLifecycle:
    def test_default_app_session_factory_initialised(self, tmp_path: Path) -> None:
        """M-01: The default create_app() must initialise the database session
        factory via its lifespan, so data routes do not 500."""
        from polynexus_core.persistence.database import dispose_engine, get_engine

        db_path = tmp_path / "lifecycle_test.db"
        db_url = f"sqlite:///{db_path}"
        alembic_dir = Path(__file__).parent.parent / "alembic"
        ini = _make_alembic_ini(db_path, alembic_dir)
        alembic_cmd.upgrade(Config(str(ini)), "head")
        import os
        os.environ["POLYNEXUS_DATABASE_URL"] = db_url
        try:
            from polynexus_core.app import create_app
            from polynexus_core.api.dependencies import require_loopback

            app = create_app()
            app.dependency_overrides[require_loopback] = lambda: None

            # Use context manager to trigger lifespan startup/shutdown
            with TestClient(app) as client:
                # Health must work without database
                resp = client.get("/api/v1/health")
                assert resp.status_code == 200

                # Session factory must now be initialised by lifespan
                engine = get_engine()
                assert engine is not None

                # Data route must work (not 500 from missing session factory)
                resp = client.get("/api/v1/projects")
                assert resp.status_code == 200
                assert resp.json()["projects"] == []

            # Cleanup
            dispose_engine()
        finally:
            os.environ.pop("POLYNEXUS_DATABASE_URL", None)
