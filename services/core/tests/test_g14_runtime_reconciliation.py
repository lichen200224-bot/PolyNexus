"""G14 restart reconciliation and fail-closed cleanup tests.

These tests use temporary SQLite databases and deterministic fake adapters.  A
restart pass may inspect an existing runtime reference, but it must never call
``create_run`` or ``submit`` and must never silently rebind a Run.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.models import (
    Artifact,
    ContextPackage,
    Evidence,
    Finding,
    Project,
    Run,
    Task,
)
from polynexus_core.domain.enums import (
    ArtifactType,
    EvidenceStatus,
    EvidenceType,
    FindingSeverity,
)
from polynexus_core.persistence.models import Base
from polynexus_core.persistence.repository import (
    SqlArtifactRepository,
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlFindingRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlRuntimeBindingSnapshotRepository,
    SqlTaskRepository,
)
from polynexus_core.runtime.contracts import (
    RuntimeCapabilities,
    RuntimeResult,
    RuntimeStatus,
)
from polynexus_core.runtime.reconciliation import (
    RestartReconciliationError,
    reconcile_non_terminal_runs,
)
from polynexus_core.runtime.registry import RuntimeRegistry, build_reference_profile


def _upgrade_to_head(db_path: Path) -> None:
    """Prepare an application-startup fixture through Alembic only."""
    from alembic import command as alembic_cmd
    from alembic.config import Config

    config = Config()
    config.set_main_option(
        "script_location", str(Path(__file__).parent.parent / "alembic")
    )
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    alembic_cmd.upgrade(config, "head")


class _RestartAdapter:
    def __init__(
        self,
        states: dict[str, RunState],
        *,
        post_cleanup_states: dict[str, RunState] | None = None,
        cleanup_returns: bool = True,
        status_raises: bool = False,
        cleanup_cancels: bool = False,
        external_status_cancels: bool = False,
        runtime_result: RuntimeResult | None = None,
        version_raises: bool = False,
        version_value: str = "test-restart-adapter/1",
    ) -> None:
        self.states = states
        self.post_cleanup_states = post_cleanup_states or {}
        self.cleanup_returns = cleanup_returns
        self.status_raises = status_raises
        self.cleanup_cancels = cleanup_cancels
        self.external_status_cancels = external_status_cancels
        self.runtime_result = runtime_result
        self.version_raises = version_raises
        self.version_value = version_value
        self.cleaned: set[str] = set()
        self.status_calls = 0
        self.cancel_calls = 0
        self.cleanup_calls = 0
        self.create_calls = 0
        self.submit_calls = 0
        self.result_calls = 0

    async def health(self) -> bool:
        return True

    async def readiness(self) -> bool:
        return True

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(cancel=True)

    async def create_run(self, context) -> str:
        self.create_calls += 1
        raise AssertionError("restart reconciliation must not create a runtime Run")

    async def submit(self, runtime_ref: str, task) -> None:
        self.submit_calls += 1
        raise AssertionError("restart reconciliation must not submit a runtime Run")

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        self.status_calls += 1
        if self.external_status_cancels:
            task = asyncio.current_task()
            assert task is not None
            task.cancel()
            await asyncio.sleep(0)
        if self.status_raises:
            raise RuntimeError("vendor status failure with secret marker")
        if runtime_ref in self.cleaned:
            return RuntimeStatus(
                state=self.post_cleanup_states.get(runtime_ref, RunState.CANCELLED)
            )
        return RuntimeStatus(state=self.states[runtime_ref])

    async def result(self, runtime_ref: str) -> RuntimeResult:
        self.result_calls += 1
        return self.runtime_result or RuntimeResult(
            summary="raw vendor result SECRET_MARKER"
        )

    async def cancel(self, runtime_ref: str) -> None:
        self.cancel_calls += 1

    async def resume(self, runtime_ref: str, checkpoint=None) -> None:
        raise NotImplementedError

    async def artifacts(self, runtime_ref: str):
        return ()

    async def cleanup(self, runtime_ref: str) -> bool:
        self.cleanup_calls += 1
        if self.cleanup_cancels:
            raise asyncio.CancelledError()
        self.cleaned.add(runtime_ref)
        return self.cleanup_returns

    def version_info(self) -> str:
        if self.version_raises:
            raise RuntimeError("version secret marker")
        return self.version_value


@pytest.fixture()
def db(tmp_path: Path):
    db_path = tmp_path / "g14-reconciliation.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = SessionFactory()
    yield session, SessionFactory, engine
    session.close()
    engine.dispose()


def _seed_run(
    session: Session,
    *,
    state: RunState,
    runtime_ref: str,
    bind: bool = True,
) -> Run:
    project = Project(name="G14")
    context = ContextPackage(project_id=project.id, version=1)
    task = Task(
        project_id=project.id,
        title="restart reconciliation",
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id=context.id,
    )
    run = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
        runtime_ref=runtime_ref,
    )
    if state in {RunState.STARTING, RunState.RUNNING, RunState.CANCEL_REQUESTED}:
        run.transition(RunState.STARTING)
    if state is RunState.RUNNING:
        run.transition(RunState.RUNNING)
    if state is RunState.CANCEL_REQUESTED:
        run.transition(RunState.CANCEL_REQUESTED)

    SqlProjectRepository(session).add(project)
    SqlContextPackageRepository(session).add(context)
    SqlTaskRepository(session).add(task)
    SqlRunRepository(session).add(run)
    session.commit()

    if bind:
        profile = build_reference_profile()
        SqlRuntimeBindingSnapshotRepository(session).insert_once(
            profile.bind(run.id, resolved_at=run.created_at)
        )
        session.commit()
    return run


def _registry(adapter: _RestartAdapter) -> RuntimeRegistry:
    registry = RuntimeRegistry()
    registry.register(build_reference_profile(), lambda: adapter)
    return registry


def test_completed_runtime_is_reloaded_without_resubmission(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:completed",
    )
    adapter = _RestartAdapter({"runtime:completed": RunState.COMPLETED})

    report = asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))
    session.commit()

    assert report == type(report)(examined=1, reconciled=1, orphaned=0)
    assert adapter.create_calls == 0
    assert adapter.submit_calls == 0
    assert adapter.result_calls == 1

    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.COMPLETED
    assert reloaded.result is not None
    assert reloaded.result.summary == "Run completed after restart reconciliation"
    assert "SECRET_MARKER" not in reloaded.result.summary
    restart_evidence = SqlEvidenceRepository(reloaded_session).list_by_run(run.id)
    assert len(restart_evidence) == 1
    assert restart_evidence[0].metadata["reconciled_after_restart"] is True
    assert "SECRET_MARKER" not in str(restart_evidence[0].metadata)
    assert [event.to_state for event in reloaded.events][-1] is RunState.COMPLETED
    reloaded_session.close()

    second_session = SessionFactory()
    second_report = asyncio.run(
        reconcile_non_terminal_runs(second_session, _registry(adapter))
    )
    assert second_report == type(second_report)(examined=0, reconciled=0, orphaned=0)
    assert adapter.result_calls == 1
    second_session.close()


def test_completed_runtime_retains_owned_safe_normalized_outputs(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:safe-output",
    )
    task = SqlTaskRepository(session).get(run.task_id)
    assert task is not None
    safe_evidence = Evidence(
        task_id=run.task_id,
        run_id=run.id,
        actor_id="adapter:normalized",
        source="normalized-runtime",
        type=EvidenceType.RUNTIME_EVIDENCE,
        status=EvidenceStatus.OBSERVED,
        metadata={"safe_key": "safe_value"},
    )
    safe_finding = Finding(
        task_id=run.task_id,
        run_id=run.id,
        title="Safe finding",
        description="Safe normalized finding",
        severity=FindingSeverity.LOW,
    )
    safe_artifact = Artifact(
        project_id=task.project_id,
        task_id=run.task_id,
        run_id=run.id,
        artifact_type=ArtifactType.TEXT,
        mime_type="text/plain",
        source_type="normalized-runtime",
        storage_ref="artifact://safe-output",
        sha256="safe-sha256",
    )
    adapter = _RestartAdapter(
        {"runtime:safe-output": RunState.COMPLETED},
        runtime_result=RuntimeResult(
            summary="opaque credential value Q7m9z2-random",
            evidence=(safe_evidence,),
            findings=(safe_finding,),
            artifacts=(safe_artifact,),
        ),
    )

    report = asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))
    session.commit()
    assert report == type(report)(examined=1, reconciled=1, orphaned=0)

    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.result is not None
    assert reloaded.result.summary == "Run completed after restart reconciliation"
    assert "Q7m9z2" not in reloaded.result.summary
    assert reloaded.result.finding_ids == (safe_finding.id,)
    assert reloaded.result.artifact_ids == (safe_artifact.id,)
    assert len(SqlFindingRepository(reloaded_session).list_by_run(run.id)) == 1
    assert len(SqlArtifactRepository(reloaded_session).list_by_run(run.id)) == 1
    evidence = SqlEvidenceRepository(reloaded_session).list_by_run(run.id)
    assert evidence[0].metadata["safe_key"] == "safe_value"
    assert evidence[-1].metadata["adapter_version"] == "test-restart-adapter/1"
    reloaded_session.close()


def test_completed_runtime_without_version_provenance_is_orphaned(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:missing-version",
    )
    adapter = _RestartAdapter(
        {"runtime:missing-version": RunState.COMPLETED},
        version_raises=True,
    )

    report = asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))
    session.commit()
    assert report == type(report)(examined=1, reconciled=0, orphaned=1)
    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.ORPHANED
    assert reloaded.result is None
    assert all("secret" not in (event.reason or "").lower() for event in reloaded.events)
    reloaded_session.close()


def test_completed_runtime_with_opaque_version_is_orphaned(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:opaque-version",
    )
    adapter = _RestartAdapter(
        {"runtime:opaque-version": RunState.COMPLETED},
        version_value="Q7m9z2-random-credential",
    )

    report = asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))
    session.commit()
    assert report == type(report)(examined=1, reconciled=0, orphaned=1)
    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.ORPHANED
    assert reloaded.result is None
    reloaded_session.close()


def test_restart_cancel_requires_cleanup_proof_and_reloads_cancelled(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:cancel",
    )
    adapter = _RestartAdapter(
        {"runtime:cancel": RunState.RUNNING},
        post_cleanup_states={"runtime:cancel": RunState.CANCELLED},
    )

    report = asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))
    session.commit()

    assert report == type(report)(examined=1, reconciled=1, orphaned=0)
    assert adapter.cancel_calls == 1
    assert adapter.cleanup_calls == 1
    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.CANCELLED
    assert [event.to_state for event in reloaded.events][-2:] == [
        RunState.CANCEL_REQUESTED,
        RunState.CANCELLED,
    ]
    reloaded_session.close()


def test_restart_timeout_requires_timeout_cleanup_proof(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:timeout",
    )
    adapter = _RestartAdapter(
        {"runtime:timeout": RunState.TIMED_OUT},
        post_cleanup_states={"runtime:timeout": RunState.TIMED_OUT},
    )

    report = asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))
    session.commit()

    assert report == type(report)(examined=1, reconciled=1, orphaned=0)
    assert adapter.cancel_calls == 1
    assert adapter.cleanup_calls == 1
    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.TIMED_OUT
    assert [event.to_state for event in reloaded.events][-1] is RunState.TIMED_OUT
    reloaded_session.close()


def test_unverified_cleanup_becomes_orphaned_with_sanitized_reason(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.STARTING,
        runtime_ref="runtime:unknown-cleanup",
    )
    adapter = _RestartAdapter(
        {"runtime:unknown-cleanup": RunState.RUNNING},
        cleanup_returns=False,
    )

    report = asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))
    session.commit()

    assert report == type(report)(examined=1, reconciled=0, orphaned=1)
    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.ORPHANED
    orphan_events = [event for event in reloaded.events if event.to_state is RunState.ORPHANED]
    assert len(orphan_events) == 1
    assert "secret" not in (orphan_events[0].reason or "").lower()
    assert "vendor" not in (orphan_events[0].reason or "").lower()
    reloaded_session.close()


def test_status_failure_is_orphaned_without_raw_error(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:status-failure",
    )
    adapter = _RestartAdapter(
        {"runtime:status-failure": RunState.RUNNING},
        status_raises=True,
    )

    report = asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))
    session.commit()

    assert report == type(report)(examined=1, reconciled=0, orphaned=1)
    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.ORPHANED
    assert all("secret" not in (event.reason or "").lower() for event in reloaded.events)
    reloaded_session.close()


def test_cleanup_task_cancellation_is_orphaned(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:cleanup-cancelled",
    )
    adapter = _RestartAdapter(
        {"runtime:cleanup-cancelled": RunState.RUNNING},
        cleanup_cancels=True,
    )

    report = asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))
    session.commit()

    assert report == type(report)(examined=1, reconciled=0, orphaned=1)
    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.ORPHANED
    reloaded_session.close()


def test_external_reconciliation_task_cancellation_is_not_swallowed(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:external-cancel",
    )
    adapter = _RestartAdapter(
        {"runtime:external-cancel": RunState.RUNNING},
        external_status_cancels=True,
    )

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))

    # The caller owns the transaction; mirror app startup's cancellation
    # handler to prove the current Run was persisted before unwind.
    session.commit()
    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.ORPHANED
    reloaded_session.close()


def test_missing_binding_stops_before_partial_mutation(db) -> None:
    session, SessionFactory, engine = db
    run = _seed_run(
        session,
        state=RunState.RUNNING,
        runtime_ref="runtime:unbound",
        bind=False,
    )
    adapter = _RestartAdapter({"runtime:unbound": RunState.RUNNING})

    with pytest.raises(RestartReconciliationError):
        asyncio.run(reconcile_non_terminal_runs(session, _registry(adapter)))

    session.rollback()
    session.close()
    reloaded_session = SessionFactory()
    reloaded = SqlRunRepository(reloaded_session).get(run.id)
    assert reloaded is not None
    assert reloaded.state is RunState.RUNNING
    assert reloaded.events[-1].to_state is RunState.RUNNING
    assert adapter.cancel_calls == 0
    assert adapter.cleanup_calls == 0
    reloaded_session.close()


def test_app_lifespan_unbound_run_stops_and_disposes_engine(monkeypatch, tmp_path: Path) -> None:
    import polynexus_core.app as app_module
    from polynexus_core.persistence.database import dispose_engine

    db_path = tmp_path / "g14-app-unbound.db"
    _upgrade_to_head(db_path)
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    seed_session = SessionFactory()
    _seed_run(
        seed_session,
        state=RunState.RUNNING,
        runtime_ref="runtime:app-unbound",
        bind=False,
    )
    seed_session.close()
    engine.dispose()

    monkeypatch.setenv("POLYNEXUS_DATABASE_URL", f"sqlite:///{db_path}")
    dispose_engine()
    with pytest.raises(RestartReconciliationError):
        with TestClient(app_module.create_app()):
            pass

    from polynexus_core.persistence.database import get_engine

    with pytest.raises(RuntimeError):
        get_engine()


def test_app_lifespan_runs_reconciliation_before_serving(monkeypatch, tmp_path: Path) -> None:
    import polynexus_core.app as app_module
    import polynexus_core.runtime.reconciliation as reconciliation_module

    calls: list[Session] = []

    async def _fake_reconcile(session: Session):
        calls.append(session)

    monkeypatch.setattr(
        reconciliation_module,
        "reconcile_non_terminal_runs",
        _fake_reconcile,
    )
    db_path = tmp_path / "g14-app.db"
    _upgrade_to_head(db_path)
    monkeypatch.setenv(
        "POLYNEXUS_DATABASE_URL",
        f"sqlite:///{db_path}",
    )

    with TestClient(app_module.create_app()) as client:
        assert client.get("/api/v1/health").status_code == 200

    assert len(calls) == 1
    os.environ.pop("POLYNEXUS_DATABASE_URL", None)
