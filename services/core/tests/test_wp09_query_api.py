"""WP-09C query API tests — read-only run-scoped queries."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from alembic import command as alembic_cmd
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from polynexus_core.api.dependencies import require_loopback
from polynexus_core.domain.enums import (
    ArtifactType, EvidenceStatus, EvidenceType, FindingSeverity, RunState,
)
from polynexus_core.domain.models import Artifact, ContextPackage, Evidence, Finding, Project, Task
from polynexus_core.persistence.database import get_session
from polynexus_core.persistence.repository import (
    SqlArtifactRepository, SqlContextPackageRepository, SqlEvidenceRepository,
    SqlFindingRepository, SqlProjectRepository, SqlRunRepository, SqlTaskRepository,
)

ALEMBIC_DIR = Path(__file__).parent.parent / "alembic"


def _make_alembic_ini(db_path: Path) -> Path:
    ini = db_path.parent / "alembic.ini"
    ini.write_text(
        "[alembic]\n"
        f"script_location = {ALEMBIC_DIR}\n"
        "prepend_sys_path = .\n"
        f"sqlalchemy.url = sqlite:///{db_path}\n"
        "\n[loggers]\nkeys = root,sqlalchemy,alembic\n[handlers]\nkeys = console\n[formatters]\nkeys = generic\n"
        "[logger_root]\nlevel = WARN\nhandlers = console\n[logger_sqlalchemy]\nlevel = WARN\nhandlers =\nqualname = sqlalchemy.engine\n"
        "[logger_alembic]\nlevel = INFO\nhandlers =\nqualname = alembic\n[handler_console]\nclass = StreamHandler\nargs = (sys.stderr,)\nlevel = NOTSET\nformatter = generic\n[formatter_generic]\nformat = %(levelname)-5.5s [%(name)s] %(message)s\ndatefmt = %H:%M:%S\n"
    )
    return ini


def _create_test_app(db_url: str) -> tuple[FastAPI, sessionmaker]:
    from polynexus_core.api.health import router as health_router
    from polynexus_core.api.projects import router as projects_router
    from polynexus_core.api.tasks import router as tasks_router
    from polynexus_core.api.runs import router as runs_router
    from polynexus_core.api.run_outputs import router as run_outputs_router
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    app = FastAPI()
    def _override_get_session():
        s = TestSession()
        try:
            yield s; s.commit()
        except Exception:
            s.rollback(); raise
        finally:
            s.close()
    def _override_auth():
        return None
    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[require_loopback] = _override_auth
    for r in (health_router, projects_router, tasks_router, runs_router, run_outputs_router):
        app.include_router(r, prefix="/api/v1")
    return app, TestSession


class _Ctx:
    def __init__(self, client: TestClient, sf: sessionmaker):
        self.client = client; self.sf = sf
    def create_project(self, name="P") -> str:
        r = self.client.post("/api/v1/projects", json={"name": name}); assert r.status_code == 201; return r.json()["id"]
    def create_cp(self, pid: str) -> str:
        s = self.sf()
        try:
            cp = ContextPackage(project_id=pid, version=1); SqlContextPackageRepository(s).add(cp); s.commit(); return cp.id
        finally: s.close()
    def create_task(self, pid: str, title="T") -> str:
        r = self.client.post(f"/api/v1/projects/{pid}/tasks", json={"title": title, "workflow_id": "review-minimal", "workflow_version": 1})
        assert r.status_code == 201; return r.json()["id"]
    def create_run(self, tid: str, cpid: str) -> str:
        r = self.client.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": cpid}); assert r.status_code == 201; return r.json()["id"]


@pytest.fixture()
def ctx(tmp_path: Path) -> _Ctx:
    db_path = tmp_path / "test.db"
    ini = _make_alembic_ini(db_path)
    config = Config(str(ini)); alembic_cmd.upgrade(config, "head")
    db_url = f"sqlite:///{db_path}"
    app, sf = _create_test_app(db_url)
    client = TestClient(app)
    yield _Ctx(client, sf)


ENDPOINTS = [
    "/runs/{run_id}/result",
    "/runs/{run_id}/findings",
    "/runs/{run_id}/evidence",
    "/runs/{run_id}/artifacts",
    "/runs/{run_id}/history",
]


# 1. 403
@pytest.mark.parametrize("ep", ENDPOINTS)
def test_403_each_endpoint(tmp_path: Path, ep: str):
    db_path = tmp_path / "test.db"
    ini = _make_alembic_ini(db_path)
    config = Config(str(ini)); alembic_cmd.upgrade(config, "head")
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, future=True)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    from polynexus_core.api.health import router as health_router
    from polynexus_core.api.projects import router as projects_router
    from polynexus_core.api.tasks import router as tasks_router
    from polynexus_core.api.runs import router as runs_router
    from polynexus_core.api.run_outputs import router as run_outputs_router
    app = FastAPI()
    def _override_get_session():
        s = TestSession()
        try: yield s; s.commit()
        except Exception: s.rollback(); raise
        finally: s.close()
    app.dependency_overrides[get_session] = _override_get_session
    for r in (health_router, projects_router, tasks_router, runs_router, run_outputs_router):
        app.include_router(r, prefix="/api/v1")
    client = TestClient(app, raise_server_exceptions=False)
    path = ep.replace("{run_id}", "any")
    assert client.get(f"/api/v1{path}").status_code == 403
    engine.dispose()


# 2. 404
@pytest.mark.parametrize("ep", ENDPOINTS)
def test_404_each_endpoint(ctx: _Ctx, ep: str):
    path = ep.replace("{run_id}", "nonexistent")
    assert ctx.client.get(f"/api/v1{path}").status_code == 404


# 3. empty wrappers
def test_empty_wrappers(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid); tid = ctx.create_task(pid); rid = ctx.create_run(tid, cpid)
    for ep, key, empty in [
        (f"/runs/{rid}/result", "result", None),
        (f"/runs/{rid}/findings", "findings", []),
        (f"/runs/{rid}/evidence", "evidence", []),
        (f"/runs/{rid}/artifacts", "artifacts", []),
        (f"/runs/{rid}/history", "events", []),
    ]:
        r = ctx.client.get(f"/api/v1{ep}")
        assert r.status_code == 200, f"{ep} {r.text}"
        assert r.json()[key] == empty


# Helper to execute with injected finding/evidence/artifact
def _execute_with_injected_outputs(c: TestClient, sf, pid, tid, rid):
    from polynexus_core.runtime.contracts import RuntimeResult
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
    injected_evidence = Evidence(task_id=tid, run_id=rid, actor_id="test:adapter", source="test", type=EvidenceType.TOOL_EVIDENCE, status=EvidenceStatus.PASS)
    injected_finding = Finding(task_id=tid, run_id=rid, title="TF", description="desc", severity=FindingSeverity.LOW, evidence_refs=(injected_evidence.id,))
    injected_artifact = Artifact(project_id=pid, artifact_type=ArtifactType.TEXT, mime_type="text/plain", source_type="test", storage_ref="test/ref", sha256="a"*64, task_id=tid, run_id=rid)
    orig_result = ReferenceRuntimeAdapter.result
    orig_artifacts = ReferenceRuntimeAdapter.artifacts
    async def inj_result(self_adapter, runtime_ref):
        return RuntimeResult(summary="inj", evidence=(injected_evidence,), findings=(injected_finding,), artifacts=(injected_artifact,))
    async def inj_artifacts(self_adapter, runtime_ref):
        return ()
    ReferenceRuntimeAdapter.result = inj_result  # type: ignore
    ReferenceRuntimeAdapter.artifacts = inj_artifacts  # type: ignore
    try:
        r = c.post(f"/api/v1/runs/{rid}/execute")
        assert r.status_code == 202
    finally:
        ReferenceRuntimeAdapter.result = orig_result  # type: ignore
        ReferenceRuntimeAdapter.artifacts = orig_artifacts  # type: ignore
    return injected_evidence, injected_finding, injected_artifact


# 4-7. success fidelity + close/reopen + IDs match + deterministic history
def test_success_fidelity_and_reload(tmp_path: Path):
    db_path = tmp_path / "wp09c.db"
    ini = _make_alembic_ini(db_path)
    config = Config(str(ini)); alembic_cmd.upgrade(config, "head")
    db_url = f"sqlite:///{db_path}"
    app1, sf1 = _create_test_app(db_url)
    c1 = TestClient(app1)
    pid = c1.post("/api/v1/projects", json={"name": "P"}).json()["id"]
    s = sf1()
    try:
        cp = ContextPackage(project_id=pid, version=1); SqlContextPackageRepository(s).add(cp); s.commit(); cpid = cp.id
    finally: s.close()
    tid = c1.post(f"/api/v1/projects/{pid}/tasks", json={"title": "T", "workflow_id": "review-minimal", "workflow_version": 1}).json()["id"]
    rid = c1.post(f"/api/v1/tasks/{tid}/runs", json={"context_package_id": cpid}).json()["id"]
    # injected evidence with distinct observed_at for ordering check + supervisor evidence will also be present
    from polynexus_core.runtime.contracts import RuntimeResult
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
    from polynexus_core.domain.enums import ArtifactType, EvidenceStatus, EvidenceType, FindingSeverity
    ev1 = Evidence(task_id=tid, run_id=rid, actor_id="a1", source="s", type=EvidenceType.TOOL_EVIDENCE, status=EvidenceStatus.PASS)
    f1 = Finding(task_id=tid, run_id=rid, title="TF", description="d", severity=FindingSeverity.LOW, evidence_refs=(ev1.id,))
    art = Artifact(project_id=pid, artifact_type=ArtifactType.TEXT, mime_type="text/plain", source_type="test", storage_ref="ref1", sha256="b"*64, task_id=tid, run_id=rid)
    orig_r = ReferenceRuntimeAdapter.result
    orig_a = ReferenceRuntimeAdapter.artifacts
    async def inj_r(self_adapter, rr): return RuntimeResult(summary="inj", evidence=(ev1,), findings=(f1,), artifacts=(art,))
    async def inj_a(self_adapter, rr): return ()
    ReferenceRuntimeAdapter.result = inj_r  # type: ignore
    ReferenceRuntimeAdapter.artifacts = inj_a  # type: ignore
    try:
        assert c1.post(f"/api/v1/runs/{rid}/execute").status_code == 202
    finally:
        ReferenceRuntimeAdapter.result = orig_r  # type: ignore
        ReferenceRuntimeAdapter.artifacts = orig_a  # type: ignore
    c1.close()
    # close/reopen
    app2, sf2 = _create_test_app(db_url)
    c2 = TestClient(app2)
    # 4. result fidelity — exact parity: result IDs must exactly equal queried endpoints
    r = c2.get(f"/api/v1/runs/{rid}/result")
    assert r.status_code == 200
    result = r.json()["result"]
    assert result is not None
    # Retrieve endpoints first to get actual persisted IDs
    r2 = c2.get(f"/api/v1/runs/{rid}/evidence")
    r3 = c2.get(f"/api/v1/runs/{rid}/findings")
    r4 = c2.get(f"/api/v1/runs/{rid}/artifacts")
    assert r2.status_code == 200 and r3.status_code == 200 and r4.status_code == 200
    assert set(result["finding_ids"]) == {f["id"] for f in r3.json()["findings"]}
    # Gate evaluation evidence is included in RunResult.evidence_ids before
    # construction, so exact parity holds.
    assert set(result["evidence_ids"]) == {e["id"] for e in r2.json()["evidence"]}
    assert set(result["artifact_ids"]) == {a["id"] for a in r4.json()["artifacts"]}
    # Also verify injected IDs are present
    assert f1.id in result["finding_ids"]
    assert ev1.id in result["evidence_ids"]
    assert art.id in result["artifact_ids"]
    # JSON tuple fields serialize as arrays
    assert isinstance(result["finding_ids"], list)
    # 7. history deterministic ordering
    r5 = c2.get(f"/api/v1/runs/{rid}/history")
    events = r5.json()["events"]
    assert [(e["from_state"], e["to_state"]) for e in events] == [("CREATED","STARTING"),("STARTING","RUNNING"),("RUNNING","COMPLETED")]
    # timestamps ordered
    times = [e["occurred_at"] for e in events]
    assert times == sorted(times)


def test_equal_timestamp_history_ordering(ctx: _Ctx):
    """Regression: same occurred_at, different ID must order by id."""
    from datetime import datetime, timezone
    from polynexus_core.domain.models import RunEvent
    pid = ctx.create_project(); cpid = ctx.create_cp(pid); tid = ctx.create_task(pid); rid = ctx.create_run(tid, cpid)
    ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    e1 = RunEvent(run_id=rid, from_state=RunState.STARTING, to_state=RunState.RUNNING, occurred_at=ts, id="aaa_run-event_1")
    e2 = RunEvent(run_id=rid, from_state=RunState.RUNNING, to_state=RunState.COMPLETED, occurred_at=ts, id="zzz_run-event_2")
    # Insert in reverse ID order to verify deterministic sort
    s = ctx.sf()
    try:
        from polynexus_core.persistence.repository import SqlRunEventRepository
        repo = SqlRunEventRepository(s)
        repo.add(e2); repo.add(e1); s.commit()
    finally: s.close()
    hist = ctx.client.get(f"/api/v1/runs/{rid}/history").json()["events"]
    # Filter to the two injected events (there may be no prior events because Run is CREATED)
    ids = [e["id"] for e in hist if e["id"] in ("aaa_run-event_1", "zzz_run-event_2")]
    assert ids == ["aaa_run-event_1", "zzz_run-event_2"]


# 8. multiple runs under one task do not leak
def test_multiple_runs_no_leak(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid); tid = ctx.create_task(pid)
    r1 = ctx.create_run(tid, cpid); r2 = ctx.create_run(tid, cpid)
    # execute r1 only with injected
    from polynexus_core.runtime.contracts import RuntimeResult
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
    ev = Evidence(task_id=tid, run_id=r1, actor_id="a", source="s", type=EvidenceType.TOOL_EVIDENCE, status=EvidenceStatus.PASS)
    f = Finding(task_id=tid, run_id=r1, title="t", description="d", severity=FindingSeverity.LOW)
    art = Artifact(project_id=pid, artifact_type=ArtifactType.TEXT, mime_type="text/plain", source_type="t", storage_ref="s", sha256="c"*64, task_id=tid, run_id=r1)
    orig_r = ReferenceRuntimeAdapter.result; orig_a = ReferenceRuntimeAdapter.artifacts
    async def inj_r(self_adapter, rr): return RuntimeResult(summary="x", evidence=(ev,), findings=(f,), artifacts=(art,))
    async def inj_a(self_adapter, rr): return ()
    ReferenceRuntimeAdapter.result = inj_r  # type: ignore
    ReferenceRuntimeAdapter.artifacts = inj_a  # type: ignore
    try:
        assert ctx.client.post(f"/api/v1/runs/{r1}/execute").status_code == 202
    finally:
        ReferenceRuntimeAdapter.result = orig_r  # type: ignore
        ReferenceRuntimeAdapter.artifacts = orig_a  # type: ignore
    # r2 should have empty
    assert ctx.client.get(f"/api/v1/runs/{r2}/findings").json()["findings"] == []
    assert ctx.client.get(f"/api/v1/runs/{r2}/evidence").json()["evidence"] == []
    assert ctx.client.get(f"/api/v1/runs/{r2}/artifacts").json()["artifacts"] == []
    # r1 should have
    assert len(ctx.client.get(f"/api/v1/runs/{r1}/findings").json()["findings"]) >= 1


# 9. runs under different tasks in same project do not leak
def test_different_tasks_no_leak(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid)
    t1 = ctx.create_task(pid); t2 = ctx.create_task(pid)
    r1 = ctx.create_run(t1, cpid)
    from polynexus_core.runtime.contracts import RuntimeResult
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
    ev = Evidence(task_id=t1, run_id=r1, actor_id="a", source="s", type=EvidenceType.TOOL_EVIDENCE, status=EvidenceStatus.PASS)
    orig_r = ReferenceRuntimeAdapter.result; orig_a = ReferenceRuntimeAdapter.artifacts
    async def inj_r(self_adapter, rr): return RuntimeResult(summary="x", evidence=(ev,), findings=(), artifacts=())
    async def inj_a(self_adapter, rr): return ()
    ReferenceRuntimeAdapter.result = inj_r  # type: ignore
    ReferenceRuntimeAdapter.artifacts = inj_a  # type: ignore
    try: ctx.client.post(f"/api/v1/runs/{r1}/execute")
    finally:
        ReferenceRuntimeAdapter.result = orig_r  # type: ignore
        ReferenceRuntimeAdapter.artifacts = orig_a  # type: ignore
    r_other = ctx.create_run(t2, cpid)
    assert ctx.client.get(f"/api/v1/runs/{r_other}/evidence").json()["evidence"] == []


# 10. runs under different projects do not leak artifacts
def test_different_projects_no_leak(ctx: _Ctx):
    p1 = ctx.create_project("P1"); c1 = ctx.create_cp(p1); t1 = ctx.create_task(p1); r1 = ctx.create_run(t1, c1)
    p2 = ctx.create_project("P2"); c2 = ctx.create_cp(p2); t2 = ctx.create_task(p2); r2 = ctx.create_run(t2, c2)
    from polynexus_core.runtime.contracts import RuntimeResult
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
    art = Artifact(project_id=p1, artifact_type=ArtifactType.TEXT, mime_type="text/plain", source_type="t", storage_ref="s", sha256="d"*64, task_id=t1, run_id=r1)
    ev = Evidence(task_id=t1, run_id=r1, actor_id="a", source="s", type=EvidenceType.TOOL_EVIDENCE, status=EvidenceStatus.PASS)
    orig_r = ReferenceRuntimeAdapter.result; orig_a = ReferenceRuntimeAdapter.artifacts
    async def inj_r(self_adapter, rr): return RuntimeResult(summary="x", evidence=(ev,), findings=(), artifacts=(art,))
    async def inj_a(self_adapter, rr): return ()
    ReferenceRuntimeAdapter.result = inj_r  # type: ignore
    ReferenceRuntimeAdapter.artifacts = inj_a  # type: ignore
    try: ctx.client.post(f"/api/v1/runs/{r1}/execute")
    finally:
        ReferenceRuntimeAdapter.result = orig_r  # type: ignore
        ReferenceRuntimeAdapter.artifacts = orig_a  # type: ignore
    # r2 artifacts should not contain r1 artifact
    assert all(a["id"] != art.id for a in ctx.client.get(f"/api/v1/runs/{r2}/artifacts").json()["artifacts"])


# 11. missing parent Task 422
def test_missing_parent_task_422(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid); tid = ctx.create_task(pid); rid = ctx.create_run(tid, cpid)
    # delete task directly
    from sqlalchemy import text
    s = ctx.sf()
    try:
        s.execute(text("DELETE FROM tasks WHERE id = :id"), {"id": tid}); s.commit()
    finally: s.close()
    for ep in ["/result", "/findings", "/evidence", "/artifacts", "/history"]:
        assert ctx.client.get(f"/api/v1/runs/{rid}{ep}").status_code == 422


# 12. dangling result output ID 422
def test_dangling_result_id_422(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid); tid = ctx.create_task(pid); rid = ctx.create_run(tid, cpid)
    # execute to get COMPLETED with result
    assert ctx.client.post(f"/api/v1/runs/{rid}/execute").status_code == 202
    # corrupt result to reference non-existent finding
    from sqlalchemy import text
    s = ctx.sf()
    try:
        s.execute(text("UPDATE runs SET result_finding_ids = :v WHERE id = :id"), {"v": json.dumps(["nonexistent"]), "id": rid}); s.commit()
    finally: s.close()
    assert ctx.client.get(f"/api/v1/runs/{rid}/result").status_code == 422


# 13a. cross-run finding 422 (different run)
def test_cross_run_finding_422(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid)
    t1 = ctx.create_task(pid); r1 = ctx.create_run(t1, cpid)
    t2 = ctx.create_task(pid); r2 = ctx.create_run(t2, cpid)
    from polynexus_core.domain.enums import FindingSeverity
    f = Finding(task_id=t2, run_id=r2, title="cross", description="d", severity=FindingSeverity.LOW)
    s = ctx.sf()
    try:
        from polynexus_core.persistence.repository import SqlFindingRepository
        repo = SqlFindingRepository(s); repo.add(f); s.commit()
        from sqlalchemy import text
        s.execute(text("UPDATE runs SET result_finding_ids = :v, result_status='COMPLETED', result_summary='x' WHERE id = :id"), {"v": json.dumps([f.id]), "id": r1}); s.commit()
    finally: s.close()
    assert ctx.client.get(f"/api/v1/runs/{r1}/result").status_code == 422

# 13b. same run_id, other task ownership -> findings/evidence 422
def test_findings_same_run_other_task_422(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid)
    t1 = ctx.create_task(pid); r1 = ctx.create_run(t1, cpid)
    t2 = ctx.create_task(pid)
    f = Finding(task_id=t2, run_id=r1, title="cross-task", description="d", severity=FindingSeverity.LOW)
    s = ctx.sf()
    try:
        from polynexus_core.persistence.repository import SqlFindingRepository
        SqlFindingRepository(s).add(f); s.commit()
    finally: s.close()
    assert ctx.client.get(f"/api/v1/runs/{r1}/findings").status_code == 422

def test_evidence_same_run_other_task_422(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid)
    t1 = ctx.create_task(pid); r1 = ctx.create_run(t1, cpid)
    t2 = ctx.create_task(pid)
    ev = Evidence(task_id=t2, run_id=r1, actor_id="a", source="s", type=EvidenceType.TOOL_EVIDENCE, status=EvidenceStatus.PASS)
    s = ctx.sf()
    try:
        SqlEvidenceRepository(s).add(ev); s.commit()
    finally: s.close()
    assert ctx.client.get(f"/api/v1/runs/{r1}/evidence").status_code == 422


# 14. cross-project artifact 422
def test_cross_project_artifact_422(ctx: _Ctx):
    p1 = ctx.create_project("P1"); c1 = ctx.create_cp(p1); t1 = ctx.create_task(p1); r1 = ctx.create_run(t1, c1)
    p2 = ctx.create_project("P2")
    art = Artifact(project_id=p2, artifact_type=ArtifactType.TEXT, mime_type="text/plain", source_type="t", storage_ref="s", sha256="e"*64, task_id=t1, run_id=r1)
    s = ctx.sf()
    try:
        SqlArtifactRepository(s).add(art); s.commit()
        from sqlalchemy import text
        s.execute(text("UPDATE runs SET result_artifact_ids = :v, result_status='COMPLETED', result_summary='x' WHERE id = :id"), {"v": json.dumps([art.id]), "id": r1}); s.commit()
    finally: s.close()
    # result should be 422 due to cross-project artifact
    assert ctx.client.get(f"/api/v1/runs/{r1}/result").status_code == 422
    # artifacts endpoint validates ownership -> also 422 because artifact project mismatch
    assert ctx.client.get(f"/api/v1/runs/{r1}/artifacts").status_code == 422


# 15. artifact only metadata
def test_artifact_only_metadata(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid); tid = ctx.create_task(pid); rid = ctx.create_run(tid, cpid)
    from polynexus_core.runtime.contracts import RuntimeResult
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
    art = Artifact(project_id=pid, artifact_type=ArtifactType.TEXT, mime_type="text/plain", source_type="t", storage_ref="my/ref", sha256="f"*64, size=123, task_id=tid, run_id=rid)
    orig_r = ReferenceRuntimeAdapter.result; orig_a = ReferenceRuntimeAdapter.artifacts
    async def inj_r(self_adapter, rr): return RuntimeResult(summary="x", evidence=(), findings=(), artifacts=(art,))
    async def inj_a(self_adapter, rr): return ()
    ReferenceRuntimeAdapter.result = inj_r  # type: ignore
    ReferenceRuntimeAdapter.artifacts = inj_a  # type: ignore
    try: ctx.client.post(f"/api/v1/runs/{rid}/execute")
    finally:
        ReferenceRuntimeAdapter.result = orig_r  # type: ignore
        ReferenceRuntimeAdapter.artifacts = orig_a  # type: ignore
    data = ctx.client.get(f"/api/v1/runs/{rid}/artifacts").json()["artifacts"][0]
    assert data["storage_ref"] == "my/ref"
    assert "content" not in data
    assert "data" not in data


# 16. evidence type/status exact + AI_OPINION not upgraded
def test_evidence_type_status_exact(ctx: _Ctx):
    pid = ctx.create_project(); cpid = ctx.create_cp(pid); tid = ctx.create_task(pid); rid = ctx.create_run(tid, cpid)
    # Persist an AI_OPINION evidence directly and verify API returns it verbatim
    ai_ev = Evidence(task_id=tid, run_id=rid, actor_id="ai:test", source="test", type=EvidenceType.AI_OPINION, status=EvidenceStatus.OBSERVED)
    s = ctx.sf()
    try:
        SqlEvidenceRepository(s).add(ai_ev); s.commit()
    finally: s.close()
    # Also execute to get supervisor RUNTIME_EVIDENCE
    assert ctx.client.post(f"/api/v1/runs/{rid}/execute").status_code == 202
    evs = ctx.client.get(f"/api/v1/runs/{rid}/evidence").json()["evidence"]
    by_id = {e["id"]: e for e in evs}
    assert ai_ev.id in by_id
    assert by_id[ai_ev.id]["type"] == EvidenceType.AI_OPINION.value
    assert by_id[ai_ev.id]["status"] == EvidenceStatus.OBSERVED.value
    # supervisor evidence remains RUNTIME_EVIDENCE PASS, not upgraded
    # Filter out gate evaluation DOCUMENT_EVIDENCE (additive layer from WP-13)
    runtime_evs = [
        e for e in evs
        if e["id"] != ai_ev.id and e.get("source") != "workflow-gate-evaluation"
    ]
    assert len(runtime_evs) >= 1
    for ev in runtime_evs:
        assert ev["type"] == EvidenceType.RUNTIME_EVIDENCE.value
