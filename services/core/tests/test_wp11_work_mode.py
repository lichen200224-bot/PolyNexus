"""WP-11 — Discuss / Review / Validate WorkMode contract tests.

Deterministic, temporary database (Alembic upgrade head), no global state pollution.
Auth is overridden via test-only dependency injection (no production secret exposed).

Scope (tests-only; no product source change):
- WorkMode enum has exactly DISCUSS / REVIEW / VALIDATE (no DEVELOP or fourth mode).
- Domain Task construction: full required params, omitted mode defaults to REVIEW.
- API: valid modes -> 201 with matching mode; omitted/null/"" -> 201 with REVIEW.
- API: illegal modes -> 422 with deterministic detail, no Task row created.
- Persistence/reload round-trip for all modes; cross-project mode isolation.
- Mode validation does not bypass auth (403) or existence (404) checks.
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
from polynexus_core.api.health import router as health_router
from polynexus_core.api.projects import router as projects_router
from polynexus_core.api.runs import router as runs_router
from polynexus_core.api.tasks import router as tasks_router
from polynexus_core.domain.enums import WorkMode
from polynexus_core.domain.models import Task
from polynexus_core.persistence.database import get_session


# --- test app helpers (mirror services/core/tests/test_api.py) --------------

def _make_alembic_ini(db_path: Path, alembic_dir: Path) -> Path:
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


def _create_test_app(db_url: str, auth_override: bool = True) -> tuple[FastAPI, sessionmaker]:
    """Create a FastAPI app with test DB session and optional auth override.

    auth_override=True mirrors the production loopback auth (always authorized).
    auth_override=False leaves the production default (fail closed -> 403).
    """
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
    if auth_override:
        app.dependency_overrides[require_loopback] = _override_auth

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(tasks_router, prefix="/api/v1")
    app.include_router(runs_router, prefix="/api/v1")

    return app, TestSession


class _TestContext:
    def __init__(self, client: TestClient, session_factory: sessionmaker, db_url: str):
        self.client = client
        self.sf = session_factory
        self.db_url = db_url

    def create_project(self, name: str = "WP-11 Parent") -> str:
        return self.client.post("/api/v1/projects", json={"name": name}).json()["id"]


@pytest.fixture()
def ctx(tmp_path: Path) -> _TestContext:
    db_path = tmp_path / "wp11.db"
    alembic_dir = Path(__file__).parent.parent / "alembic"
    ini = _make_alembic_ini(db_path, alembic_dir)
    config = Config(str(ini))
    alembic_cmd.upgrade(config, "head")

    db_url = f"sqlite:///{db_path}"
    app, sf = _create_test_app(db_url, auth_override=True)
    client = TestClient(app)
    yield _TestContext(client, sf, db_url)


# ---------------------------------------------------------------------------
# 1. WorkMode enum semantics
# ---------------------------------------------------------------------------

class TestWorkModeEnum:
    def test_exactly_three_modes_no_develop(self) -> None:
        members = set(WorkMode.__members__.keys())
        assert members == {"DISCUSS", "REVIEW", "VALIDATE"}
        assert "DEVELOP" not in members
        assert "EXECUTE" not in members
        assert "ANALYZE" not in members

    def test_mode_values_are_canonical_strings(self) -> None:
        assert WorkMode.DISCUSS.value == "DISCUSS"
        assert WorkMode.REVIEW.value == "REVIEW"
        assert WorkMode.VALIDATE.value == "VALIDATE"


# ---------------------------------------------------------------------------
# 2. Domain Task construction
# ---------------------------------------------------------------------------

class TestTaskDomainDefault:
    def test_full_required_params_omitted_mode_defaults_review(self) -> None:
        t = Task(project_id="p_1", title="T", workflow_id="wf", workflow_version=1)
        assert t.mode == WorkMode.REVIEW

    def test_explicit_modes_round_trip(self) -> None:
        for mode in (WorkMode.DISCUSS, WorkMode.REVIEW, WorkMode.VALIDATE):
            t = Task(
                project_id="p_1",
                title="T",
                workflow_id="wf",
                workflow_version=1,
                mode=mode,
            )
            assert t.mode == mode
            assert t.mode.value == mode.value


# ---------------------------------------------------------------------------
# 3-5. API valid modes
# ---------------------------------------------------------------------------

class TestTaskApiValidModes:
    def test_discuss_returns_201(self, ctx: _TestContext) -> None:
        pid = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1, "mode": "DISCUSS"},
        )
        assert resp.status_code == 201
        assert resp.json()["mode"] == "DISCUSS"

    def test_review_returns_201(self, ctx: _TestContext) -> None:
        pid = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1, "mode": "REVIEW"},
        )
        assert resp.status_code == 201
        assert resp.json()["mode"] == "REVIEW"

    def test_validate_returns_201(self, ctx: _TestContext) -> None:
        pid = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1, "mode": "VALIDATE"},
        )
        assert resp.status_code == 201
        assert resp.json()["mode"] == "VALIDATE"


# ---------------------------------------------------------------------------
# 6-7. Current default contract (omitted / null / empty string)
# ---------------------------------------------------------------------------

class TestTaskApiDefaultContract:
    def test_omitted_mode_returns_201_review(self, ctx: _TestContext) -> None:
        pid = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1},
        )
        assert resp.status_code == 201
        assert resp.json()["mode"] == "REVIEW"

    def test_null_mode_returns_201_review(self, ctx: _TestContext) -> None:
        pid = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1, "mode": None},
        )
        assert resp.status_code == 201
        assert resp.json()["mode"] == "REVIEW"

    def test_empty_string_mode_returns_201_review(self, ctx: _TestContext) -> None:
        # Current code treats "" as falsy -> REVIEW (not 422).
        pid = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1, "mode": ""},
        )
        assert resp.status_code == 201
        assert resp.json()["mode"] == "REVIEW"


# ---------------------------------------------------------------------------
# 8. Illegal modes -> 422, no row created
# ---------------------------------------------------------------------------

class TestTaskApiIllegalModes:
    @pytest.mark.parametrize(
        "bad_mode",
        ["INVALID", "DEVELOP", "discuss", " REVIEW "],
    )
    def test_illegal_mode_returns_422(self, ctx: _TestContext, bad_mode: str) -> None:
        pid = ctx.create_project()
        resp = ctx.client.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1, "mode": bad_mode},
        )
        assert resp.status_code == 422
        detail = resp.json()["detail"]
        assert "Invalid mode" in detail
        assert "Must be one of" in detail

    @pytest.mark.parametrize(
        "bad_mode",
        ["INVALID", "DEVELOP", "discuss", " REVIEW "],
    )
    def test_illegal_mode_creates_no_row(self, ctx: _TestContext, bad_mode: str) -> None:
        pid = ctx.create_project()
        before = len(ctx.client.get(f"/api/v1/projects/{pid}/tasks").json()["tasks"])
        ctx.client.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "wf-1", "workflow_version": 1, "mode": bad_mode},
        )
        after = len(ctx.client.get(f"/api/v1/projects/{pid}/tasks").json()["tasks"])
        assert after == before


# ---------------------------------------------------------------------------
# 9-10. Persistence / reload round-trip + cross-project isolation
# ---------------------------------------------------------------------------

class TestTaskApiPersistenceReload:
    def _create_task(self, c: TestClient, pid: str, mode: str | None) -> str:
        body = {"title": "T", "workflow_id": "wf-1", "workflow_version": 1}
        if mode is not None:
            body["mode"] = mode
        resp = c.post(f"/api/v1/projects/{pid}/tasks", json=body)
        assert resp.status_code == 201
        return resp.json()["id"]

    def test_legal_modes_and_default_round_trip(self, tmp_path: Path) -> None:
        db_path = tmp_path / "wp11_reload.db"
        alembic_dir = Path(__file__).parent.parent / "alembic"
        ini = _make_alembic_ini(db_path, alembic_dir)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")
        db_url = f"sqlite:///{db_path}"

        app1, _ = _create_test_app(db_url, auth_override=True)
        c1 = TestClient(app1)
        pid = c1.post("/api/v1/projects", json={"name": "Reload"}).json()["id"]

        expected = {
            self._create_task(c1, pid, "DISCUSS"): "DISCUSS",
            self._create_task(c1, pid, "REVIEW"): "REVIEW",
            self._create_task(c1, pid, "VALIDATE"): "VALIDATE",
            self._create_task(c1, pid, None): "REVIEW",
            self._create_task(c1, pid, ""): "REVIEW",
        }
        c1.close()

        app2, _ = _create_test_app(db_url, auth_override=True)
        c2 = TestClient(app2)
        for task_id, want in expected.items():
            single = c2.get(f"/api/v1/tasks/{task_id}")
            assert single.status_code == 200
            assert single.json()["mode"] == want
        listing = c2.get(f"/api/v1/projects/{pid}/tasks")
        assert listing.status_code == 200
        modes = {t["id"]: t["mode"] for t in listing.json()["tasks"]}
        for task_id, want in expected.items():
            assert modes[task_id] == want

    def test_cross_project_mode_isolation(self, ctx: _TestContext) -> None:
        pid_a = ctx.create_project("Project A")
        pid_b = ctx.create_project("Project B")
        tid_a = self._create_task(ctx.client, pid_a, "DISCUSS")
        tid_b = self._create_task(ctx.client, pid_b, "VALIDATE")

        a = ctx.client.get(f"/api/v1/tasks/{tid_a}").json()
        b = ctx.client.get(f"/api/v1/tasks/{tid_b}").json()
        assert a["mode"] == "DISCUSS"
        assert b["mode"] == "VALIDATE"
        assert a["project_id"] == pid_a
        assert b["project_id"] == pid_b


# ---------------------------------------------------------------------------
# 11. Mode validation does not bypass auth (403) or existence (404)
# ---------------------------------------------------------------------------

class TestTaskApiAuthExistenceNotBypassed:
    def test_get_task_without_auth_returns_403(self, tmp_path: Path) -> None:
        db_path = tmp_path / "wp11_auth.db"
        alembic_dir = Path(__file__).parent.parent / "alembic"
        ini = _make_alembic_ini(db_path, alembic_dir)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")
        db_url = f"sqlite:///{db_path}"

        # No auth override -> production fail-closed
        app, _ = _create_test_app(db_url, auth_override=False)
        c = TestClient(app)
        assert c.get("/api/v1/tasks/any-id").status_code == 403
        assert c.get("/api/v1/projects/any-id/tasks").status_code == 403

    def test_list_tasks_missing_project_returns_404(self, ctx: _TestContext) -> None:
        resp = ctx.client.get("/api/v1/projects/nonexistent/tasks")
        assert resp.status_code == 404

    def test_get_missing_task_returns_404(self, ctx: _TestContext) -> None:
        resp = ctx.client.get("/api/v1/tasks/nonexistent")
        assert resp.status_code == 404
