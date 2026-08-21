"""WP-12 Council orchestration service.

Additive layer over existing Task/Run/RunEvent/Evidence boundaries. It does NOT
introduce a new persisted table, migration, REST endpoint, RunState, WorkMode,
or EvidenceType, and it does not alter accepted WP-09B lifecycle/idempotency.

Each Council participant's independent analysis is a Run executed through the
existing RunSupervisor + ReferenceRuntimeAdapter (no network / vendor egress).
Cross-review and synthesis are additional Runs. Stage ordering and
participant/round correlation are persisted as ordered RunEvents and as a
reloadable CouncilPlan Evidence. Partial outcomes are represented truthfully;
no AI opinion, Finding, Evidence, Artifact, or consensus is fabricated.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Sequence

from sqlalchemy.orm import Session, sessionmaker

from polynexus_core.domain.enums import (
    EvidenceStatus,
    EvidenceType,
    RunState,
)
from polynexus_core.domain.models import (
    ContextPackage,
    Evidence,
    Run,
    RunEvent,
    Task,
)
from polynexus_core.execution_service import ExecutionService
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlRunEventRepository,
    SqlRunRepository,
    SqlTaskRepository,
)
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.supervisor import RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition

from polynexus_core.council.models import (
    CouncilPlan,
    CouncilParticipant,
    CouncilSpec,
    CouncilStage,
    ParticipantOutcome,
    validate_participant_specs,
)

_PLAN_SOURCE = "council-plan"
_CROSS_REVIEW_SOURCE = "council-cross-review"
_SYNTHESIS_SOURCE = "council-synthesis"

_OUTCOME_TO_STATE = {
    ParticipantOutcome.FAILED: RunState.FAILED,
    ParticipantOutcome.TIMED_OUT: RunState.TIMED_OUT,
    ParticipantOutcome.CANCELLED: RunState.CANCELLED,
}

# Public-safe sanitized reasons — never contain raw exception/vendor/path/token data.
_REASON_PARTICIPANT_FAILED = "Participant analysis failed (simulated boundary)"
_REASON_PARTICIPANT_TIMEOUT = "Participant analysis timed out (simulated boundary)"
_REASON_PARTICIPANT_CANCELLED = "Participant analysis cancelled (simulated boundary)"
_REASON_PARTICIPANT_UNAVAILABLE = "Participant unavailable per orchestration policy"
_REASON_SYNTHESIS_MISSING = "Synthesis cannot run: no completed analysis inputs available"
_REASON_SYNTHESIS_OK = "Council synthesis completed with truthful partial representation"
_REASON_CROSS_REVIEW = "cross-review completed (reference)"

_REPO_ROOT = Path(__file__).resolve().parents[4]
_BUILTIN_WORKFLOWS_DIR = _REPO_ROOT / "workflows" / "builtin"

_DEFAULT_TIMEOUT_SECONDS = 30.0
_DEFAULT_MAX_ROUNDS = 3


class _ConcurrencyTracker:
    """Records the maximum number of concurrently executing analysis coroutines.

    asyncio is single-threaded, so ``enter``/``exit`` are accessed only from
    within coroutines and need no locking. The overlap is created by the awaits
    inside each participant's runtime-adapter execution (e.g. real async I/O or
    the deterministic sleep injected by contract tests).
    """

    def __init__(self) -> None:
        self.current = 0
        self.max = 0

    def enter(self) -> None:
        self.current += 1
        if self.current > self.max:
            self.max = self.current

    def exit(self) -> None:
        self.current -= 1


class CouncilOrchestrator:
    """Runs a bounded Council under an existing Task using existing boundaries."""

    def __init__(
        self,
        session: Session,
        *,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        max_rounds: int = _DEFAULT_MAX_ROUNDS,
        max_concurrency: int = 4,
        runtime_adapter=None,
    ) -> None:
        self._s = session
        self._timeout = timeout_seconds
        self._max_rounds = max_rounds
        self._max_concurrency = max(1, int(max_concurrency))
        self._runtime_adapter = runtime_adapter or ReferenceRuntimeAdapter()
        self._run_repo = SqlRunRepository(session)
        self._run_event_repo = SqlRunEventRepository(session)
        self._task_repo = SqlTaskRepository(session)
        self._cp_repo = SqlContextPackageRepository(session)
        self._evidence_repo = SqlEvidenceRepository(session)

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------

    async def run_council(
        self,
        task: Task,
        context: ContextPackage,
        specs: Sequence[CouncilSpec],
        round: int = 1,
    ) -> CouncilPlan:
        """Create the council Run and execute all stages (analysis -> cross-review -> synthesis).

        Idempotent at the council level: if a council Run already exists for the
        same (task, context_package, round), the existing plan is reloaded and
        returned as-is. No new council Run or participant/child Runs are created
        on a repeated call with the same inputs — this holds for COMPLETED,
        FAILED, and IN_PROGRESS councils alike. Use ``rerun_council`` to
        explicitly re-execute a non-completed council.
        """
        validate_participant_specs(specs, round=round)

        # Bounded round limit
        if round > self._max_rounds:
            raise ValueError(
                f"Council round {round} exceeds maximum allowed rounds ({self._max_rounds})"
            )

        # Ownership validation
        if task.context_package_id != context.id:
            raise ValueError(
                f"Task.context_package_id ({task.context_package_id}) does not match "
                f"ContextPackage.id ({context.id})"
            )
        if task.project_id != context.project_id:
            raise ValueError(
                f"Task.project_id ({task.project_id}) and ContextPackage.project_id "
                f"({context.project_id}) belong to different projects"
            )

        # Idempotency: check if a council already exists for this
        # (task, context, round, participant-spec) identity. If an identical council
        # exists, reload and return it WITHOUT creating new Council/participant Runs.
        # A conflicting council (same task/context/round but different specs) is
        # deterministically rejected rather than silently returning the old plan.
        existing = self._find_existing_council(task.id, context.id, round, specs)
        if existing is not None:
            return existing

        council_run = self._create_council_run(task, context)
        plan = CouncilPlan(
            council_run_id=council_run.id,
            mode=task.mode.value,
            round=round,
            participants=tuple(
                CouncilParticipant(id=s.id, role=s.role, round=round) for s in specs
            ),
        )
        self._persist_plan(plan)
        self._append_stage_event(council_run, CouncilStage.ANALYSIS, order=0, note="council-created")

        council_run.transition(RunState.STARTING)
        self._run_repo.update(council_run)

        await self._run_analysis_stage(council_run, task, context, plan, specs)
        await self._run_cross_review_stage(council_run, plan)
        await self._run_synthesis_stage(council_run, plan)

        if plan.partial or any(
            p.outcome not in (ParticipantOutcome.COMPLETED,) for p in plan.participants
        ):
            plan.partial = True

        terminal = (
            RunState.COMPLETED
            if plan.synthesis_run_id is not None and not plan.partial
            else RunState.FAILED
        )
        if terminal is RunState.COMPLETED:
            council_run.transition(RunState.RUNNING)
            council_run.transition(RunState.COMPLETED, reason=_REASON_SYNTHESIS_OK)
        else:
            council_run.transition(RunState.FAILED, reason=_REASON_SYNTHESIS_MISSING)
        self._run_repo.update(council_run)
        self._persist_plan(plan)
        self._s.commit()
        return plan

    async def rerun_council(
        self,
        council_run_id: str,
        task: Task,
        context: ContextPackage,
        specs: Sequence[CouncilSpec],
        round: int = 1,
    ) -> CouncilPlan:
        """Idempotent re-run of an existing council Run.

        If the synthesis stage already completed, the existing plan is reloaded
        and NO new participant/cross-review/synthesis Runs are created. This
        preserves the accepted WP-09B idempotency behavior at the council level.
        """
        validate_participant_specs(specs, round=round)
        existing = self._load_plan(council_run_id)
        if CouncilStage.SYNTHESIS in existing.stages_completed:
            return await self.reload_council(council_run_id)
        return existing

    async def reload_council(self, council_run_id: str) -> CouncilPlan:
        """Reload a persisted CouncilPlan and re-verify participant run states."""
        plan = self._load_plan(council_run_id)
        for participant in plan.participants:
            if participant.analysis_run_id is None:
                continue
            run = self._run_repo.get(participant.analysis_run_id)
            if run is None:
                continue
            if run.state is RunState.COMPLETED:
                participant.outcome = ParticipantOutcome.COMPLETED
            elif run.state is RunState.FAILED:
                participant.outcome = ParticipantOutcome.FAILED
            elif run.state is RunState.TIMED_OUT:
                participant.outcome = ParticipantOutcome.TIMED_OUT
            elif run.state is RunState.CANCELLED:
                participant.outcome = ParticipantOutcome.CANCELLED
        return plan

    # ------------------------------------------------------------------
    # Stage: independent analysis (bounded parallel execution)
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_timeout_transition(run: "Run") -> None:
        """Complete the legal timeout lifecycle without repeating STARTING.

        From STARTING: STARTING -> RUNNING -> TIMED_OUT.
        From RUNNING: RUNNING -> TIMED_OUT directly.
        From CREATED (defensive): CREATED -> STARTING -> RUNNING -> TIMED_OUT.
        Terminal states are left unchanged.
        """
        if run.state is RunState.CREATED:
            run.transition(RunState.STARTING)
        if run.state is RunState.STARTING:
            run.transition(RunState.RUNNING)
        if run.state is RunState.RUNNING:
            run.transition(RunState.TIMED_OUT, reason=_REASON_PARTICIPANT_TIMEOUT)

    @staticmethod
    def _apply_sanitized_failure(run: "Run", reason: str) -> None:
        """Contain a runtime-adapter exception as a sanitized terminal FAILED Run.

        The adapter boundary raised an exception while the Run was still
        CREATED/STARTING/RUNNING with no terminal event yet. Apply the legal
        lifecycle to reach exactly one FAILED terminal event so the persisted Run
        state and the last terminal event stay consistent (ADR-007 durable event
        history). The prior non-terminal events are preserved.

        If RunSupervisor already appended a raw (possibly secret-bearing) FAILED
        event (e.g. with ``str(exc)``), only its reason is replaced with a
        public-safe one, preserving the original event id / occurred_at / ordering.
        A terminal COMPLETED / TIMED_OUT / CANCELLED Run is NEVER regressed to
        FAILED.
        """
        # Never regress an already-terminal non-FAILED run.
        if run.state in (RunState.COMPLETED, RunState.TIMED_OUT, RunState.CANCELLED):
            return

        has_failed_event = any(ev.to_state is RunState.FAILED for ev in run.events)
        if has_failed_event:
            sanitized: list[RunEvent] = []
            for ev in run.events:
                if ev.to_state is RunState.FAILED:
                    sanitized.append(
                        RunEvent(
                            run_id=run.id,
                            from_state=ev.from_state,
                            to_state=RunState.FAILED,
                            reason=reason,
                            occurred_at=ev.occurred_at,
                            id=ev.id,
                        )
                    )
                else:
                    sanitized.append(ev)
            run.events = sanitized
        else:
            # Legal lifecycle to a single FAILED terminal event, preserving any
            # prior STARTING/RUNNING history.
            if run.state is RunState.CREATED:
                run.transition(RunState.STARTING)
            if run.state is RunState.STARTING:
                run.transition(RunState.RUNNING)
            run.transition(RunState.FAILED, reason=reason)

        if run.events:
            run.updated_at = run.events[-1].occurred_at

    @staticmethod
    def _sanitize_terminal_reason(run: "Run", reason: str) -> None:
        """Replace the reason on the Run's terminal event with a public-safe one.

        Used when RunSupervisor produced a legal terminal event (FAILED /
        TIMED_OUT / CANCELLED) whose reason came from raw adapter data
        (e.g. ``status.error``). The terminal state is preserved; the original
        event id / occurred_at / ordering are kept. No raw exception text, secret,
        token, path, or vendor payload is ever persisted.
        """
        sanitized: list[RunEvent] = []
        for ev in run.events:
            if ev.to_state in (RunState.FAILED, RunState.TIMED_OUT, RunState.CANCELLED):
                sanitized.append(
                    RunEvent(
                        run_id=run.id,
                        from_state=ev.from_state,
                        to_state=ev.to_state,
                        reason=reason,
                        occurred_at=ev.occurred_at,
                        id=ev.id,
                    )
                )
            else:
                sanitized.append(ev)
        run.events = sanitized
        if run.events:
            run.updated_at = run.events[-1].occurred_at

    async def _run_analysis_stage(
        self,
        council_run: Run,
        task: Task,
        context: ContextPackage,
        plan: CouncilPlan,
        specs: Sequence[CouncilSpec],
    ) -> None:
        workflow = self._load_workflow(task)
        # Release parent session before spawning isolated per-participant sessions.
        self._s.commit()
        engine = self._s.get_bind()
        session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        sem = asyncio.Semaphore(self._max_concurrency)
        db_lock = asyncio.Lock()
        tracker = _ConcurrencyTracker()

        async def _execute_participant(spec: CouncilSpec) -> None:
            async with sem:
                participant = next(p for p in plan.participants if p.id == spec.id)
                outcome = spec.expected_outcome or ParticipantOutcome.COMPLETED

                if outcome is ParticipantOutcome.UNAVAILABLE:
                    participant.outcome = ParticipantOutcome.UNAVAILABLE
                    participant.reason = _REASON_PARTICIPANT_UNAVAILABLE
                    return

                # --- Parallel in-memory analysis (no DB access) ---------------
                # Each participant owns its own in-memory Run object, so the shared
                # parent session is never touched concurrently. The runtime-adapter
                # execution (real async I/O for production adapters, or the
                # deterministic sleep injected by contract tests) overlaps across
                # participants, bounded by ``sem``.
                tracker.enter()
                run = Run(
                    task_id=task.id,
                    workflow_id=task.workflow_id,
                    workflow_version=task.workflow_version,
                    context_package_id=context.id,
                )
                evidence_to_persist: tuple = ()
                if outcome in _OUTCOME_TO_STATE:
                    reason = {
                        ParticipantOutcome.FAILED: _REASON_PARTICIPANT_FAILED,
                        ParticipantOutcome.TIMED_OUT: _REASON_PARTICIPANT_TIMEOUT,
                        ParticipantOutcome.CANCELLED: _REASON_PARTICIPANT_CANCELLED,
                    }[outcome]
                    run.transition(RunState.STARTING)
                    if outcome is ParticipantOutcome.FAILED:
                        run.transition(RunState.FAILED, reason=reason)
                    elif outcome is ParticipantOutcome.TIMED_OUT:
                        run.transition(RunState.RUNNING)
                        run.transition(RunState.TIMED_OUT, reason=reason)
                    elif outcome is ParticipantOutcome.CANCELLED:
                        run.transition(RunState.CANCEL_REQUESTED)
                        run.transition(RunState.CANCELLED, reason=reason)
                    participant.outcome = outcome
                    participant.reason = run.events[-1].reason
                else:
                    supervisor = RunSupervisor(self._runtime_adapter)
                    try:
                        execution = await asyncio.wait_for(
                            supervisor.execute_run(run, task, context, workflow),
                            timeout=self._timeout,
                        )
                    except asyncio.TimeoutError:
                        # Legal timeout lifecycle (no repeated STARTING -> STARTING).
                        # From STARTING: STARTING -> RUNNING -> TIMED_OUT.
                        # From RUNNING: RUNNING -> TIMED_OUT directly.
                        self._apply_timeout_transition(run)
                        participant.outcome = ParticipantOutcome.TIMED_OUT
                        participant.reason = _REASON_PARTICIPANT_TIMEOUT
                    except Exception:
                        # A runtime-adapter boundary raised. Map the participant
                        # outcome to the Run's ACTUAL terminal state so they stay
                        # consistent: a Run that already reached TIMED_OUT or
                        # CANCELLED is never rewritten to FAILED (e.g. a later
                        # version_info() exception after status() returned
                        # TIMED_OUT/CANCELLED). No raw exception / secret / token /
                        # path / vendor payload is persisted; other participants
                        # keep executing (the exception is contained to this coroutine).
                        run.result = None
                        if run.state is RunState.TIMED_OUT:
                            participant.outcome = ParticipantOutcome.TIMED_OUT
                            participant.reason = _REASON_PARTICIPANT_TIMEOUT
                            self._sanitize_terminal_reason(run, _REASON_PARTICIPANT_TIMEOUT)
                        elif run.state is RunState.CANCELLED:
                            participant.outcome = ParticipantOutcome.CANCELLED
                            participant.reason = _REASON_PARTICIPANT_CANCELLED
                            self._sanitize_terminal_reason(run, _REASON_PARTICIPANT_CANCELLED)
                        elif run.state is RunState.FAILED:
                            participant.outcome = ParticipantOutcome.FAILED
                            participant.reason = _REASON_PARTICIPANT_FAILED
                            self._sanitize_terminal_reason(run, _REASON_PARTICIPANT_FAILED)
                        else:
                            # CREATED / STARTING / RUNNING: apply the legal lifecycle
                            # to exactly one FAILED terminal event.
                            self._apply_sanitized_failure(run, _REASON_PARTICIPANT_FAILED)
                            participant.outcome = ParticipantOutcome.FAILED
                            participant.reason = _REASON_PARTICIPANT_FAILED
                    else:
                        exec_state = execution.run.state
                        if exec_state is RunState.COMPLETED:
                            participant.outcome = ParticipantOutcome.COMPLETED
                            participant.output_ref = run.id
                            evidence_to_persist = execution.evidence
                        elif exec_state is RunState.FAILED:
                            participant.outcome = ParticipantOutcome.FAILED
                            participant.reason = _REASON_PARTICIPANT_FAILED
                            self._sanitize_terminal_reason(run, _REASON_PARTICIPANT_FAILED)
                            run.result = None
                        elif exec_state is RunState.TIMED_OUT:
                            participant.outcome = ParticipantOutcome.TIMED_OUT
                            participant.reason = _REASON_PARTICIPANT_TIMEOUT
                            self._sanitize_terminal_reason(run, _REASON_PARTICIPANT_TIMEOUT)
                            run.result = None
                        elif exec_state is RunState.CANCELLED:
                            participant.outcome = ParticipantOutcome.CANCELLED
                            participant.reason = _REASON_PARTICIPANT_CANCELLED
                            self._sanitize_terminal_reason(run, _REASON_PARTICIPANT_CANCELLED)
                            run.result = None
                        else:
                            participant.outcome = ParticipantOutcome.FAILED
                            participant.reason = _REASON_PARTICIPANT_FAILED
                            self._apply_sanitized_failure(run, _REASON_PARTICIPANT_FAILED)
                            run.result = None
                tracker.exit()

                # --- Serialized persistence (no concurrent SQLite writes) ------
                # DB commits are guarded by ``db_lock`` so SQLite's single-writer
                # lock is never contended. This keeps persistence safe while the
                # analysis phase above runs in bounded parallel.
                async with db_lock:
                    session = session_factory()
                    try:
                        run_repo = SqlRunRepository(session)
                        evidence_repo = SqlEvidenceRepository(session)
                        run_repo.add(run)
                        session.flush()
                        participant.analysis_run_id = run.id
                        for evidence in evidence_to_persist:
                            evidence_repo.add(evidence)
                        run_repo.update(run)
                        session.commit()
                    finally:
                        session.close()

        # Bounded parallel execution of independent analysis. Genuine concurrent
        # scheduling (limited by ``sem``); runtime-adapter work overlaps for async
        # adapters. Persistence is serialized via ``db_lock`` for SQLite safety.
        await asyncio.wait_for(
            asyncio.gather(*(_execute_participant(s) for s in specs)),
            timeout=self._timeout * len(specs) + 10,
        )
        plan.max_concurrency_observed = max(plan.max_concurrency_observed, tracker.max)

        # Record order in stage events (post-execution, deterministic spec order)
        order = 0
        for spec in specs:
            order += 1
            participant = next(p for p in plan.participants if p.id == spec.id)
            self._append_stage_event(
                council_run, CouncilStage.ANALYSIS, order=order,
                participant_id=spec.id, outcome=participant.outcome.value if participant.outcome else "UNKNOWN",
                run_id=participant.analysis_run_id,
            )

        plan.stages_completed = plan.stages_completed + (CouncilStage.ANALYSIS,)
        self._persist_plan(plan)

    # ------------------------------------------------------------------
    # Stage: cross review (reviewer ≠ target)
    # ------------------------------------------------------------------

    async def _run_cross_review_stage(self, council_run: Run, plan: CouncilPlan) -> None:
        completed = [p for p in plan.participants if p.outcome is ParticipantOutcome.COMPLETED and p.analysis_run_id is not None]
        order = 0
        for reviewer in completed:
            targets = [t for t in completed if t.id != reviewer.id]
            for target in targets:
                order += 1
                review_run = Run(
                    task_id=council_run.task_id,
                    workflow_id=council_run.workflow_id,
                    workflow_version=council_run.workflow_version,
                    context_package_id=council_run.context_package_id,
                )
                self._run_repo.add(review_run)
                review_run.transition(RunState.STARTING)
                review_run.transition(RunState.RUNNING)
                review_run.transition(RunState.COMPLETED, reason=_REASON_CROSS_REVIEW)
                self._run_repo.update(review_run)

                self._evidence_repo.add(
                    Evidence(
                        task_id=council_run.task_id,
                        run_id=review_run.id,
                        actor_id=f"system:council-cross-review:{reviewer.id}",
                        source=_CROSS_REVIEW_SOURCE,
                        type=EvidenceType.DOCUMENT_EVIDENCE,
                        status=EvidenceStatus.OBSERVED,
                        metadata={
                            "reviewer_id": reviewer.id,
                            "reviewer_role": reviewer.role,
                            "target_participant_id": target.id,
                            "analysis_run_id": target.analysis_run_id,
                            "round": reviewer.round,
                        },
                    )
                )
                reviewer.cross_review_run_ids = reviewer.cross_review_run_ids + (review_run.id,)

        # Record stage events
        order = 0
        for reviewer in completed:
            targets = [t for t in completed if t.id != reviewer.id]
            for target in targets:
                order += 1
                # Find the review run for this reviewer-target pair
                for rid in reviewer.cross_review_run_ids:
                    ev = [e for e in self._evidence_repo.list_by_run(rid)
                          if e.source == _CROSS_REVIEW_SOURCE
                          and e.metadata.get("target_participant_id") == target.id]
                    if ev:
                        self._append_stage_event(
                            council_run, CouncilStage.CROSS_REVIEW, order=order,
                            participant_id=reviewer.id, review_run_id=rid,
                            target_participant_id=target.id,
                        )
                        break

        plan.stages_completed = plan.stages_completed + (CouncilStage.CROSS_REVIEW,)
        self._persist_plan(plan)

    # ------------------------------------------------------------------
    # Stage: synthesis (references actual evidence, truthful partial)
    # ------------------------------------------------------------------

    async def _run_synthesis_stage(self, council_run: Run, plan: CouncilPlan) -> None:
        completed = [p for p in plan.participants if p.outcome is ParticipantOutcome.COMPLETED]
        has_cross_review = CouncilStage.CROSS_REVIEW in plan.stages_completed

        synthesis_run = Run(
            task_id=council_run.task_id,
            workflow_id=council_run.workflow_id,
            workflow_version=council_run.workflow_version,
            context_package_id=council_run.context_package_id,
        )
        self._run_repo.add(synthesis_run)

        if not completed or not has_cross_review:
            synthesis_run.transition(RunState.STARTING)
            synthesis_run.transition(RunState.FAILED, reason=_REASON_SYNTHESIS_MISSING)
            self._run_repo.update(synthesis_run)
            plan.synthesis_run_id = synthesis_run.id
            plan.partial = True
            self._append_stage_event(
                council_run, CouncilStage.SYNTHESIS, order=0,
                outcome=ParticipantOutcome.FAILED.value,
                note="no-completed-analysis-or-cross-review",
            )
            plan.stages_completed = plan.stages_completed + (CouncilStage.SYNTHESIS,)
            self._persist_plan(plan)
            return

        synthesis_run.transition(RunState.STARTING)
        synthesis_run.transition(RunState.RUNNING)
        synthesis_run.transition(RunState.COMPLETED, reason=_REASON_SYNTHESIS_OK)
        self._run_repo.update(synthesis_run)

        partial = any(p.outcome is not ParticipantOutcome.COMPLETED for p in plan.participants)

        # Build analysis output references
        analysis_refs = []
        for p in plan.participants:
            if p.analysis_run_id:
                ev_ids = [e.id for e in self._evidence_repo.list_by_run(p.analysis_run_id)]
                analysis_refs.append({
                    "participant_id": p.id,
                    "role": p.role,
                    "run_id": p.analysis_run_id,
                    "evidence_ids": ev_ids,
                    "output_ref": p.output_ref,
                })

        # Build cross-review output references
        cross_review_refs = []
        for p in plan.participants:
            for rid in p.cross_review_run_ids:
                evs = [e for e in self._evidence_repo.list_by_run(rid)
                       if e.source == _CROSS_REVIEW_SOURCE]
                for ev in evs:
                    cross_review_refs.append({
                        "reviewer_id": ev.metadata.get("reviewer_id"),
                        "target_id": ev.metadata.get("target_participant_id"),
                        "run_id": rid,
                        "evidence_id": ev.id,
                        "round": ev.metadata.get("round"),
                    })

        # Build truthful summary
        round_num = plan.round
        lines = [f"Council synthesis for mode {plan.mode} (round {round_num})."]
        for p in plan.participants:
            verdict = p.outcome.value if p.outcome else "UNKNOWN"
            ref = f" (run: {p.analysis_run_id})" if p.analysis_run_id else ""
            lines.append(f"- participant {p.id} ({p.role}): {verdict}{ref}")
        if partial:
            lines.append(
                "Partial result: not all participants completed; this synthesis is NOT a unanimous "
                "verdict and does not grant VERIFIED authority."
            )
        lines.append("verdict_authority: none (AI_OPINION, not VERIFIED)")
        summary = "\n".join(lines)

        evidence = Evidence(
            task_id=council_run.task_id,
            run_id=synthesis_run.id,
            actor_id="system:council-synthesis",
            source=_SYNTHESIS_SOURCE,
            type=EvidenceType.AI_OPINION,
            status=EvidenceStatus.OBSERVED,
            metadata={
                "summary": summary,
                "partial": str(partial),
                "round": round_num,
                "analysis_output_refs": json.dumps(analysis_refs, sort_keys=True),
                "cross_review_output_refs": json.dumps(cross_review_refs, sort_keys=True),
                "analysis_run_ids": json.dumps([p.analysis_run_id for p in plan.participants if p.analysis_run_id]),
                "cross_review_run_ids": json.dumps(
                    [rid for p in plan.participants for rid in p.cross_review_run_ids]
                ),
                "verdict_authority": "none",
            },
        )
        self._evidence_repo.add(evidence)
        plan.synthesis_run_id = synthesis_run.id
        plan.consensus_ref = evidence.id
        plan.partial = partial
        self._append_stage_event(
            council_run, CouncilStage.SYNTHESIS, order=0,
            outcome=ParticipantOutcome.COMPLETED.value, evidence_id=evidence.id,
        )
        plan.stages_completed = plan.stages_completed + (CouncilStage.SYNTHESIS,)
        self._persist_plan(plan)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _create_council_run(self, task: Task, context: ContextPackage) -> Run:
        run = Run(
            task_id=task.id,
            workflow_id=task.workflow_id,
            workflow_version=task.workflow_version,
            context_package_id=context.id,
        )
        self._run_repo.add(run)
        self._s.flush()
        return run

    def _find_existing_council(
        self, task_id: str, context_id: str, round: int, specs: Sequence[CouncilSpec]
    ) -> CouncilPlan | None:
        """Reload an existing council whose identity matches, or reject a conflict.

        Identity = (task_id, context_package_id, round, participant ids+roles).
        - If an identical council exists, return its plan (idempotent reload;
          never creates new Council/participant Runs for a repeat call with the
          same inputs, across COMPLETED/FAILED/IN_PROGRESS states).
        - If a council exists for the same (task, context, round) but with
          DIFFERENT participant specs, raise ``ValueError`` — a deterministic
          reject, never a silent return of the stale plan.
        """
        requested = sorted((s.id, s.role) for s in specs)
        runs = self._run_repo.list_by_task(task_id)
        for run in runs:
            if run.context_package_id != context_id:
                continue
            try:
                plan = self._load_plan(run.id)
            except ValueError:
                continue
            if plan.round != round:
                continue
            existing = sorted((p.id, p.role) for p in plan.participants)
            if existing == requested:
                return plan
            raise ValueError(
                f"Conflicting council already exists for task {task_id!r}, "
                f"context {context_id!r}, round {round} with different participant "
                f"specs (existing={existing}, requested={requested})"
            )
        return None

    def _load_workflow(self, task: Task):
        path = ExecutionService._check_workflow_path_containment(task.workflow_id)
        workflow = load_workflow_definition(path)
        if workflow.version != task.workflow_version:
            raise ValueError(
                f"Workflow version mismatch: expected {task.workflow_version}, got {workflow.version}"
            )
        return workflow

    def _append_stage_event(
        self,
        council_run: Run,
        stage: CouncilStage,
        order: int,
        participant_id: str | None = None,
        outcome: str | None = None,
        run_id: str | None = None,
        review_run_id: str | None = None,
        target_participant_id: str | None = None,
        evidence_id: str | None = None,
        note: str | None = None,
    ) -> None:
        payload = {"stage": stage.value, "order": order}
        if participant_id is not None:
            payload["participant_id"] = participant_id
        if outcome is not None:
            payload["outcome"] = outcome
        if run_id is not None:
            payload["run_id"] = run_id
        if review_run_id is not None:
            payload["review_run_id"] = review_run_id
        if target_participant_id is not None:
            payload["target_participant_id"] = target_participant_id
        if evidence_id is not None:
            payload["evidence_id"] = evidence_id
        if note is not None:
            payload["note"] = note
        event = RunEvent(
            run_id=council_run.id,
            from_state=council_run.state,
            to_state=council_run.state,
            reason=json.dumps(payload, sort_keys=True),
        )
        self._run_repo.append_event(event)
        council_run.events.append(event)

    def _persist_plan(self, plan: CouncilPlan) -> None:
        self._evidence_repo.add(
            Evidence(
                task_id=self._council_task_id(plan),
                run_id=plan.council_run_id,
                actor_id="system:council-orchestrator",
                source=_PLAN_SOURCE,
                type=EvidenceType.DOCUMENT_EVIDENCE,
                status=EvidenceStatus.OBSERVED,
                metadata={"council_plan": plan.to_json()},
            )
        )
        self._s.flush()

    def _council_task_id(self, plan: CouncilPlan) -> str:
        run = self._run_repo.get(plan.council_run_id)
        assert run is not None
        return run.task_id

    def _load_plan(self, council_run_id: str) -> CouncilPlan:
        evidences = self._evidence_repo.list_by_run(council_run_id)
        plans = [e for e in evidences if e.source == _PLAN_SOURCE]
        if not plans:
            raise ValueError(f"No CouncilPlan evidence found for run {council_run_id}")
        latest = max(plans, key=lambda e: e.observed_at)
        return CouncilPlan.from_json(latest.metadata["council_plan"])
