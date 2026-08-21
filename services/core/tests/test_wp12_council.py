"""WP-12 — Council, Cross Review, Synthesis, and Partial Failure contract tests.

Additive contract tests over existing Task/Run/RunEvent/Evidence boundaries.
No product source beyond the new council/ orchestration package is exercised.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from polynexus_core.domain.enums import EvidenceType, RunState, WorkMode
from polynexus_core.domain.models import ContextPackage, Project, Task
from polynexus_core.execution_service import ExecutionService
from polynexus_core.persistence.models import Base
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlRunEventRepository,
    SqlTaskRepository,
)
from polynexus_core.council.models import CouncilSpec, ParticipantOutcome
from polynexus_core.council.orchestrator import (
    CouncilOrchestrator,
    _PLAN_SOURCE,
    _REASON_PARTICIPANT_FAILED,
)
from polynexus_core.runtime.contracts import RuntimeStatus
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter

_FORBIDDEN_SECRET_FRAGMENTS = ("SECRET_MARKER", "sk-", "token=", "Bearer ")


@pytest.fixture()
def council_session(tmp_path: Path):
    db_path = tmp_path / "wp12.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
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
    return task, context


def _specs(ids_roles: list[tuple[str, str]], outcomes: dict[str, ParticipantOutcome] | None = None):
    outcomes = outcomes or {}
    return [
        CouncilSpec(id=pid, role=role, expected_outcome=outcomes.get(pid))
        for pid, role in ids_roles
    ]


def _run(session, task, context, specs, **kwargs):
    orch = CouncilOrchestrator(session, **kwargs)
    return asyncio.run(orch.run_council(task, context, specs))


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


class _FailingOnceAdapter(ReferenceRuntimeAdapter):
    """Adapter that raises a secret-bearing error on its FIRST create_run only.

    Used to prove runtime-failure isolation: exactly one participant fails with a
    sanitized outcome while the others continue, and no raw secret leaks.
    """

    def __init__(self) -> None:
        super().__init__()
        self._calls = 0

    async def create_run(self, context):
        self._calls += 1
        if self._calls == 1:
            raise RuntimeError("SECRET_MARKER_CRITICAL_LEAK_xyz123")
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
    plan = _run(
        session, task, context,
        _specs([("p1", "analyst-a"), ("p2", "analyst-b")], {"p2": ParticipantOutcome.FAILED}),
    )
    failed = [p for p in plan.participants if p.id == "p2"][0]
    assert failed.outcome is ParticipantOutcome.FAILED
    assert failed.reason == "Participant analysis failed (simulated boundary)"
    assert plan.partial is True
    assert plan.synthesis_run_id is not None
    assert plan.consensus_ref is not None
    ev = [e for e in SqlEvidenceRepository(session).list_by_run(plan.synthesis_run_id)
          if e.source == "council-synthesis"][0]
    assert "p2" in ev.metadata["summary"]
    assert ev.metadata["verdict_authority"] == "none"


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
    )
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
        asyncio.run(orch.run_council(task, context, specs, round=1))


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
    plan = asyncio.run(orch.run_council(task, context, specs))

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
        CouncilOrchestrator(session).run_council(task, context, specs, round=2)
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
        CouncilOrchestrator(session2).run_council(task, context, specs, round=2)
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
    asyncio.run(CouncilOrchestrator(session).run_council(task, context, specs_a, round=1))

    # Conflicting request: same task/context/round, different participant specs.
    specs_b = _specs([("p1", "analyst-a"), ("p3", "analyst-c")])
    with pytest.raises(ValueError, match="different participant specs"):
        asyncio.run(
            CouncilOrchestrator(session).run_council(task, context, specs_b, round=1)
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
        )
    )
    # Both participants are isolated as TIMED_OUT (not a Council-wide crash).
    assert all(p.outcome is ParticipantOutcome.TIMED_OUT for p in plan.participants)
    for p in plan.participants:
        run = SqlRunRepository(session).get(p.analysis_run_id)
        assert run is not None
        assert run.state is RunState.TIMED_OUT
        # Exactly one STARTING event and one legal terminal TIMED_OUT event;
        # the timeout transition must not repeat STARTING -> STARTING.
        starting = [e for e in run.events if e.to_state == RunState.STARTING]
        timed_out = [e for e in run.events if e.to_state == RunState.TIMED_OUT]
        assert len(starting) == 1
        assert len(timed_out) == 1
        assert run.events[-1].to_state is RunState.TIMED_OUT
        assert run.events[-1].reason == "Participant analysis timed out (simulated boundary)"
    # Council still completes with a truthful (failed) synthesis; no consensus is
    # fabricated when synthesis cannot run (no completed analysis + cross-review).
    assert plan.synthesis_run_id is not None
    assert plan.partial is True
    assert plan.consensus_ref is None


# ---------------------------------------------------------------------------
# 29: participant runtime failure is sanitized; other participants continue
# ---------------------------------------------------------------------------


def test_participant_failure_sanitized_others_continue(council_session) -> None:
    session, _ = council_session
    task, context = _seed(session)
    adapter = _FailingOnceAdapter()
    # 3 participants: the first adapter call fails, the other two succeed.
    specs = _specs([("p1", "analyst-a"), ("p2", "analyst-b"), ("p3", "analyst-c")])
    plan = asyncio.run(
        CouncilOrchestrator(session, runtime_adapter=adapter).run_council(task, context, specs)
    )
    # Council completed (did not crash) with a truthful partial result.
    assert plan.synthesis_run_id is not None
    failed = [p for p in plan.participants if p.outcome is ParticipantOutcome.FAILED]
    completed = [p for p in plan.participants if p.outcome is ParticipantOutcome.COMPLETED]
    assert len(failed) == 1
    assert len(completed) == 2
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
    # no raw secret, no fabricated evidence.
    for p in plan.participants:
        assert p.analysis_run_id is not None
        child = SqlRunRepository(session).get(p.analysis_run_id)
        assert child is not None
        assert child.task_id == task.id
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

        # No fabricated Evidence on a failed child Run.
        run_evidence = SqlEvidenceRepository(session).list_by_run(p.analysis_run_id)
        assert len(run_evidence) == 0, "failed run must not persist fabricated evidence"

    # Synthesis remains truthful: failed result (no consensus) when no completed
    # analysis, otherwise a truthful partial synthesis.
    synth_run = SqlRunRepository(session).get(plan.synthesis_run_id)
    assert synth_run is not None
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
        CouncilOrchestrator(session, runtime_adapter=adapter).run_council(task, context, specs)
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
        CouncilOrchestrator(session, runtime_adapter=adapter).run_council(task, context, specs)
    )

    for p in plan.participants:
        assert p.outcome is not ParticipantOutcome.COMPLETED
        assert p.output_ref is None
        child = SqlRunRepository(session).get(p.analysis_run_id)
        assert child is not None
        # run.result must be None: no raw RuntimeResult.summary / dangling refs.
        assert child.result is None
        # No fabricated Evidence/Finding/Artifact persisted for the failed Run.
        assert len(SqlEvidenceRepository(session).list_by_run(p.analysis_run_id)) == 0
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
            assert len(SqlEvidenceRepository(session2).list_by_run(p.analysis_run_id)) == 0
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
        CouncilOrchestrator(session, runtime_adapter=adapter).run_council(task, context, specs)
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
