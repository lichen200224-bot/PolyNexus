"""WP-12 — Council, Cross Review, Synthesis, and Partial Failure contract tests.

Additive contract tests over existing Task/Run/RunEvent/Evidence boundaries.
No product source beyond the new council/ orchestration package is exercised.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from d1a_fixtures import d1a_content_environment,prepare_generation,migrate_fixture_engine
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from polynexus_core.domain.enums import EvidenceType, RunState, WorkMode
from polynexus_core.domain.models import ContextPackage, Project, Run, Task
from polynexus_core.domain.runtime_binding import RuntimeBindingError
from polynexus_core.execution_service import ExecutionService
from polynexus_core.persistence.models import Base
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlRunEventRepository,
    SqlRuntimeBindingSnapshotRepository,
    SqlTaskRepository,
)
from polynexus_core.council.models import CouncilSpec, CouncilStage, ParticipantOutcome
from polynexus_core.council.orchestrator import (
    CouncilOrchestrator,
    _PLAN_SOURCE,
    _REASON_PARTICIPANT_FAILED,
    _REASON_UNVERIFIED_CLEANUP,
)
from polynexus_core.runtime.contracts import RuntimeStatus
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.registry import RuntimeRegistry, build_reference_profile

_FORBIDDEN_SECRET_FRAGMENTS = ("SECRET_MARKER", "sk-", "token=", "Bearer ")


@pytest.fixture()
def council_session(tmp_path: Path):
    db_path = tmp_path / "wp12.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    migrate_fixture_engine(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = Session()
    yield session, db_path
    session.close()
    engine.dispose()


def _seed(session) -> tuple[Task, ContextPackage]:
    project = Project(name="WP-12 Project")
    SqlProjectRepository(session).add(project)
    context = ContextPackage(project_id=project.id, version=1)
    SqlContextPackageRepository(session).add(context)
    task = Task(
        project_id=project.id,
        title="Council task",
        workflow_id="review-minimal",
        workflow_version=1,
        mode=WorkMode.REVIEW,
        context_package_id=context.id,
    )
    SqlTaskRepository(session).add(task)
    session.commit()
    prepare_generation(session,task.id)
    return task, context


def _specs(ids_roles: list[tuple[str, str]], outcomes: dict[str, ParticipantOutcome] | None = None):
    outcomes = outcomes or {}
    return [
        CouncilSpec(id=pid, role=role, expected_outcome=outcomes.get(pid))
        for pid, role in ids_roles
    ]


def _run(session, task, context, specs, **kwargs):
    orch = CouncilOrchestrator(session, **kwargs)
    return asyncio.run(orch.run_council(task, context, specs, generation_revision=1))


class _ConcurrencyTracker:
    """Records max concurrently executing analysis coroutines (test-side)."""

    def __init__(self) -> None:
        self.current = 0
        self.max = 0

    def enter(self) -> None:
        self.current += 1
        if self.current > self.max:
            self.max = self.current

    def exit(self) -> None:
        self.current -= 1


class _ConcurrencyProbeAdapter(ReferenceRuntimeAdapter):
    """Reference adapter that yields during execution to expose real overlap.

    The injected ``asyncio.sleep`` creates a genuine await point so that, under
    the orchestrator's bounded parallel scheduling, two participants' analysis
    executions are concurrently in flight. This lets the contract test prove
    actual overlap rather than merely sequential scheduling.
    """

    def __init__(self, tracker: _ConcurrencyTracker) -> None:
        super().__init__()
        self._tracker = tracker

    async def result(self, runtime_ref: str):
        self._tracker.enter()
        try:
            await asyncio.sleep(0.05)
            return await super().result(runtime_ref)
        finally:
            self._tracker.exit()


class _SlowTimeoutAdapter(ReferenceRuntimeAdapter):
    """Adapter whose execution always exceeds any reasonable council timeout."""

    async def result(self, runtime_ref: str):
        await asyncio.sleep(5)
        return await super().result(runtime_ref)


class _CancellationProbeAdapter(_SlowTimeoutAdapter):
    def __init__(self, started: asyncio.Event) -> None:
        super().__init__()
        self._started = started

    async def result(self, runtime_ref: str):
        self._started.set()
        return await super().result(runtime_ref)


class _ParentInterruptionAdapter(ReferenceRuntimeAdapter):
    """Normal child runtime, with a controllable parent boundary."""

    def __init__(self, mode: str, parent_started: asyncio.Event | None = None) -> None:
        super().__init__()
        self._mode = mode
        self._parent_started = parent_started
        self._status_calls = 0

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        self._status_calls += 1
        if self._status_calls >= 6:
            if self._parent_started is not None:
                self._parent_started.set()
            if self._mode == "failed":
                return RuntimeStatus(state=RunState.FAILED)
        return await super().status(runtime_ref)

    async def result(self, runtime_ref: str):
        if self._status_calls >= 6 and self._mode in {"timeout", "cancel"}:
            await asyncio.sleep(5)
        return await super().result(runtime_ref)


class _FailingOnceAdapter(ReferenceRuntimeAdapter):
    """Adapter that raises on FIRST submit after allocating a real reference handle.

    Used to prove runtime-failure isolation: exactly one participant fails with a
    sanitized outcome while the others continue, and no raw secret leaks.
    """

    def __init__(self) -> None:
        super().__init__()
        self._calls = 0

    async def submit(self, runtime_ref, task):
        self._calls += 1
        if self._calls == 1:
            raise RuntimeError("SECRET_MARKER_CRITICAL_LEAK_xyz123")
        return await super().submit(runtime_ref, task)


class _CountingAdapter(ReferenceRuntimeAdapter):
    """Reference adapter used to prove that invalid synthesis is not invoked."""

    def __init__(self) -> None:
        super().__init__()
        self.create_calls = 0

    async def create_run(self, context):
        self.create_calls += 1
        return await super().create_run(context)


# ---------------------------------------------------------------------------
# 1-4: bounds and identity
# ---------------------------------------------------------------------------


def test_two_participants_accepted(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    assert len(plan.participants) == 2
    assert plan.synthesis_run_id is not None
    assert all(p.outcome is ParticipantOutcome.COMPLETED for p in plan.participants)


def test_four_participants_accepted(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(
        session, task, context,
        _specs([("p1", "a"), ("p2", "b"), ("p3", "c"), ("p4", "d")]),
    )
    assert len(plan.participants) == 4


def test_fewer_than_two_rejected(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    with pytest.raises(ValueError):
        _run(session, task, context, _specs([("p1", "only")]))


def test_more_than_four_rejected(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    with pytest.raises(ValueError):
        _run(
            session, task, context,
            _specs([("p1", "a"), ("p2", "b"), ("p3", "c"), ("p4", "d"), ("p5", "e")]),
        )


def test_duplicate_participant_identity_rejected(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    with pytest.raises(ValueError):
        _run(session, task, context, _specs([("p1", "a"), ("p1", "b")]))


# ---------------------------------------------------------------------------
# 5-6: independent analysis
# ---------------------------------------------------------------------------


def test_independent_analysis_attributable_output(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    for p in plan.participants:
        assert p.outcome is ParticipantOutcome.COMPLETED
        assert p.analysis_run_id is not None
        evidences = SqlEvidenceRepository(session).list_by_run(p.analysis_run_id)
        assert any(e.type is EvidenceType.RUNTIME_EVIDENCE for e in evidences)


def test_analysis_does_not_consume_another_output(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    run_ids = [p.analysis_run_id for p in plan.participants]
    assert len(set(run_ids)) == 2


# ---------------------------------------------------------------------------
# 7-10: cross review + synthesis ordering
# ---------------------------------------------------------------------------


def test_cross_review_runs_after_analysis(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    order = [s.value for s in plan.stages_completed]
    assert order.index("ANALYSIS") < order.index("CROSS_REVIEW")


def test_cross_review_preserves_reviewer_and_target(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    for p in plan.participants:
        assert p.cross_review_run_ids
        for rid in p.cross_review_run_ids:
            ev = [e for e in SqlEvidenceRepository(session).list_by_run(rid)
                  if e.source == "council-cross-review"]
            assert ev
            assert ev[0].metadata["target_participant_id"] != p.id
            assert ev[0].metadata["reviewer_id"] == p.id
            assert ev[0].metadata["round"] == p.round
            assert ev[0].metadata["analysis_run_id"] is not None


def test_cross_reviewer_is_not_target(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    for p in plan.participants:
        for rid in p.cross_review_run_ids:
            evs = [e for e in SqlEvidenceRepository(session).list_by_run(rid)
                   if e.source == "council-cross-review"]
            for ev in evs:
                assert ev.metadata["reviewer_id"] != ev.metadata["target_participant_id"]


def test_synthesis_runs_after_cross_review(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    order = [s.value for s in plan.stages_completed]
    assert order.index("CROSS_REVIEW") < order.index("SYNTHESIS")


def test_synthesis_references_actual_outputs(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    ev = [e for e in SqlEvidenceRepository(session).list_by_run(plan.synthesis_run_id)
          if e.source == "council-synthesis"][0]
    analysis_ids = str(ev.metadata["analysis_run_ids"])
    cross_ids = str(ev.metadata["cross_review_run_ids"])
    assert plan.participants[0].analysis_run_id in analysis_ids
    assert plan.participants[0].cross_review_run_ids[0] in cross_ids


def test_synthesis_references_actual_evidence(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    ev = [e for e in SqlEvidenceRepository(session).list_by_run(plan.synthesis_run_id)
          if e.source == "council-synthesis"][0]
    import json
    analysis_refs = json.loads(ev.metadata["analysis_output_refs"])
    cross_refs = json.loads(ev.metadata["cross_review_output_refs"])
    assert len(analysis_refs) == 2
    assert len(cross_refs) > 0
    for ref in analysis_refs:
        assert ref["participant_id"] is not None
        assert ref["run_id"] is not None
        assert ref["evidence_ids"] is not None
        run = SqlRunRepository(session).get(ref["run_id"])
        assert run is not None


def test_synthesis_has_round_and_participant_correlation(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    ev = [e for e in SqlEvidenceRepository(session).list_by_run(plan.synthesis_run_id)
          if e.source == "council-synthesis"][0]
    assert ev.metadata["round"] == 1
    assert ev.metadata["verdict_authority"] == "none"


# ---------------------------------------------------------------------------
# 11-14: partial / failure / timeout / cancel / all-fail
# ---------------------------------------------------------------------------


def test_one_participant_failure_partial_truthful(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    adapter = _CountingAdapter()
    plan = _run(
        session, task, context,
        _specs([("p1", "analyst-a"), ("p2", "analyst-b")], {"p2": ParticipantOutcome.FAILED}),
        runtime_adapter=adapter,
    )
    failed = [p for p in plan.participants if p.id == "p2"][0]
    assert failed.outcome is ParticipantOutcome.FAILED
    assert failed.reason == "Participant analysis failed (simulated boundary)"
    assert plan.partial is True
    assert plan.synthesis_run_id is not None
    # One completed analysis has no distinct reviewer/target pair.  The
    # cross-review stage therefore remains incomplete and synthesis must not
    # invoke a runtime or fabricate a consensus from missing inputs.
    assert CouncilStage.CROSS_REVIEW not in plan.stages_completed
    assert plan.consensus_ref is None
    synthesis_run = SqlRunRepository(session).get(plan.synthesis_run_id)
    assert synthesis_run is not None
    assert synthesis_run.state is RunState.FAILED
    assert adapter.create_calls == 1, "synthesis must not invoke the runtime"
    assert not [
        e for e in SqlEvidenceRepository(session).list_by_run(plan.synthesis_run_id)
        if e.source == "council-synthesis"
    ]


def test_timeout_and_cancel_partial_no_fabrication(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(
        session, task, context,
        _specs(
            [("p1", "analyst-a"), ("p2", "analyst-b"), ("p3", "analyst-c")],
            {"p2": ParticipantOutcome.TIMED_OUT, "p3": ParticipantOutcome.CANCELLED},
        ),
    )
    outcomes = {p.id: p.outcome for p in plan.participants}
    assert outcomes["p2"] is ParticipantOutcome.TIMED_OUT
    assert outcomes["p3"] is ParticipantOutcome.CANCELLED
    assert plan.partial is True
    assert outcomes["p2"] is not ParticipantOutcome.COMPLETED


def test_all_participants_fail_no_fabricated_consensus(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(
        session, task, context,
        _specs([("p1", "analyst-a"), ("p2", "analyst-b")],
               {"p1": ParticipantOutcome.FAILED, "p2": ParticipantOutcome.FAILED}),
    )
    synth_run = SqlRunRepository(session).get(plan.synthesis_run_id)
    assert synth_run.state is RunState.FAILED
    assert plan.consensus_ref is None
    assert plan.partial is True


def test_missing_stage_input_deterministic_failure(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(
        session, task, context,
        _specs([("p1", "analyst-a"), ("p2", "analyst-b")],
               {"p1": ParticipantOutcome.UNAVAILABLE, "p2": ParticipantOutcome.UNAVAILABLE}),
    )
    synth_run = SqlRunRepository(session).get(plan.synthesis_run_id)
    assert synth_run.state is RunState.FAILED
    assert plan.consensus_ref is None
    for p in plan.participants:
        assert p.outcome is ParticipantOutcome.UNAVAILABLE


# ---------------------------------------------------------------------------
# 15: stage/participant events ordering + ownership
# ---------------------------------------------------------------------------


def test_stage_events_ordered_and_owned(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    events = SqlRunEventRepository(session).list_by_run(plan.council_run_id)
    stages = [e.reason for e in events]
    assert "ANALYSIS" in stages[0]
    for e in events:
        assert e.run_id == plan.council_run_id
    for p in plan.participants:
        if p.analysis_run_id:
            run = SqlRunRepository(session).get(p.analysis_run_id)
            assert run.task_id == task.id


# ---------------------------------------------------------------------------
# 16: close/reopen reload (child run state + terminal event)
# ---------------------------------------------------------------------------


def test_close_reopen_reload(council_session, tmp_path) -> None:
    session, db_path = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    council_run_id = plan.council_run_id
    session.close()

    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    orch = CouncilOrchestrator(session2)
    reloaded = asyncio.run(orch.reload_council(council_run_id))
    session2.close()
    engine.dispose()

    assert reloaded.council_run_id == council_run_id
    assert reloaded.synthesis_run_id == plan.synthesis_run_id
    assert len(reloaded.participants) == 2
    assert all(p.outcome is ParticipantOutcome.COMPLETED for p in reloaded.participants)
    assert "SYNTHESIS" in [s.value for s in reloaded.stages_completed]


def test_every_council_run_has_immutable_runtime_binding(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))

    run_ids = [plan.council_run_id, plan.synthesis_run_id]
    run_ids.extend(p.analysis_run_id for p in plan.participants)
    run_ids.extend(rid for p in plan.participants for rid in p.cross_review_run_ids)
    assert all(run_id is not None for run_id in run_ids)

    bindings = SqlRuntimeBindingSnapshotRepository(session)
    for run_id in run_ids:
        snapshot = bindings.get_by_run(run_id)
        assert snapshot is not None
        assert snapshot.run_id == run_id
        assert snapshot.runtime_profile_ref == "reference.local"
        assert snapshot.legacy_backfill is False
        run = SqlRunRepository(session).get(run_id)
        assert run is not None
        assert run.runtime_ref is not None
        assert any(
            evidence.type is EvidenceType.RUNTIME_EVIDENCE
            for evidence in SqlEvidenceRepository(session).list_by_run(run_id)
        )

    assert len({snapshot.run_id for snapshot in (bindings.get_by_run(rid) for rid in run_ids)}) == len(run_ids)


def test_council_factory_failure_after_binding_is_orphaned(
    council_session,
) -> None:
    session, _ = council_session
    task, context = _seed(session)
    registry = RuntimeRegistry()
    factory_calls = 0

    def factory():
        nonlocal factory_calls
        factory_calls += 1
        # Two analysis + two cross-review + one synthesis succeed; parent
        # construction then fails after its immutable binding is committed.
        if factory_calls == 6:
            raise RuntimeError("raw factory secret should not persist")
        return ReferenceRuntimeAdapter()

    registry.register(build_reference_profile(), factory)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    orchestrator = CouncilOrchestrator(session, runtime_registry=registry)

    with pytest.raises(RuntimeBindingError, match="Runtime adapter construction failed"):
        asyncio.run(orchestrator.run_council(task, context, specs, generation_revision=1))

    runs = SqlRunRepository(session).list_by_task(task.id)
    parent = next(
        run
        for run in runs
        if any(
            evidence.source == _PLAN_SOURCE
            for evidence in SqlEvidenceRepository(session).list_by_run(run.id)
        )
    )
    assert parent.state is RunState.ORPHANED
    assert [event.to_state for event in parent.events[-2:]] == [
        RunState.CANCEL_REQUESTED,
        RunState.ORPHANED,
    ]
    assert all(
        "raw factory secret" not in (event.reason or "")
        for run in runs
        for event in run.events
    )


def test_child_binding_failure_rolls_back_unbound_run(council_session, monkeypatch) -> None:
    session, _ = council_session
    task, context = _seed(session)
    workflow = CouncilOrchestrator(session)._load_workflow(task)
    run = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
     generation_revision=1)
    run_repo = SqlRunRepository(session)
    run_repo.add(run)
    session.flush()

    service = ExecutionService(session)

    def fail_binding(_snapshot) -> None:
        raise RuntimeError("binding insertion failed")

    monkeypatch.setattr(service._binding_repo, "insert_once", fail_binding)
    with pytest.raises(RuntimeError, match="binding insertion failed"):
        service.prepare_claimed_run(
            run, task, context, workflow, commit=False
        )

    # The child identity, claim event, and snapshot share one transaction. A
    # binding failure therefore leaves no durable unbound Run behind.
    assert run_repo.get(run.id) is None
    assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) is None


def test_council_child_policy_denial_commit_false_is_durable(
    council_session,
) -> None:
    """A denied Council child keeps only its CREATED identity and policy audit."""
    from dataclasses import replace

    from polynexus_core.domain.enums import TransportKind
    from polynexus_core.domain.generation import GenerationConflict, WorkGenerationRef
    from polynexus_core.persistence.generation import GenerationRepository

    session, db_path = council_session
    task, context = _seed(session)
    workflow = CouncilOrchestrator(session)._load_workflow(task)
    factory_calls: list[str] = []
    method_calls: list[str] = []

    class ForbiddenAdapter(ReferenceRuntimeAdapter):
        async def create_run(self, runtime_context):
            method_calls.append("create_run")
            return await super().create_run(runtime_context)

    def factory():
        factory_calls.append("factory")
        return ForbiddenAdapter()

    profile = replace(
        build_reference_profile(),
        transport_kind=TransportKind.OFFICIAL_API,
        runtime_profile_ref="reference.external",
    )
    registry = RuntimeRegistry()
    registry.register(profile, factory)
    registry._resolve_selected_profile = lambda: profile

    run = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
        generation_revision=1,
    )
    SqlRunRepository(session).add(run)
    session.flush()

    with pytest.raises(GenerationConflict, match="^predispatch_policy_denied$"):
        ExecutionService(session, registry=registry).prepare_claimed_run(
            run, task, context, workflow, commit=False
        )

    reopened_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    ReopenedSession = sessionmaker(
        bind=reopened_engine, expire_on_commit=False, future=True
    )
    try:
        with ReopenedSession() as reopened:
            stored = SqlRunRepository(reopened).get(run.id)
            assert stored is not None
            assert stored.state is RunState.CREATED
            assert stored.runtime_ref is None
            assert SqlRuntimeBindingSnapshotRepository(reopened).get_by_run(run.id) is None
            observation = GenerationRepository(reopened).observe(
                WorkGenerationRef(task.id, 1)
            )
            assert observation["writer"] is None
            audits = [
                evidence
                for evidence in SqlEvidenceRepository(reopened).list_by_run(run.id)
                if evidence.source == "runtime.routing_policy"
            ]
            assert len(audits) == 1
            assert audits[0].status.value == "FAIL"
            assert audits[0].metadata["decision"] == "DENY"
            assert audits[0].metadata["route"] == "MANUAL"
            assert audits[0].metadata["tool_trust"] == "TRUSTED_REGISTERED"
            assert audits[0].metadata["side_effect"] == "True"
            assert all(
                fragment not in str(audits[0].metadata)
                for fragment in _FORBIDDEN_SECRET_FRAGMENTS
            )
    finally:
        reopened_engine.dispose()

    assert factory_calls == []
    assert method_calls == []


def test_profile_resolution_failure_rolls_back_flushed_run(
    council_session, monkeypatch
) -> None:
    session, _ = council_session
    task, context = _seed(session)
    workflow = CouncilOrchestrator(session)._load_workflow(task)
    run = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
     generation_revision=1)
    run_repo = SqlRunRepository(session)
    run_repo.add(run)
    session.flush()
    service = ExecutionService(session)

    def fail_profile(_profile_ref: str):
        raise RuntimeError("profile resolution failed")

    monkeypatch.setattr(service._registry, "resolve", fail_profile)
    with pytest.raises(RuntimeError, match="profile resolution failed"):
        service.prepare_claimed_run(run, task, context, workflow, commit=False)

    assert run_repo.get(run.id) is None
    assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) is None


def test_council_profile_resolution_failure_leaves_no_parent_run(
    council_session, monkeypatch
) -> None:
    session, _ = council_session
    task, context = _seed(session)
    orchestrator = CouncilOrchestrator(session)

    def fail_profile(_profile_ref: str):
        raise RuntimeError("profile resolution failed")

    monkeypatch.setattr(orchestrator._registry, "resolve", fail_profile)
    with pytest.raises(RuntimeError, match="profile resolution failed"):
        asyncio.run(
            orchestrator.run_council(
                task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
            , generation_revision=1)
        )

    assert SqlRunRepository(session).list_by_task(task.id) == []


def test_council_stage_profile_resolution_failure_leaves_no_stage_run(
    council_session, monkeypatch
) -> None:
    session, _ = council_session
    task, context = _seed(session)
    orchestrator = CouncilOrchestrator(session)
    parent = orchestrator._create_council_run(task, context, generation_revision=1)
    parent, _ = orchestrator._execution_service.prepare_claimed_run(
        parent, task, context, orchestrator._load_workflow(task)
    )
    monkeypatch.setattr(
        orchestrator._registry,
        "resolve",
        lambda _profile_ref: (_ for _ in ()).throw(
            RuntimeError("profile resolution failed")
        ),
    )
    stage = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
     generation_revision=1)

    with pytest.raises(RuntimeError, match="profile resolution failed"):
        orchestrator._prepare_council_stage_run(stage, parent)

    assert SqlRunRepository(session).get(stage.id) is None
    assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(stage.id) is None
    assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(parent.id) is not None


def test_child_run_terminal_state_reloadable(council_session, tmp_path) -> None:
    session, db_path = council_session
    task, context = _seed(session)
    plan = _run(
        session, task, context,
        _specs([("p1", "analyst-a"), ("p2", "analyst-b")], {"p2": ParticipantOutcome.FAILED}),
    )
    failed_participant = [p for p in plan.participants if p.id == "p2"][0]
    child_run_id = failed_participant.analysis_run_id
    session.close()

    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    child_run = SqlRunRepository(session2).get(child_run_id)
    assert child_run is not None
    assert child_run.state is RunState.FAILED
    assert child_run.task_id == task.id
    terminal_events = [e for e in child_run.events if e.to_state == RunState.FAILED]
    assert len(terminal_events) >= 1
    assert terminal_events[-1].reason == "Participant analysis failed (simulated boundary)"
    session2.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 17: idempotent re-run does not duplicate
# ---------------------------------------------------------------------------


def test_repeated_execution_no_duplicate(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    plan1 = _run(session, task, context, specs)
    run_count_before = len(SqlRunRepository(session).list_by_task(task.id))

    orch = CouncilOrchestrator(session)
    plan2 = asyncio.run(orch.rerun_council(plan1.council_run_id, task, context, specs))
    run_count_after = len(SqlRunRepository(session).list_by_task(task.id))

    assert plan2.council_run_id == plan1.council_run_id
    assert run_count_after == run_count_before
    assert plan2.synthesis_run_id == plan1.synthesis_run_id


def test_run_council_idempotent_on_same_task(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    plan1 = _run(session, task, context, specs)
    run_count_before = len(SqlRunRepository(session).list_by_task(task.id))

    plan2 = _run(session, task, context, specs)
    run_count_after = len(SqlRunRepository(session).list_by_task(task.id))

    assert plan2.council_run_id == plan1.council_run_id
    assert run_count_after == run_count_before
    assert plan2.synthesis_run_id == plan1.synthesis_run_id


# ---------------------------------------------------------------------------
# 18-19: no secret leakage, reference adapter no network
# ---------------------------------------------------------------------------


def test_no_secret_in_results_or_events(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(
        session, task, context,
        _specs([("p1", "analyst-a"), ("p2", "analyst-b")], {"p2": ParticipantOutcome.FAILED}),
    )
    blobs = []
    if plan.consensus_ref:
        ev = [e for e in SqlEvidenceRepository(session).list_by_run(plan.synthesis_run_id)
              if e.id == plan.consensus_ref][0]
        blobs.append(ev.metadata.get("summary", ""))
    for p in plan.participants:
        if p.reason:
            blobs.append(p.reason)
    events = SqlRunEventRepository(session).list_by_run(plan.council_run_id)
    blobs.extend(e.reason for e in events if e.reason is not None)
    text = " ".join(blobs).lower()
    for frag in _FORBIDDEN_SECRET_FRAGMENTS:
        assert frag.lower() not in text


def test_reference_adapter_has_no_network(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    plan = _run(session, task, context, _specs([("p1", "analyst-a"), ("p2", "analyst-b")]))
    for p in plan.participants:
        if p.analysis_run_id:
            run = SqlRunRepository(session).get(p.analysis_run_id)
            assert run.runtime_ref.startswith("reference:")


# ---------------------------------------------------------------------------
# 20: existing WP-09B lifecycle unaffected (regression)
# ---------------------------------------------------------------------------


def test_existing_run_lifecycle_unaffected(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    from polynexus_core.domain.models import Run

    run = Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=context.id,
     generation_revision=1)
    SqlRunRepository(session).add(run)
    session.commit()

    service = ExecutionService(session)
    execution = asyncio.run(service.execute_existing_run(run.id))
    assert execution.run.state is RunState.COMPLETED
    assert execution.evidence


# ---------------------------------------------------------------------------
# 21: ownership validation
# ---------------------------------------------------------------------------


def test_council_rejects_cross_project_ownership(council_session) -> None:
    session, _ = council_session
    project1 = Project(name="Project A")
    project2 = Project(name="Project B")
    SqlProjectRepository(session).add(project1)
    SqlProjectRepository(session).add(project2)
    context = ContextPackage(project_id=project1.id, version=1)
    SqlContextPackageRepository(session).add(context)
    task = Task(
        project_id=project2.id,
        title="Cross-project task",
        workflow_id="review-minimal",
        workflow_version=1,
        mode=WorkMode.REVIEW,
        context_package_id=context.id,
    )
    SqlTaskRepository(session).add(task)
    session.commit()

    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    with pytest.raises(ValueError, match="different projects"):
        _run(session, task, context, specs)


def test_council_rejects_mismatched_context_package(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    other_context = ContextPackage(project_id=task.project_id, version=2)
    SqlContextPackageRepository(session).add(other_context)
    session.commit()
    task.context_package_id = "nonexistent"
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    with pytest.raises(ValueError, match="does not match"):
        _run(session, task, other_context, specs)


# ---------------------------------------------------------------------------
# 22: bounded round limit
# ---------------------------------------------------------------------------


def test_max_rounds_enforced(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    orch = CouncilOrchestrator(session, max_rounds=0)
    with pytest.raises(ValueError, match="round"):
        asyncio.run(orch.run_council(task, context, specs, round=1, generation_revision=1))


# ---------------------------------------------------------------------------
# 23: timeout framework (reference adapter completes instantly)
# ---------------------------------------------------------------------------


def test_timeout_framework_with_reference_adapter(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    plan = _run(session, task, context, specs, timeout_seconds=60.0)
    assert plan.synthesis_run_id is not None
    assert all(p.outcome is ParticipantOutcome.COMPLETED for p in plan.participants)


# ---------------------------------------------------------------------------
# 24: independent analysis is genuinely bounded-parallel (overlap proven)
# ---------------------------------------------------------------------------


def test_analysis_runs_in_bounded_parallel(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    tracker = _ConcurrencyTracker()
    adapter = _ConcurrencyProbeAdapter(tracker)
    max_concurrency = 2
    specs = _specs([
        ("p1", "analyst-a"), ("p2", "analyst-b"),
        ("p3", "analyst-c"), ("p4", "analyst-d"),
    ])
    orch = CouncilOrchestrator(
        session, runtime_adapter=adapter, max_concurrency=max_concurrency
    )
    plan = asyncio.run(orch.run_council(task, context, specs, generation_revision=1))

    # Genuine overlap: at least two participant analyses were concurrently in flight.
    assert tracker.max >= 2, "expected concurrent analysis execution overlap"
    # Bounded: the semaphore must cap concurrency at max_concurrency.
    assert tracker.max <= max_concurrency
    # Orchestrator-observed concurrency is also recorded on the plan.
    assert plan.max_concurrency_observed >= 2
    assert plan.synthesis_run_id is not None
    assert all(p.outcome is ParticipantOutcome.COMPLETED for p in plan.participants)


# ---------------------------------------------------------------------------
# 25: run_council is idempotent for a FAILED/partial council (no new Runs)
# ---------------------------------------------------------------------------


def test_run_council_idempotent_on_failed_council(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    specs = _specs(
        [("p1", "analyst-a"), ("p2", "analyst-b")],
        {"p2": ParticipantOutcome.FAILED},
    )
    plan1 = _run(session, task, context, specs)
    # First council reaches a FAILED terminal state (partial outcome).
    council_run = SqlRunRepository(session).get(plan1.council_run_id)
    assert council_run.state is RunState.FAILED
    run_count_before = len(SqlRunRepository(session).list_by_task(task.id))
    analysis_ids_before = {p.analysis_run_id for p in plan1.participants}

    # Repeat the SAME request: must not unconditionally create new Council/participant Runs.
    plan2 = _run(session, task, context, specs)
    run_count_after = len(SqlRunRepository(session).list_by_task(task.id))

    assert plan2.council_run_id == plan1.council_run_id
    assert run_count_after == run_count_before
    assert {p.analysis_run_id for p in plan2.participants} == analysis_ids_before
    # Outcome is stable (still failed), not silently re-attempted/fixed.
    assert any(p.outcome is ParticipantOutcome.FAILED for p in plan2.participants)


# ---------------------------------------------------------------------------
# 26: round propagates to CouncilPlan, participants, persisted plan, and
#     idempotency (close/reopen preserves round; repeat adds no Runs)
# ---------------------------------------------------------------------------


def test_round_two_plan_persists_and_is_idempotent(council_session, tmp_path) -> None:
    session, db_path = council_session
    task, context = _seed(session)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])

    plan = asyncio.run(
        CouncilOrchestrator(session).run_council(task, context, specs, round=2, generation_revision=1)
    )
    assert plan.round == 2
    assert all(p.round == 2 for p in plan.participants)

    # Close and reopen: persisted plan must preserve the round.
    session.close()
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session2 = Session()
    reloaded = asyncio.run(
        CouncilOrchestrator(session2).reload_council(plan.council_run_id)
    )
    assert reloaded.round == 2
    assert all(p.round == 2 for p in reloaded.participants)

    # Repeat run_council with identical inputs: same council, no new Runs.
    run_count_before = len(SqlRunRepository(session2).list_by_task(task.id))
    plan2 = asyncio.run(
        CouncilOrchestrator(session2).run_council(task, context, specs, round=2, generation_revision=1)
    )
    run_count_after = len(SqlRunRepository(session2).list_by_task(task.id))

    assert plan2.council_run_id == plan.council_run_id
    assert run_count_after == run_count_before
    session2.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# 27: same task/context/round but different specs -> deterministic reject
# ---------------------------------------------------------------------------


def test_different_specs_same_task_context_round_rejected(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    specs_a = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    asyncio.run(CouncilOrchestrator(session).run_council(task, context, specs_a, round=1, generation_revision=1))

    # Conflicting request: same task/context/round, different participant specs.
    specs_b = _specs([("p1", "analyst-a"), ("p3", "analyst-c")])
    with pytest.raises(ValueError, match="different participant specs"):
        asyncio.run(
            CouncilOrchestrator(session).run_council(task, context, specs_b, round=1, generation_revision=1)
        )


# ---------------------------------------------------------------------------
# 28: participant timeout isolation — legal lifecycle, reloadable, no dup STARTING
# ---------------------------------------------------------------------------


def test_participant_timeout_isolated_and_reloadable(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    adapter = _SlowTimeoutAdapter()
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    plan = asyncio.run(
        CouncilOrchestrator(session, runtime_adapter=adapter, timeout_seconds=0.1).run_council(
            task, context, specs
        , generation_revision=1)
    )
    # Council timeout intent remains TIMED_OUT; ADR-014 Supervisor cancellation
    # now verifies Reference cleanup and durably records CANCELLED.
    assert all(p.outcome is ParticipantOutcome.TIMED_OUT for p in plan.participants)
    for p in plan.participants:
        run = SqlRunRepository(session).get(p.analysis_run_id)
        assert run is not None
        assert run.state is RunState.CANCELLED
        assert adapter.was_cleaned(run.runtime_ref)
        # Exactly one STARTING and one verified cancellation terminal event.
        starting = [e for e in run.events if e.to_state == RunState.STARTING]
        cancel_requested = [
            e for e in run.events if e.to_state == RunState.CANCEL_REQUESTED
        ]
        orphaned = [e for e in run.events if e.to_state == RunState.CANCELLED]
        assert len(starting) == 1
        assert len(cancel_requested) == 1
        assert len(orphaned) == 1
        assert run.events[-1].to_state is RunState.CANCELLED
        assert run.events[-1].reason == "Run cancelled"
    # Council still completes with a truthful (failed) synthesis; no consensus is
    # fabricated when synthesis cannot run (no completed analysis + cross-review).
    assert plan.synthesis_run_id is not None
    assert plan.partial is True
    assert plan.consensus_ref is None


# ---------------------------------------------------------------------------
# 29: outer Council cancellation fails closed for parent and bound children
# ---------------------------------------------------------------------------


def test_outer_cancellation_fail_closed_parent_and_children(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    started = asyncio.Event()
    adapter = _CancellationProbeAdapter(started)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    orchestrator = CouncilOrchestrator(
        session, runtime_adapter=adapter, timeout_seconds=30.0
    )

    async def cancel_after_binding() -> None:
        operation = asyncio.create_task(
            orchestrator.run_council(task, context, specs, generation_revision=1)
        )
        await asyncio.wait_for(started.wait(), timeout=1.0)
        operation.cancel()
        with pytest.raises(asyncio.CancelledError):
            await operation

    asyncio.run(cancel_after_binding())

    runs = SqlRunRepository(session).list_by_task(task.id)
    council_runs = [
        run
        for run in runs
        if any(
            evidence.source == _PLAN_SOURCE
            for evidence in SqlEvidenceRepository(session).list_by_run(run.id)
        )
    ]
    assert len(council_runs) == 1
    council_run = council_runs[0]
    child_runs = [run for run in runs if run.id != council_run.id]
    assert len(child_runs) == 2
    assert council_run.state is RunState.ORPHANED
    assert all(run.state is RunState.CANCELLED for run in child_runs)
    assert all(adapter.was_cleaned(run.runtime_ref) for run in child_runs)
    assert all(
        SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) is not None
        for run in [council_run, *child_runs]
    )
    assert all(
        run.events[-1].to_state not in (RunState.STARTING, RunState.CANCEL_REQUESTED)
        for run in [council_run, *child_runs]
    )
    assert all(
        run.events[-1].reason == "Run cancelled"
        for run in child_runs
    )

    reloaded = asyncio.run(
        CouncilOrchestrator(session).reload_council(council_run.id)
    )
    assert all(p.outcome is ParticipantOutcome.CANCELLED for p in reloaded.participants)


# ---------------------------------------------------------------------------
# 30: outer stage timeout fail-closes the already-bound parent Council Run
# ---------------------------------------------------------------------------


def test_outer_stage_timeout_fail_closed_parent(council_session, monkeypatch) -> None:
    session, _ = council_session
    task, context = _seed(session)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    orchestrator = CouncilOrchestrator(session, timeout_seconds=30.0)

    async def raise_outer_timeout(*args, **kwargs):
        raise asyncio.TimeoutError()

    monkeypatch.setattr(orchestrator, "_run_analysis_stage", raise_outer_timeout)
    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(orchestrator.run_council(task, context, specs, generation_revision=1))

    runs = SqlRunRepository(session).list_by_task(task.id)
    council_runs = [
        run
        for run in runs
        if any(
            evidence.source == _PLAN_SOURCE
            for evidence in SqlEvidenceRepository(session).list_by_run(run.id)
        )
    ]
    assert len(council_runs) == 1
    council_run = council_runs[0]
    assert council_run.state is RunState.ORPHANED
    assert (
        council_run.events[-1].reason
        == "Council execution cleanup could not be verified"
    )
    assert (
        SqlRuntimeBindingSnapshotRepository(session).get_by_run(council_run.id)
        is not None
    )


def test_parent_runtime_timeout_fails_closed_after_children_complete(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    adapter = _ParentInterruptionAdapter("timeout")
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])

    with pytest.raises(asyncio.TimeoutError):
        asyncio.run(
            CouncilOrchestrator(
                session, runtime_adapter=adapter, timeout_seconds=0.1
            ).run_council(task, context, specs, generation_revision=1)
        )

    runs = SqlRunRepository(session).list_by_task(task.id)
    parent = next(
        run
        for run in runs
        if any(
            evidence.source == _PLAN_SOURCE
            for evidence in SqlEvidenceRepository(session).list_by_run(run.id)
        )
    )
    assert parent.state is RunState.CANCELLED
    assert adapter.was_cleaned(parent.runtime_ref)
    assert all(
        run.events[-1].to_state not in (RunState.STARTING, RunState.CANCEL_REQUESTED)
        for run in runs
    )
    assert all(
        SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) is not None
        for run in runs
    )


def test_parent_runtime_cancellation_fails_closed_after_children_complete(
    council_session,
) -> None:
    session, _ = council_session
    task, context = _seed(session)
    parent_started = asyncio.Event()
    adapter = _ParentInterruptionAdapter("cancel", parent_started)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    orchestrator = CouncilOrchestrator(
        session, runtime_adapter=adapter, timeout_seconds=30.0
    )

    async def cancel_parent() -> None:
        operation = asyncio.create_task(orchestrator.run_council(task, context, specs, generation_revision=1))
        await asyncio.wait_for(parent_started.wait(), timeout=1.0)
        operation.cancel()
        with pytest.raises(asyncio.CancelledError):
            await operation

    asyncio.run(cancel_parent())

    runs = SqlRunRepository(session).list_by_task(task.id)
    parent = next(
        run
        for run in runs
        if any(
            evidence.source == _PLAN_SOURCE
            for evidence in SqlEvidenceRepository(session).list_by_run(run.id)
        )
    )
    assert parent.state is RunState.CANCELLED
    assert adapter.was_cleaned(parent.runtime_ref)
    assert all(
        run.events[-1].to_state not in (RunState.STARTING, RunState.CANCEL_REQUESTED)
        for run in runs
    )


def test_parent_noncompleted_runtime_clears_consensus_and_reloads_truthfully(
    council_session,
) -> None:
    session, _ = council_session
    task, context = _seed(session)
    adapter = _ParentInterruptionAdapter("failed")
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    orchestrator = CouncilOrchestrator(session, runtime_adapter=adapter)

    with pytest.raises(RuntimeError, match="parent runtime did not complete"):
        asyncio.run(orchestrator.run_council(task, context, specs, generation_revision=1))

    runs = SqlRunRepository(session).list_by_task(task.id)
    parent = next(
        run
        for run in runs
        if any(
            evidence.source == _PLAN_SOURCE
            for evidence in SqlEvidenceRepository(session).list_by_run(run.id)
        )
    )
    assert parent.state is RunState.FAILED
    reloaded = asyncio.run(CouncilOrchestrator(session).reload_council(parent.id))
    assert reloaded.partial is True
    assert reloaded.consensus_ref is None


def test_stage_setup_failure_reconciles_bound_stage_run_and_parent(
    council_session, monkeypatch
) -> None:
    session, _ = council_session
    task, context = _seed(session)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    orchestrator = CouncilOrchestrator(session, timeout_seconds=30.0)
    original_prepare = orchestrator._prepare_council_stage_run

    def fail_after_binding(run, council_run, bound_run_ids=None):
        original_prepare(run, council_run, bound_run_ids)
        raise RuntimeError("unexpected stage setup failure")

    monkeypatch.setattr(
        orchestrator, "_prepare_council_stage_run", fail_after_binding
    )
    with pytest.raises(RuntimeError, match="unexpected stage setup failure"):
        asyncio.run(orchestrator.run_council(task, context, specs, generation_revision=1))

    runs = list(SqlRunRepository(session).list_by_task(task.id))
    parent = next(
        run
        for run in runs
        if any(
            evidence.source == _PLAN_SOURCE
            for evidence in SqlEvidenceRepository(session).list_by_run(run.id)
        )
    )
    analysis_ids = {
        participant.analysis_run_id
        for participant in orchestrator._load_plan(parent.id).participants
        if participant.analysis_run_id is not None
    }
    stage_runs = [
        run for run in runs if run.id != parent.id and run.id not in analysis_ids
    ]
    assert len(stage_runs) == 1
    assert parent.state is RunState.ORPHANED
    assert stage_runs[0].state is RunState.ORPHANED
    assert all(
        run.events[-1].to_state not in (RunState.STARTING, RunState.CANCEL_REQUESTED)
        for run in runs
    )
    bindings = SqlRuntimeBindingSnapshotRepository(session)
    assert all(bindings.get_by_run(run.id) is not None for run in runs)

    reloaded = asyncio.run(
        CouncilOrchestrator(session).reload_council(parent.id)
    )
    assert reloaded.partial is True
    assert CouncilStage.CROSS_REVIEW not in reloaded.stages_completed


def test_unexpected_child_setup_cancels_and_reconciles_siblings(
    council_session, monkeypatch
) -> None:
    session, _ = council_session
    task, context = _seed(session)
    started = asyncio.Event()
    adapter = _CancellationProbeAdapter(started)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    orchestrator = CouncilOrchestrator(
        session, runtime_adapter=adapter, timeout_seconds=30.0
    )
    original_prepare = ExecutionService.prepare_claimed_run
    prepare_calls = 0

    def fail_second_child_setup(self, run, task_arg, context_arg, workflow, *, commit=True):
        nonlocal prepare_calls
        prepare_calls += 1
        if prepare_calls == 3:
            raise RuntimeError("unexpected child setup failure")
        return original_prepare(
            self, run, task_arg, context_arg, workflow, commit=commit
        )

    monkeypatch.setattr(
        ExecutionService, "prepare_claimed_run", fail_second_child_setup
    )
    with pytest.raises(RuntimeError, match="unexpected child setup failure"):
        asyncio.run(orchestrator.run_council(task, context, specs, generation_revision=1))

    assert started.is_set()
    runs = list(SqlRunRepository(session).list_by_task(task.id))
    assert len(runs) == 2
    parent = next(
        run
        for run in runs
        if any(
            evidence.source == _PLAN_SOURCE
            for evidence in SqlEvidenceRepository(session).list_by_run(run.id)
        )
    )
    child = next(run for run in runs if run.id != parent.id)
    assert parent.state is RunState.ORPHANED
    assert child.state is RunState.CANCELLED
    assert adapter.was_cleaned(child.runtime_ref)
    assert child.events[-1].reason == "Run cancelled"
    assert all(
        run.events[-1].to_state not in (RunState.STARTING, RunState.CANCEL_REQUESTED)
        for run in runs
    )
    assert all(
        SqlRuntimeBindingSnapshotRepository(session).get_by_run(run.id) is not None
        for run in runs
    )

    reloaded = asyncio.run(
        CouncilOrchestrator(session).reload_council(parent.id)
    )
    assert reloaded.partial is True
    assert all(
        participant.outcome is ParticipantOutcome.CANCELLED
        for participant in reloaded.participants
        if participant.analysis_run_id is not None
    )
    assert any(
        participant.analysis_run_id is None
        for participant in reloaded.participants
    )


# ---------------------------------------------------------------------------
# 31: participant runtime failure is sanitized; other participants continue
# ---------------------------------------------------------------------------


def test_participant_failure_sanitized_others_continue(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    adapter = _FailingOnceAdapter()
    # 3 participants: the first adapter call fails, the other two succeed.
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b"), ("p3", "analyst-c")])
    plan = asyncio.run(
        CouncilOrchestrator(session, runtime_adapter=adapter).run_council(task, context, specs, generation_revision=1)
    )
    # Council completed (did not crash) with a truthful partial result.
    assert plan.synthesis_run_id is not None
    failed = [p for p in plan.participants if p.outcome is ParticipantOutcome.FAILED]
    completed = [p for p in plan.participants if p.outcome is ParticipantOutcome.COMPLETED]
    assert len(failed) == 1
    assert len(completed) == 2
    assert adapter._runs and all(record.cleaned for record in adapter._runs.values())
    # Sanitized reason persisted; raw secret marker never appears.
    secret = "SECRET_MARKER_CRITICAL_LEAK_xyz123"
    assert failed[0].reason == _REASON_PARTICIPANT_FAILED
    assert secret not in failed[0].reason
    # No raw secret in any persisted Run event.
    for run in SqlRunRepository(session).list_by_task(task.id):
        for ev in run.events:
            assert secret not in (ev.reason or "")
    # No raw secret in the persisted CouncilPlan evidence.
    plan_blobs = [
        str(e.metadata)
        for e in SqlEvidenceRepository(session).list_by_run(plan.council_run_id)
        if e.source == _PLAN_SOURCE
    ]
    assert plan_blobs  # at least one persisted plan
    for blob in plan_blobs:
        assert secret not in blob


# ---------------------------------------------------------------------------
# 30: adapter boundary failures are contained truthfully (no COMPLETED mislabel,
#     no lifecycle break, no raw secret, no fabricated output)
# ---------------------------------------------------------------------------

_SECRET = "SECRET_MARKER_RAW_LEAK_abc123"


class _StatusStateAdapter(ReferenceRuntimeAdapter):
    """Adapter whose status() returns a forced terminal state with a raw secret."""

    def __init__(self, state: RunState, error: str = f"raw-{_SECRET}") -> None:
        super().__init__()
        self._forced_state = state
        self._forced_error = error

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        return RuntimeStatus(state=self._forced_state, error=self._forced_error)


class _RaisingAdapter(ReferenceRuntimeAdapter):
    """Adapter that raises a secret-bearing error at a specific boundary."""

    def __init__(self, boundary: str) -> None:
        super().__init__()
        self._boundary = boundary
        self._secret = f"raw-{_SECRET}"

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        if self._boundary == "status":
            raise RuntimeError(self._secret)
        return await super().status(runtime_ref)

    async def result(self, runtime_ref: str):
        if self._boundary == "result":
            raise RuntimeError(self._secret)
        return await super().result(runtime_ref)

    async def artifacts(self, runtime_ref: str) -> tuple:
        if self._boundary == "artifacts":
            raise RuntimeError(self._secret)
        return await super().artifacts(runtime_ref)

    def version_info(self) -> str:
        if self._boundary == "version_info":
            raise RuntimeError(self._secret)
        return super().version_info()


class _StatusErrorAdapter(ReferenceRuntimeAdapter):
    """Adapter whose status() returns a forced terminal state with a raw secret error."""

    def __init__(self, state: RunState, error: str = f"raw-status-error-{_SECRET}") -> None:
        super().__init__()
        self._forced_state = state
        self._forced_error = error

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        return RuntimeStatus(state=self._forced_state, error=self._forced_error)


class _StatusThenVersionInfoRaisesAdapter(ReferenceRuntimeAdapter):
    """Adapter that returns a terminal status, then raises a secret error in version_info()."""

    def __init__(self, state: RunState, error: str = f"raw-status-error-{_SECRET}") -> None:
        super().__init__()
        self._forced_state = state
        self._forced_error = error

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        return RuntimeStatus(state=self._forced_state, error=self._forced_error)

    def version_info(self) -> str:
        raise RuntimeError(f"raw-version-info-{_SECRET}")


def _reopen_session(db_path: Path):
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    return Session(), engine


def _assert_truthful_boundary_failure(
    session,
    task,
    plan,
    terminal_state: RunState,
) -> None:
    """Verify the full WP-12 containment contract for adapter boundary failures."""
    completed = [p for p in plan.participants if p.outcome is ParticipantOutcome.COMPLETED]
    failed = [p for p in plan.participants if p.outcome is not ParticipantOutcome.COMPLETED]
    assert failed, "expected at least one failed participant"

    # Failed participants: no output_ref, not COMPLETED, sanitized reason.
    for p in failed:
        assert p.outcome is not ParticipantOutcome.COMPLETED
        assert p.output_ref is None
        # Failed participant never enters cross review.
        assert list(p.cross_review_run_ids) == []

    # Cross review runs only belong to completed participants.
    completed_ids = {p.id for p in completed}
    for p in plan.participants:
        for rid in p.cross_review_run_ids:
            assert p.id in completed_ids

    # Each child Run: reloadable, consistent state/terminal event, terminal once,
    # no raw secret, and only the required routing-policy audit evidence.
    for p in plan.participants:
        assert p.analysis_run_id is not None
        child = SqlRunRepository(session).get(p.analysis_run_id)
        assert child is not None
        assert child.task_id == task.id
        assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(p.analysis_run_id) is not None
        # Failed participants must not persist a raw RuntimeResult (no status.error
        # in result.summary, no dangling finding/evidence/artifact references).
        assert child.result is None

        terminal_events = [e for e in child.events if e.to_state is terminal_state]
        assert child.state is terminal_state
        assert child.events[-1].to_state is terminal_state
        # Terminal event appears exactly once.
        assert len(terminal_events) == 1

        # No raw secret in any event reason.
        for ev in child.events:
            assert _SECRET not in (ev.reason or "")

        # Failed child Runs persist exactly one routing-policy audit and no other evidence.
        run_evidence = SqlEvidenceRepository(session).list_by_run(p.analysis_run_id)
        assert len(run_evidence) == 1
        assert run_evidence[0].source == "runtime.routing_policy"

    # Synthesis remains truthful: failed result (no consensus) when no completed
    # analysis, otherwise a truthful partial synthesis.
    synth_run = SqlRunRepository(session).get(plan.synthesis_run_id)
    assert synth_run is not None
    assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(plan.synthesis_run_id) is not None
    if not completed:
        assert synth_run.state is RunState.FAILED
        assert plan.consensus_ref is None
    assert plan.partial is True
    # No raw secret anywhere in child events already checked; plan also clean.
    plan_blobs = [
        str(e.metadata)
        for e in SqlEvidenceRepository(session).list_by_run(plan.council_run_id)
        if e.source == _PLAN_SOURCE
    ]
    for blob in plan_blobs:
        assert _SECRET not in blob


@pytest.mark.parametrize(
    "mode,terminal_state",
    [
        ("status_failed", RunState.FAILED),
        ("status_timed_out", RunState.TIMED_OUT),
        ("status_cancelled", RunState.CANCELLED),
        ("status_raise", RunState.FAILED),
        ("result_raise", RunState.FAILED),
        ("artifacts_raise", RunState.FAILED),
        ("version_info_raise", RunState.FAILED),
    ],
)
def test_adapter_boundary_failure_truthful_and_reloadable(
    mode, terminal_state, council_session, tmp_path
) -> None:
    session, db_path = council_session
    task, context = _seed(session)

    if mode == "status_failed":
        adapter = _StatusStateAdapter(RunState.FAILED)
    elif mode == "status_timed_out":
        adapter = _StatusStateAdapter(RunState.TIMED_OUT)
    elif mode == "status_cancelled":
        adapter = _StatusStateAdapter(RunState.CANCELLED)
    elif mode == "status_raise":
        adapter = _RaisingAdapter("status")
    elif mode == "result_raise":
        adapter = _RaisingAdapter("result")
    elif mode == "artifacts_raise":
        adapter = _RaisingAdapter("artifacts")
    elif mode == "version_info_raise":
        adapter = _RaisingAdapter("version_info")
    else:  # pragma: no cover
        raise AssertionError(f"unexpected mode: {mode}")

    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    plan = asyncio.run(
        CouncilOrchestrator(session, runtime_adapter=adapter).run_council(task, context, specs, generation_revision=1)
    )

    _assert_truthful_boundary_failure(session, task, plan, terminal_state)

    # Close / reopen: child Run and council plan reload with consistent state.
    session.close()
    session2, engine2 = _reopen_session(db_path)
    try:
        for p in plan.participants:
            child = SqlRunRepository(session2).get(p.analysis_run_id)
            assert child is not None
            assert child.state is terminal_state
            assert child.events[-1].to_state is terminal_state
        orch = CouncilOrchestrator(session2)
        reloaded = asyncio.run(orch.reload_council(plan.council_run_id))
        for p, orig in zip(reloaded.participants, plan.participants):
            assert p.outcome is orig.outcome
            assert p.output_ref is orig.output_ref
    finally:
        session2.close()
        engine2.dispose()
    # Truthful partial result: not a unanimous/fabricated verdict.
    assert plan.partial is True


# ---------------------------------------------------------------------------
# 31: raw status.error must not leak into persisted run.result
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", [RunState.FAILED, RunState.TIMED_OUT])
def test_status_error_not_persisted_in_result(state, council_session, tmp_path) -> None:
    session, db_path = council_session
    task, context = _seed(session)
    adapter = _StatusErrorAdapter(state)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    plan = asyncio.run(
        CouncilOrchestrator(session, runtime_adapter=adapter).run_council(task, context, specs, generation_revision=1)
    )

    for p in plan.participants:
        assert p.outcome is not ParticipantOutcome.COMPLETED
        assert p.output_ref is None
        child = SqlRunRepository(session).get(p.analysis_run_id)
        assert child is not None
        # run.result must be None: no raw RuntimeResult.summary / dangling refs.
        assert child.result is None
        # Only the required routing-policy audit is persisted for the failed Run.
        evidence = SqlEvidenceRepository(session).list_by_run(p.analysis_run_id)
        assert len(evidence) == 1
        assert evidence[0].source == "runtime.routing_policy"
        # No raw secret in any event reason.
        for ev in child.events:
            assert _SECRET not in (ev.reason or "")

    # Synthesis stays truthful (failed result when no completed analysis).
    synth = SqlRunRepository(session).get(plan.synthesis_run_id)
    assert synth is not None
    if plan.consensus_ref is None:
        assert synth.state is RunState.FAILED

    # Close / reopen: reload the persisted Run and confirm the secret is absent
    # from result_summary, event reasons, and evidence references.
    session.close()
    session2, engine2 = _reopen_session(db_path)
    try:
        for p in plan.participants:
            c2 = SqlRunRepository(session2).get(p.analysis_run_id)
            assert c2 is not None
            assert c2.state is state
            assert c2.result is None
            for ev in c2.events:
                assert _SECRET not in (ev.reason or "")
            evidence = SqlEvidenceRepository(session2).list_by_run(p.analysis_run_id)
            assert len(evidence) == 1
            assert evidence[0].source == "runtime.routing_policy"
    finally:
        session2.close()
        engine2.dispose()


# ---------------------------------------------------------------------------
# 32: a later boundary exception must not rewrite an already-terminal
#     TIMED_OUT/CANCELLED participant into FAILED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", [RunState.TIMED_OUT, RunState.CANCELLED])
def test_status_then_version_info_raises_keeps_terminal(
    state, council_session, tmp_path
) -> None:
    session, db_path = council_session
    task, context = _seed(session)
    adapter = _StatusThenVersionInfoRaisesAdapter(state)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    plan = asyncio.run(
        CouncilOrchestrator(session, runtime_adapter=adapter).run_council(task, context, specs, generation_revision=1)
    )

    expected_outcome = {
        RunState.TIMED_OUT: ParticipantOutcome.TIMED_OUT,
        RunState.CANCELLED: ParticipantOutcome.CANCELLED,
    }[state]

    for p in plan.participants:
        # Must remain the status-state outcome, NOT be rewritten to FAILED.
        assert p.outcome is expected_outcome
        assert p.output_ref is None
        child = SqlRunRepository(session).get(p.analysis_run_id)
        assert child is not None
        assert child.state is state
        assert child.events[-1].to_state is state
        # Exactly one terminal event of the expected state.
        assert len([e for e in child.events if e.to_state is state]) == 1
        # No raw secret in any event reason (terminal reason sanitized).
        for ev in child.events:
            assert _SECRET not in (ev.reason or "")
        # No raw RuntimeResult persisted.
        assert child.result is None

    # Persisted plan + close/reopen reload must be fully consistent.
    session.close()
    session2, engine2 = _reopen_session(db_path)
    try:
        reloaded = asyncio.run(
            CouncilOrchestrator(session2).reload_council(plan.council_run_id)
        )
        for p, orig in zip(reloaded.participants, plan.participants):
            assert p.outcome is orig.outcome
        for p in plan.participants:
            c2 = SqlRunRepository(session2).get(p.analysis_run_id)
            assert c2.state is state
            assert c2.events[-1].to_state is state
            assert c2.result is None
    finally:
        session2.close()
        engine2.dispose()


# ---------------------------------------------------------------------------
# 33: a post-runtime exception must not desynchronise a completed participant
# ---------------------------------------------------------------------------


def test_post_runtime_exception_preserves_completed_participant(
    council_session, monkeypatch
) -> None:
    session, _ = council_session
    task, context = _seed(session)
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    original_execute_claimed_run = ExecutionService.execute_claimed_run
    raised = False

    async def raise_after_durable_completion(
        service, run, task_arg, context_arg, workflow, profile, **kwargs
    ):
        nonlocal raised
        execution = await original_execute_claimed_run(
            service,
            run,
            task_arg,
            context_arg,
            workflow,
            profile,
            **kwargs,
        )
        if not raised:
            raised = True
            raise RuntimeError("post-runtime bookkeeping failure")
        return execution

    monkeypatch.setattr(
        ExecutionService,
        "execute_claimed_run",
        raise_after_durable_completion,
    )

    plan = asyncio.run(
        CouncilOrchestrator(session, timeout_seconds=30.0).run_council(
            task, context, specs
        , generation_revision=1)
    )

    assert raised is True
    participant = plan.participants[0]
    child = SqlRunRepository(session).get(participant.analysis_run_id)
    assert child is not None
    assert child.state is RunState.COMPLETED
    assert child.result is not None
    assert participant.outcome is ParticipantOutcome.COMPLETED
    assert participant.output_ref == child.id
    assert not any(event.to_state is RunState.FAILED for event in child.events)

    reloaded = asyncio.run(CouncilOrchestrator(session).reload_council(plan.council_run_id))
    reloaded_participant = next(
        item for item in reloaded.participants if item.id == participant.id
    )
    assert reloaded_participant.outcome is ParticipantOutcome.COMPLETED


def test_create_failure_without_handle_preserves_unknown_ownership(council_session):
    """A create exception is not proof that the adapter caused no side effects."""
    from polynexus_core.domain.generation import GenerationConflict, WorkGenerationRef
    from polynexus_core.persistence.generation import GenerationRepository

    class CreateFailure(ReferenceRuntimeAdapter):
        def __init__(self):
            super().__init__()
            self.create_calls = 0
            self.cleanup_calls = 0

        async def create_run(self, context):
            self.create_calls += 1
            raise RuntimeError("SECRET_MARKER_CREATE_UNKNOWN")

        async def cleanup(self, runtime_ref):
            self.cleanup_calls += 1
            return await super().cleanup(runtime_ref)

    session, _ = council_session
    task, context = _seed(session)
    adapter = CreateFailure()
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b")])
    with pytest.raises(GenerationConflict, match="generation_not_startable"):
        asyncio.run(CouncilOrchestrator(session, runtime_adapter=adapter).run_council(
            task, context, specs, generation_revision=1))
    repository = GenerationRepository(session)
    observation = repository.observe(WorkGenerationRef(task.id, 1))
    assert observation["ownership_unknown"] == 1
    assert observation["closed"] == 0
    assert observation["work_aborted"] is False
    assert adapter.create_calls == 1
    assert adapter.cleanup_calls == 0
    with pytest.raises(GenerationConflict, match="generation_not_startable"):
        repository.validate_run(task.id, 1, context.id)
    for run in SqlRunRepository(session).list_by_task(task.id):
        assert all("SECRET_MARKER_CREATE_UNKNOWN" not in (event.reason or "") for event in run.events)
