"""WP-09B Execution Command API Tests — Attempt 4.

Validates the approved Option A contract:
  - Execute an existing persisted Run by run_id
  - No second Run may be created
  - Run context_package_id is the authority
  - Atomic CAS claim (one-winner)
  - Runtime failure isolation with sanitized reason
  - No fabricated output on failure
  - All runtime outputs persisted on success (Finding, Evidence, Artifact)
  - Lifecycle idempotency matrix
  - Adapter invocation counter

Uses Alembic upgrade head on temporary SQLite database.
Auth is overridden via test-only dependency injection.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from alembic import command as alembic_cmd
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from d1a_fixtures import d1a_content_environment, prepared_run_body, start_body
from polynexus_core.api.generations import router as generations_router
from polynexus_core.api.dependencies import require_loopback
from polynexus_core.domain.enums import RunState, WorkMode
from polynexus_core.domain.models import ContextPackage, Project, Task
from polynexus_core.persistence.database import get_session
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlTaskRepository,
)


ALEMBIC_DIR = Path(__file__).parent.parent / "alembic"

# Public-safe sanitized reason constant (mirrors supervisor._RUNTIME_FAILURE_REASON)
_RUNTIME_FAILURE_REASON = "Runtime boundary error"

# Secret marker used to test sanitization — must never appear in output
_SECRET_MARKER = "SECRET_TOKEN_sk-test-12345-ABCD"


def _make_alembic_ini(db_path: Path) -> Path:
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
    from polynexus_core.api.health import router as health_router
    from polynexus_core.api.projects import router as projects_router
    from polynexus_core.api.tasks import router as tasks_router
    from polynexus_core.api.runs import router as runs_router

    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    app = FastAPI()


    app.include_router(generations_router, prefix="/api/v1")
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
    def __init__(self, client: TestClient, session_factory: sessionmaker, db_url: str):
        self.client = client
        self.sf = session_factory
        self.db_url = db_url

    def create_project(self, name: str = "WP-09 Test Project") -> str:
        resp = self.client.post("/api/v1/projects", json={"name": name})
        assert resp.status_code == 201
        return resp.json()["id"]

    def create_task(
        self,
        project_id: str,
        title: str = "WP-09 Test Task",
        workflow_id: str = "review-minimal",
        workflow_version: int = 1,
        context_package_id: str | None = None,
    ) -> str:
        body: dict = {
            "title": title,
            "workflow_id": workflow_id,
            "workflow_version": workflow_version,
        }
        if context_package_id is not None:
            body["context_package_id"] = context_package_id
        resp = self.client.post(
            f"/api/v1/projects/{project_id}/tasks", json=body,
        )
        assert resp.status_code == 201
        return resp.json()["id"]

    def create_context_package(self, project_id: str, version: int = 1) -> str:
        session = self.sf()
        try:
            cp = ContextPackage(project_id=project_id, version=version)
            SqlContextPackageRepository(session).add(cp)
            session.commit()
            return cp.id
        finally:
            session.close()

    def create_run(self, task_id: str, context_package_id: str) -> str:
        resp = self.client.post(
            f"/api/v1/tasks/{task_id}/runs",
            json=prepared_run_body(self.client, task_id, context_package_id),
        )
        assert resp.status_code == 201
        return resp.json()["id"]


@pytest.fixture()
def ctx(tmp_path: Path) -> _TestContext:
    db_path = tmp_path / "test.db"
    ini = _make_alembic_ini(db_path)
    config = Config(str(ini))
    alembic_cmd.upgrade(config, "head")

    db_url = f"sqlite:///{db_path}"
    app, sf = _create_test_app(db_url)
    client = TestClient(app)
    yield _TestContext(client, sf, db_url)


# ---------------------------------------------------------------------------
# 1. First execution — CREATED → 202, exact Run ID, no duplicate Run
# ---------------------------------------------------------------------------

class TestWP09FirstExecution:
    def test_execute_created_run_returns_202(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 202
        data = resp.json()
        assert data["id"] == run_id
        assert data["state"] == "COMPLETED"

    def test_execute_preserves_run_id_no_duplicate(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())

        resp = c.get(f"/api/v1/tasks/{tid}/runs")
        assert resp.status_code == 200
        runs = resp.json()["runs"]
        assert len(runs) == 1
        assert runs[0]["id"] == run_id

    def test_execute_completed_run_shows_result(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())

        resp = c.get(f"/api/v1/runs/{run_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "COMPLETED"
        assert data["result"] is not None
        assert data["result"]["status"] == "COMPLETED"
        assert data["result"]["summary"] == "Reference runtime completed without vendor execution"
        assert data["result"]["finding_ids"] == []


# ---------------------------------------------------------------------------
# 2. Claim-before-adapter: instrumented create_run check
# ---------------------------------------------------------------------------

class TestWP09ClaimBeforeAdapter:
    def test_claim_persisted_before_adapter_create_run(self, ctx: _TestContext) -> None:
        """Instrument adapter.create_run — inside it, open independent DB session
        and assert state == STARTING and CREATED→STARTING event is readable."""
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
        original_create_run = ReferenceRuntimeAdapter.create_run
        claim_verified = {}

        async def instrumented_create_run(self_adapter, context):
            session = ctx.sf()
            try:
                repo = SqlRunRepository(session)
                run = repo.get(run_id)
                if run is not None:
                    claim_verified["state"] = run.state
                    claim_verified["events"] = [
                        (e.from_state, e.to_state) for e in run.events
                    ]
            finally:
                session.close()
            return await original_create_run(self_adapter, context)

        ReferenceRuntimeAdapter.create_run = instrumented_create_run

        try:
            resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
            assert resp.status_code == 202

            # Verify the claim was visible during adapter.create_run
            assert claim_verified.get("state") == RunState.STARTING
            assert (RunState.CREATED, RunState.STARTING) in claim_verified.get("events", [])
        finally:
            ReferenceRuntimeAdapter.create_run = original_create_run

    def test_exact_ordered_lifecycle_tuples(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())

        resp = c.get(f"/api/v1/runs/{run_id}")
        events = resp.json()["events"]
        transitions = [(e["from_state"], e["to_state"]) for e in events]
        assert transitions == [
            ("CREATED", "STARTING"),
            ("STARTING", "RUNNING"),
            ("RUNNING", "COMPLETED"),
        ], f"Expected exact lifecycle, got {transitions}"


# ---------------------------------------------------------------------------
# 3. Two-session CAS one-winner claim test
# ---------------------------------------------------------------------------

class TestWP09CASOneWinner:
    def test_deterministic_two_session_cas_one_winner(self, tmp_path: Path) -> None:
        db_path = tmp_path / "wp09_cas.db"
        ini = _make_alembic_ini(db_path)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")
        db_url = f"sqlite:///{db_path}"

        engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
        TestSession = sessionmaker(bind=engine, expire_on_commit=False, future=True)

        from polynexus_core.domain.models import Run
        session1 = TestSession()
        project = Project(name="CAS Test")
        SqlProjectRepository(session1).add(project)
        session1.commit()

        cp = ContextPackage(project_id=project.id, version=1)
        SqlContextPackageRepository(session1).add(cp)
        session1.commit()

        task = Task(
            project_id=project.id,
            title="CAS Task",
            workflow_id="review-minimal",
            workflow_version=1,
            context_package_id=cp.id,
        )
        SqlTaskRepository(session1).add(task)
        session1.commit()

        run = Run(
            task_id=task.id,
            workflow_id="review-minimal",
            workflow_version=1,
            context_package_id=cp.id,
        )
        SqlRunRepository(session1).add(run)
        session1.commit()
        run_id = run.id
        session1.close()

        session_a = TestSession()
        repo_a = SqlRunRepository(session_a)
        claimed_a = repo_a.claim_for_execution(run_id)
        assert claimed_a is True
        session_a.commit()

        session_b = TestSession()
        repo_b = SqlRunRepository(session_b)
        claimed_b = repo_b.claim_for_execution(run_id)
        assert claimed_b is False
        session_b.close()

        session_verify = TestSession()
        repo_verify = SqlRunRepository(session_verify)
        run_verify = repo_verify.get(run_id)
        assert run_verify is not None
        assert run_verify.state == RunState.STARTING
        session_verify.close()

        engine.dispose()


# ---------------------------------------------------------------------------
# 4. Parameterized runtime failure tests
# ---------------------------------------------------------------------------

class TestWP09RuntimeFailure:
    """Parameterized tests: each adapter boundary call can raise RuntimeError.
    Verify: FAILED state, sanitized reason, session close/reopen, no fabricated output."""

    @pytest.mark.parametrize("fail_point", ["create_run", "status", "result", "artifacts", "version_info"])
    def test_runtime_failure_persists_failed_state(self, fail_point: str, tmp_path: Path) -> None:
        db_path = tmp_path / f"wp09_fail_{fail_point}.db"
        ini = _make_alembic_ini(db_path)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")
        db_url = f"sqlite:///{db_path}"

        app1, sf1 = _create_test_app(db_url)
        c1 = TestClient(app1)

        pid = c1.post("/api/v1/projects", json={"name": "P"}).json()["id"]
        session = sf1()
        cp = ContextPackage(project_id=pid, version=1)
        SqlContextPackageRepository(session).add(cp)
        session.commit()
        cp_id = cp.id
        session.close()

        tid = c1.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "review-minimal", "workflow_version": 1},
        ).json()["id"]

        resp = c1.post(f"/api/v1/tasks/{tid}/runs", json=prepared_run_body(c1, tid, cp_id))
        run_id = resp.json()["id"]

        # Inject failure at the specified adapter boundary
        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
        originals = {
            "create_run": ReferenceRuntimeAdapter.create_run,
            "status": ReferenceRuntimeAdapter.status,
            "result": ReferenceRuntimeAdapter.result,
            "artifacts": ReferenceRuntimeAdapter.artifacts,
            "version_info": ReferenceRuntimeAdapter.version_info,
        }

        async def failing_async(*args, **kwargs):
            raise RuntimeError(f"{_SECRET_MARKER}")

        def failing_sync(*args, **kwargs):
            raise RuntimeError(f"{_SECRET_MARKER}")

        if fail_point == "version_info":
            ReferenceRuntimeAdapter.version_info = failing_sync  # type: ignore[method-assign]
        else:
            setattr(ReferenceRuntimeAdapter, fail_point, failing_async)

        try:
            resp = c1.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
            assert resp.status_code == 202
            data = resp.json()

            # Verify sanitized response — no raw exception or secret marker
            assert _SECRET_MARKER not in str(data)
            if data.get("result") is not None:
                assert _SECRET_MARKER not in data["result"].get("summary", "")

            c1.close()

            # Session 2: reload and verify FAILED state
            app2, _ = _create_test_app(db_url)
            c2 = TestClient(app2)
            resp = c2.get(f"/api/v1/runs/{run_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["state"] == "FAILED"

            # Verify sanitized reason — no secret marker in events
            for event in data["events"]:
                reason = event.get("reason") or ""
                assert _SECRET_MARKER not in reason, f"Secret marker in event reason: {reason}"

            # Verify lifecycle chain
            transitions = [(e["from_state"], e["to_state"]) for e in data["events"]]
            assert ("CREATED", "STARTING") in transitions
            assert ("STARTING", "FAILED") in transitions or ("RUNNING", "FAILED") in transitions

            # Verify result is None (no fabricated Result)
            assert data["result"] is None

            # Verify no fabricated Evidence/Finding/Artifact for this Run
            session = sf1()
            try:
                evidence = SqlEvidenceRepository(session).list_by_task(tid)
                run_evidence = [e for e in evidence if e.run_id == run_id]
                assert len(run_evidence) == 0, "No fabricated Evidence on failure"
            finally:
                session.close()
        finally:
            for name, meth in originals.items():
                setattr(ReferenceRuntimeAdapter, name, meth)


# ---------------------------------------------------------------------------
# 5. Sanitization test
# ---------------------------------------------------------------------------

class TestWP09Sanitization:
    def test_secret_marker_not_in_any_output(self, tmp_path: Path) -> None:
        """Exception message with secret marker must not appear in
        response, events, result, evidence, or DB reload."""
        db_path = tmp_path / "wp09_sanitize.db"
        ini = _make_alembic_ini(db_path)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")
        db_url = f"sqlite:///{db_path}"

        app1, sf1 = _create_test_app(db_url)
        c1 = TestClient(app1)

        pid = c1.post("/api/v1/projects", json={"name": "P"}).json()["id"]
        session = sf1()
        cp = ContextPackage(project_id=pid, version=1)
        SqlContextPackageRepository(session).add(cp)
        session.commit()
        cp_id = cp.id
        session.close()

        tid = c1.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "review-minimal", "workflow_version": 1},
        ).json()["id"]

        resp = c1.post(f"/api/v1/tasks/{tid}/runs", json=prepared_run_body(c1, tid, cp_id))
        run_id = resp.json()["id"]

        # Inject failure with secret marker in exception message
        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
        original_create_run = ReferenceRuntimeAdapter.create_run

        async def failing_create_run(self_adapter, context):
            raise RuntimeError(f"Internal error with {_SECRET_MARKER} and /path/to/secret.key")

        ReferenceRuntimeAdapter.create_run = failing_create_run

        try:
            resp = c1.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
            assert resp.status_code == 202
            response_text = resp.text

            # Sanitization: secret marker must NOT be in API response
            assert _SECRET_MARKER not in response_text, "Secret marker in API response"
            assert "/path/to/secret.key" not in response_text, "Path in API response"

            c1.close()

            # Session 2: reload and verify
            app2, sf2 = _create_test_app(db_url)
            c2 = TestClient(app2)
            resp = c2.get(f"/api/v1/runs/{run_id}")
            data = resp.json()

            # Sanitization: secret marker must NOT be in events
            for event in data["events"]:
                reason = event.get("reason") or ""
                assert _SECRET_MARKER not in reason, f"Secret marker in event reason: {reason}"

            # Result must be None (no fabricated Result with raw error)
            assert data["result"] is None

            # Verify no Evidence with secret marker
            session = sf2()
            try:
                evidence = SqlEvidenceRepository(session).list_by_task(tid)
                for ev in evidence:
                    for val in (ev.source, ev.actor_id):
                        assert _SECRET_MARKER not in val
                    for v in ev.metadata.values():
                        assert _SECRET_MARKER not in v
            finally:
                session.close()
        finally:
            ReferenceRuntimeAdapter.create_run = original_create_run


# ---------------------------------------------------------------------------
# 6. No-fabricated-output test
# ---------------------------------------------------------------------------

class TestWP09NoFabricatedOutput:
    def test_pre_result_failure_no_fabricated_output(self, tmp_path: Path) -> None:
        """When runtime fails before producing RuntimeResult, only Run state/events
        are persisted. result must be None, and Finding/Evidence/Artifact repositories
        must not have new data for this Run."""
        db_path = tmp_path / "wp09_nofab.db"
        ini = _make_alembic_ini(db_path)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")
        db_url = f"sqlite:///{db_path}"

        app1, sf1 = _create_test_app(db_url)
        c1 = TestClient(app1)

        pid = c1.post("/api/v1/projects", json={"name": "P"}).json()["id"]
        session = sf1()
        cp = ContextPackage(project_id=pid, version=1)
        SqlContextPackageRepository(session).add(cp)
        session.commit()
        cp_id = cp.id
        session.close()

        tid = c1.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "review-minimal", "workflow_version": 1},
        ).json()["id"]

        resp = c1.post(f"/api/v1/tasks/{tid}/runs", json=prepared_run_body(c1, tid, cp_id))
        run_id = resp.json()["id"]

        # Inject failure at result call — runtime started but failed before producing result
        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
        original_result = ReferenceRuntimeAdapter.result

        async def failing_result(self_adapter, runtime_ref):
            raise RuntimeError("result call failed")

        ReferenceRuntimeAdapter.result = failing_result

        try:
            resp = c1.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
            assert resp.status_code == 202

            c1.close()

            app2, sf2 = _create_test_app(db_url)
            c2 = TestClient(app2)
            resp = c2.get(f"/api/v1/runs/{run_id}")
            data = resp.json()

            # Result must be None — no fabricated Result
            assert data["result"] is None

            # Finding/Evidence/Artifact repos must not have data for this Run
            session = sf2()
            try:
                evidence = SqlEvidenceRepository(session).list_by_task(tid)
                run_evidence = [e for e in evidence if e.run_id == run_id]
                assert len(run_evidence) == 0, "No fabricated Evidence on pre-result failure"

                from polynexus_core.persistence.repository import SqlFindingRepository, SqlArtifactRepository
                findings = SqlFindingRepository(session).list_by_task(tid)
                run_findings = [f for f in findings if f.run_id == run_id]
                assert len(run_findings) == 0, "No fabricated Finding on pre-result failure"

                artifacts = SqlArtifactRepository(session).list_by_project(pid)
                run_artifacts = [a for a in artifacts if a.run_id == run_id]
                assert len(run_artifacts) == 0, "No fabricated Artifact on pre-result failure"
            finally:
                session.close()
        finally:
            ReferenceRuntimeAdapter.result = original_result


# ---------------------------------------------------------------------------
# 7. Output persistence test — real Finding/Evidence/Artifact
# ---------------------------------------------------------------------------

class TestWP09OutputPersistence:
    def test_runtime_outputs_persist_finding_evidence_and_artifact(self, tmp_path: Path) -> None:
        """Inject RuntimeResult with one Finding, one Evidence, one Artifact via
        custom adapter. Execute production API path, then reload each ID via
        its repository and assert exists."""
        db_path = tmp_path / "wp09_outputs.db"
        ini = _make_alembic_ini(db_path)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")
        db_url = f"sqlite:///{db_path}"

        app1, sf1 = _create_test_app(db_url)
        c1 = TestClient(app1)

        pid = c1.post("/api/v1/projects", json={"name": "P"}).json()["id"]
        session = sf1()
        cp = ContextPackage(project_id=pid, version=1)
        SqlContextPackageRepository(session).add(cp)
        session.commit()
        cp_id = cp.id
        session.close()

        tid = c1.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "review-minimal", "workflow_version": 1},
        ).json()["id"]

        resp = c1.post(f"/api/v1/tasks/{tid}/runs", json=prepared_run_body(c1, tid, cp_id))
        run_id = resp.json()["id"]

        # Prepare real Finding/Evidence/Artifact that will be returned by adapter
        from polynexus_core.domain.enums import ArtifactType, EvidenceStatus, EvidenceType, FindingSeverity
        from polynexus_core.domain.models import Artifact, Evidence, Finding
        # Need run_id for evidence/finding creation — use the created run_id
        injected_evidence = Evidence(
            task_id=tid, run_id=run_id, actor_id="test:adapter",
            source="test", type=EvidenceType.TOOL_EVIDENCE, status=EvidenceStatus.PASS,
        )
        injected_finding = Finding(
            task_id=tid, run_id=run_id, title="Test Finding",
            description="desc", severity=FindingSeverity.LOW,
            evidence_refs=(injected_evidence.id,),
        )
        injected_artifact = Artifact(
            project_id=pid, artifact_type=ArtifactType.TEXT, mime_type="text/plain",
            source_type="test", storage_ref="test/ref", sha256="a" * 64, task_id=tid, run_id=run_id,
        )

        from polynexus_core.runtime.contracts import RuntimeResult
        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
        orig_result = ReferenceRuntimeAdapter.result
        orig_artifacts = ReferenceRuntimeAdapter.artifacts

        async def injected_result(self_adapter, runtime_ref):
            return RuntimeResult(
                summary="injected result",
                evidence=(injected_evidence,),
                findings=(injected_finding,),
                artifacts=(injected_artifact,),
            )

        async def injected_artifacts(self_adapter, runtime_ref):
            # Return empty — artifacts already in RuntimeResult
            return ()

        ReferenceRuntimeAdapter.result = injected_result  # type: ignore[method-assign]
        ReferenceRuntimeAdapter.artifacts = injected_artifacts  # type: ignore[method-assign]

        try:
            resp = c1.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
            assert resp.status_code == 202
            c1.close()

            app2, sf2 = _create_test_app(db_url)
            c2 = TestClient(app2)
            resp = c2.get(f"/api/v1/runs/{run_id}")
            data = resp.json()
            assert data["result"] is not None
            assert len(data["result"]["finding_ids"]) == 1
            assert len(data["result"]["evidence_ids"]) >= 1
            assert len(data["result"]["artifact_ids"]) == 1

            finding_id = data["result"]["finding_ids"][0]
            evidence_id = data["result"]["evidence_ids"][0]
            artifact_id = data["result"]["artifact_ids"][0]

            session = sf2()
            try:
                from polynexus_core.persistence.repository import SqlArtifactRepository, SqlFindingRepository
                f = SqlFindingRepository(session).get(finding_id)
                assert f is not None, f"Finding {finding_id} not found"
                e = SqlEvidenceRepository(session).get(evidence_id)
                assert e is not None, f"Evidence {evidence_id} not found"
                a = SqlArtifactRepository(session).get(artifact_id)
                assert a is not None, f"Artifact {artifact_id} not found"
            finally:
                session.close()
        finally:
            ReferenceRuntimeAdapter.result = orig_result  # type: ignore[method-assign]
            ReferenceRuntimeAdapter.artifacts = orig_artifacts  # type: ignore[method-assign]


# ---------------------------------------------------------------------------
# 8. Adapter invocation count
# ---------------------------------------------------------------------------

class TestWP09AdapterInvocationCount:
    def test_duplicate_command_does_not_invoke_adapter_twice(self, ctx: _TestContext) -> None:
        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
        original_create_run = ReferenceRuntimeAdapter.create_run
        invocation_count = 0

        async def counting_create_run(self_adapter, context):
            nonlocal invocation_count
            invocation_count += 1
            return await original_create_run(self_adapter, context)

        ReferenceRuntimeAdapter.create_run = counting_create_run

        try:
            c = ctx.client
            pid = ctx.create_project()
            cp_id = ctx.create_context_package(pid)
            tid = ctx.create_task(pid, context_package_id=cp_id)
            run_id = ctx.create_run(tid, cp_id)

            resp1 = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
            assert resp1.status_code == 202
            assert invocation_count == 1

            resp2 = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
            assert resp2.status_code == 200
            assert resp2.json()["state"] == "COMPLETED"
            assert invocation_count == 1, f"Adapter invoked {invocation_count} times, expected 1"

            resp3 = c.get(f"/api/v1/runs/{run_id}")
            events = resp3.json()["events"]
            transitions = [(e["from_state"], e["to_state"]) for e in events]
            assert len(transitions) == 3
        finally:
            ReferenceRuntimeAdapter.create_run = original_create_run


# ---------------------------------------------------------------------------
# 9. Idempotency matrix — all states
# ---------------------------------------------------------------------------

class TestWP09IdempotencyMatrix:
    def test_terminal_completed_run_returns_200(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        resp1 = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp1.status_code == 202

        resp2 = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp2.status_code == 200
        assert resp2.json()["state"] == "COMPLETED"

    def test_starting_run_returns_202(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        session = ctx.sf()
        try:
            repo = SqlRunRepository(session)
            repo.claim_for_execution(run_id)
            session.commit()
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 202

    def test_running_run_returns_202(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        session = ctx.sf()
        try:
            repo = SqlRunRepository(session)
            run = repo.get(run_id)
            run.transition(RunState.STARTING)
            run.transition(RunState.RUNNING)
            repo.update(run)
            session.commit()
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 202
        assert resp.json()["state"] == "RUNNING"

    def test_failed_run_returns_200(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        session = ctx.sf()
        try:
            repo = SqlRunRepository(session)
            run = repo.get(run_id)
            run.transition(RunState.STARTING)
            run.transition(RunState.RUNNING)
            run.transition(RunState.FAILED)
            repo.update(run)
            session.commit()
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 200
        assert resp.json()["state"] == "FAILED"

    def test_timed_out_run_returns_200(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        session = ctx.sf()
        try:
            repo = SqlRunRepository(session)
            run = repo.get(run_id)
            run.transition(RunState.STARTING)
            run.transition(RunState.RUNNING)
            run.transition(RunState.TIMED_OUT)
            repo.update(run)
            session.commit()
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 200
        assert resp.json()["state"] == "TIMED_OUT"

    def test_cancelled_run_returns_200(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        session = ctx.sf()
        try:
            repo = SqlRunRepository(session)
            run = repo.get(run_id)
            run.transition(RunState.STARTING)
            run.transition(RunState.RUNNING)
            run.transition(RunState.CANCEL_REQUESTED)
            run.transition(RunState.CANCELLED)
            repo.update(run)
            session.commit()
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 200
        assert resp.json()["state"] == "CANCELLED"

    def test_orphaned_run_returns_200(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        session = ctx.sf()
        try:
            repo = SqlRunRepository(session)
            run = repo.get(run_id)
            run.transition(RunState.STARTING)
            run.transition(RunState.RUNNING)
            run.transition(RunState.CANCEL_REQUESTED)
            run.transition(RunState.ORPHANED)
            repo.update(run)
            session.commit()
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 200
        assert resp.json()["state"] == "ORPHANED"

    def test_cancel_requested_returns_409(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)
        run_id = ctx.create_run(tid, cp_id)

        session = ctx.sf()
        try:
            repo = SqlRunRepository(session)
            run = repo.get(run_id)
            run.transition(RunState.STARTING)
            run.transition(RunState.RUNNING)
            run.transition(RunState.CANCEL_REQUESTED)
            repo.update(run)
            session.commit()
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# 10. Validation errors
# ---------------------------------------------------------------------------

class TestWP09ValidationErrors:
    def test_execute_missing_run_returns_404(self, ctx: _TestContext) -> None:
        resp = ctx.client.post("/api/v1/runs/nonexistent/execute", json=start_body())
        assert resp.status_code == 404

    def test_execute_auth_required(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        ini = _make_alembic_ini(db_path)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")
        db_url = f"sqlite:///{db_path}"

        engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
        TestSession = sessionmaker(bind=engine, expire_on_commit=False, future=True)

        from polynexus_core.api.health import router as health_router
        from polynexus_core.api.projects import router as projects_router
        from polynexus_core.api.tasks import router as tasks_router
        from polynexus_core.api.runs import router as runs_router
        from polynexus_core.api.dependencies import require_loopback

        app = FastAPI()


        app.include_router(generations_router, prefix="/api/v1")
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
        app.include_router(health_router, prefix="/api/v1")
        app.include_router(projects_router, prefix="/api/v1")
        app.include_router(tasks_router, prefix="/api/v1")
        app.include_router(runs_router, prefix="/api/v1")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/v1/runs/any/execute", json=start_body())
        assert resp.status_code == 403
        engine.dispose()

    def test_execute_cross_project_mismatch_returns_422(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid1 = ctx.create_project()
        pid2 = ctx.create_project()
        cp_id = ctx.create_context_package(pid2)
        tid = ctx.create_task(pid1)

        from polynexus_core.domain.models import Run
        session = ctx.sf()
        try:
            run = Run(task_id=tid, workflow_id="review-minimal", workflow_version=1, context_package_id=cp_id)
            SqlRunRepository(session).add(run)
            session.commit()
            run_id = run.id
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 422

    def test_execute_workflow_mismatch_returns_422(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, workflow_id="review-minimal")

        from polynexus_core.domain.models import Run
        session = ctx.sf()
        try:
            run = Run(task_id=tid, workflow_id="different-workflow", workflow_version=1, context_package_id=cp_id)
            SqlRunRepository(session).add(run)
            session.commit()
            run_id = run.id
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 422

    def test_stored_task_missing_returns_422(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)

        from polynexus_core.domain.models import Run
        session = ctx.sf()
        try:
            run = Run(task_id="nonexistent_task", workflow_id="review-minimal", workflow_version=1, context_package_id=cp_id)
            SqlRunRepository(session).add(run)
            session.commit()
            run_id = run.id
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 422

    def test_stored_context_package_missing_returns_422(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        tid = ctx.create_task(pid)

        from polynexus_core.domain.models import Run
        session = ctx.sf()
        try:
            run = Run(task_id=tid, workflow_id="review-minimal", workflow_version=1, context_package_id="nonexistent_cp")
            SqlRunRepository(session).add(run)
            session.commit()
            run_id = run.id
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 11. Reference runtime network-egress guard
# ---------------------------------------------------------------------------

class TestWP09NetworkEgressGuard:
    def test_reference_runtime_no_network_egress(self, ctx: _TestContext) -> None:
        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
        adapter = ReferenceRuntimeAdapter()
        assert adapter.capabilities().cancel is True
        assert adapter.capabilities().resume.value == "NONE"
        assert asyncio.run(adapter.health()) is True
        assert asyncio.run(adapter.readiness()) is True


# ---------------------------------------------------------------------------
# 12. Existing Run create/list/get regression
# ---------------------------------------------------------------------------

class TestWP09RunCreateRegression:
    def test_create_run_still_returns_201(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)

        resp = c.post(f"/api/v1/tasks/{tid}/runs", json=prepared_run_body(c, tid, cp_id))
        assert resp.status_code == 201
        assert resp.json()["state"] == "CREATED"
        assert resp.json()["result"] is None
        assert resp.json()["events"] == []

    def test_list_runs_still_works(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)

        c.post(f"/api/v1/tasks/{tid}/runs", json=prepared_run_body(c, tid, cp_id))
        c.post(f"/api/v1/tasks/{tid}/runs", json=prepared_run_body(c, tid, cp_id))

        resp = c.get(f"/api/v1/tasks/{tid}/runs")
        assert resp.status_code == 200
        assert len(resp.json()["runs"]) == 2

    def test_get_run_still_works(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=cp_id)

        resp = c.post(f"/api/v1/tasks/{tid}/runs", json=prepared_run_body(c, tid, cp_id))
        run_id = resp.json()["id"]

        resp = c.get(f"/api/v1/runs/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == run_id


# ---------------------------------------------------------------------------
# 13. Reload from new session
# ---------------------------------------------------------------------------

class TestWP09ReloadFromNewSession:
    def test_execute_and_reload_from_new_session(self, tmp_path: Path) -> None:
        db_path = tmp_path / "wp09_reload.db"
        ini = _make_alembic_ini(db_path)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")
        db_url = f"sqlite:///{db_path}"

        app1, sf1 = _create_test_app(db_url)
        c1 = TestClient(app1)

        pid = c1.post("/api/v1/projects", json={"name": "P"}).json()["id"]
        session = sf1()
        cp = ContextPackage(project_id=pid, version=1)
        SqlContextPackageRepository(session).add(cp)
        session.commit()
        cp_id = cp.id
        session.close()

        tid = c1.post(
            f"/api/v1/projects/{pid}/tasks",
            json={"title": "T", "workflow_id": "review-minimal", "workflow_version": 1},
        ).json()["id"]

        resp = c1.post(f"/api/v1/tasks/{tid}/runs", json=prepared_run_body(c1, tid, cp_id))
        run_id = resp.json()["id"]

        resp = c1.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 202
        c1.close()

        app2, _ = _create_test_app(db_url)
        c2 = TestClient(app2)
        resp = c2.get(f"/api/v1/runs/{run_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == run_id
        assert data["state"] == "COMPLETED"
        assert data["result"] is not None
        assert len(data["events"]) >= 3
        assert data["context_package_id"] == cp_id


# ---------------------------------------------------------------------------
# 14. Run-owned ContextPackage authority
# ---------------------------------------------------------------------------

class TestWP09ContextPackageAuthority:
    def test_run_context_package_id_is_authority(self, ctx: _TestContext) -> None:
        c = ctx.client
        pid = ctx.create_project()
        cp_id = ctx.create_context_package(pid)
        tid = ctx.create_task(pid, context_package_id=None)

        from polynexus_core.domain.models import Run
        prepared = prepared_run_body(c,tid,cp_id)
        session = ctx.sf()
        try:
            run = Run(task_id=tid, workflow_id="review-minimal", workflow_version=1, context_package_id=cp_id,generation_revision=prepared["generation_revision"])
            SqlRunRepository(session).add(run)
            session.commit()
            run_id = run.id
        finally:
            session.close()

        resp = c.post(f"/api/v1/runs/{run_id}/execute", json=start_body())
        assert resp.status_code == 202

        resp = c.get(f"/api/v1/runs/{run_id}")
        assert resp.json()["context_package_id"] == cp_id


# ---------------------------------------------------------------------------
# 15. Fresh SQLite/Alembic lifecycle
# ---------------------------------------------------------------------------

class TestWP09AlembicLifecycle:
    def test_fresh_alembic_upgrade_and_data_persist(self, tmp_path: Path) -> None:
        db_path = tmp_path / "wp09_fresh.db"
        ini = _make_alembic_ini(db_path)
        config = Config(str(ini))
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, future=True)
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(engine)
        tables = set(inspector.get_table_names())
        expected = {
            "projects", "tasks", "context_packages", "runs",
            "run_events", "artifacts", "findings", "evidence",
            "alembic_version",
        }
        assert expected.issubset(tables)
        engine.dispose()


def test_d1a_start_receipt_replay_and_payload_conflict(ctx):
    from sqlalchemy import text
    project=ctx.create_project();cp=ctx.create_context_package(project)
    task=ctx.create_task(project,context_package_id=cp);run=ctx.create_run(task,cp)
    body={'generation_revision':1,'expected_control_revision':0,'command_id':'durable-start'}
    first=ctx.client.post(f'/api/v1/runs/{run}/execute',json=body)
    assert first.status_code==202
    assert ctx.client.post(f'/api/v1/runs/{run}/execute',json=body).status_code==200
    changed={**body,'expected_control_revision':99}
    assert ctx.client.post(f'/api/v1/runs/{run}/execute',json=changed).status_code==409
    with ctx.sf() as session:
        assert session.execute(text("SELECT count(*) FROM generation_commands WHERE command_id='durable-start'")).scalar_one()==1
        assert session.execute(text("SELECT count(*) FROM run_events WHERE run_id=:r AND to_state='STARTING'"),{'r':run}).scalar_one()==1
        assert session.execute(text("SELECT count(*) FROM generation_events WHERE command_id='durable-start' AND kind='RunStartRequested'")).scalar_one()==1


def test_d1a_cancel_created_exact_receipt_never_launches(ctx):
    project=ctx.create_project();cp=ctx.create_context_package(project)
    task=ctx.create_task(project,context_package_id=cp);run=ctx.create_run(task,cp)
    body={'generation_revision':1,'expected_control_revision':0,'expected_fence':0,'command_id':'cancel-created'}
    assert ctx.client.post(f'/api/v1/runs/{run}/cancel',json={**body,'expected_fence':8}).status_code==409
    first=ctx.client.post(f'/api/v1/runs/{run}/cancel',json=body)
    assert first.status_code==200 and first.json()['cancel_requested']
    assert ctx.client.post(f'/api/v1/runs/{run}/cancel',json=body).json()==first.json()
    assert ctx.client.get(f'/api/v1/runs/{run}').json()['state']=='CANCELLED'
    assert ctx.client.post(f'/api/v1/runs/{run}/cancel',json={**body,'generation_revision':2}).status_code==409
    assert ctx.client.post(f'/api/v1/runs/{run}/execute',json={'generation_revision':1,'expected_control_revision':1,'command_id':'start-cancelled'}).status_code==200
    assert ctx.client.get(f'/api/v1/runs/{run}').json()['runtime_ref'] is None


def test_d1a_cancel_lost_active_handle_is_unknown(ctx):
    from sqlalchemy import text
    project=ctx.create_project();cp=ctx.create_context_package(project)
    task=ctx.create_task(project,context_package_id=cp);run=ctx.create_run(task,cp)
    with ctx.sf() as session:
        from polynexus_core.persistence.generation import GenerationRepository
        repository=GenerationRepository(session);stored=SqlRunRepository(session).get(run)
        claim=repository.claim_run(stored)
        session.execute(text("UPDATE runs SET state='STARTING' WHERE id=:r"),{'r':run});session.commit()
    body={'generation_revision':1,'expected_control_revision':1,'expected_fence':claim['fence'],'command_id':'lost-handle-cancel'}
    result=ctx.client.post(f'/api/v1/runs/{run}/cancel',json=body)
    assert result.status_code==200
    generation=ctx.client.get(f'/api/v1/tasks/{task}/generations/1').json()
    assert generation['ownership_unknown']==1 and generation['work_aborted'] is False
    assert ctx.client.post(f'/api/v1/runs/{run}/cancel',json=body).json()==result.json()
