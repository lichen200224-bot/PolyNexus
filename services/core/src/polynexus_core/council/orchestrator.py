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
from polynexus_core.runtime.registry import (
    RuntimeRegistry,
    RuntimeProfile,
    build_default_registry,
    build_reference_profile,
)
from polynexus_core.runtime.redaction import sanitize_evidence, sanitize_event
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
_REASON_UNVERIFIED_CLEANUP = "Participant analysis cleanup could not be verified"
_REASON_COUNCIL_UNVERIFIED_CLEANUP = "Council execution cleanup could not be verified"
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
        runtime_registry: RuntimeRegistry | None = None,
    ) -> None:
        if runtime_adapter is not None and runtime_registry is not None:
            raise ValueError(
                "runtime_adapter and runtime_registry are mutually exclusive"
            )
        self._s = session
        self._timeout = timeout_seconds
        self._max_rounds = max_rounds
        self._max_concurrency = max(1, int(max_concurrency))
        if runtime_registry is not None:
            self._registry = runtime_registry
        elif runtime_adapter is None:
            self._registry = build_default_registry()
        else:
            # Preserve the existing test/composition hook without putting
            # adapter selection back into the Council execution path.
            self._registry = RuntimeRegistry()
            self._registry.register(build_reference_profile(), lambda: runtime_adapter)
        self._execution_service = ExecutionService(session, registry=self._registry)
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

        # Parent Council Run is a real durable Run under the approved G13
        # policy: bind it through the shared service before stage execution.
        council_run, council_profile = self._execution_service.prepare_claimed_run(
            council_run, task, context, self._load_workflow(task)
        )
        bound_run_ids: set[str] = set()

        try:
            await self._run_analysis_stage(
                council_run, task, context, plan, specs, bound_run_ids
            )
            await self._run_cross_review_stage(council_run, plan, bound_run_ids)
            await self._run_synthesis_stage(council_run, plan, bound_run_ids)

            if not plan.partial:
                # The parent Council Run is itself a real execution identity.
                # Keep this call inside the fail-closed boundary so timeout,
                # cancellation, setup, and factory errors cannot unwind while the
                # bound parent remains STARTING/RUNNING.
                parent_execution = await asyncio.wait_for(
                    self._execution_service.execute_claimed_run(
                        council_run,
                        task,
                        context,
                        self._load_workflow(task),
                        council_profile,
                        fail_closed_on_factory_error=True,
                    ),
                    timeout=self._timeout,
                )
                council_run = parent_execution.run
                if council_run.state is not RunState.COMPLETED:
                    plan.partial = True
                    plan.consensus_ref = None
                    raise RuntimeError("Council parent runtime did not complete")

        except asyncio.TimeoutError:
            self._fail_closed_council_interruption(
                council_run, plan, extra_run_ids=bound_run_ids
            )
            raise
        except asyncio.CancelledError:
            self._fail_closed_council_interruption(
                council_run, plan, extra_run_ids=bound_run_ids
            )
            raise
        except Exception:
            # Any post-binding setup failure must fail closed.  Do not leave the
            # parent Council Run (or already-bound children) durably STARTING.
            self._fail_closed_council_interruption(
                council_run, plan, extra_run_ids=bound_run_ids
            )
            raise

        if plan.partial or any(
            p.outcome not in (ParticipantOutcome.COMPLETED,) for p in plan.participants
        ):
            plan.partial = True

        if not plan.partial:
            # The parent was completed by the binding-aware runtime path above.
            pass
        else:
            # Partial/invalid input is a truthful Council semantic failure; it
            # must not be presented as a successful parent runtime execution.
            council_run.transition(RunState.RUNNING)
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
            elif run.state is RunState.ORPHANED:
                participant.outcome = ParticipantOutcome.TIMED_OUT
                participant.reason = _REASON_UNVERIFIED_CLEANUP
        return plan

    # ------------------------------------------------------------------
    # Stage: independent analysis (bounded parallel execution)
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_timeout_transition(
        run: "Run", *, reason: str = _REASON_UNVERIFIED_CLEANUP
    ) -> None:
        """Fail closed when an outer timeout has unverified cleanup.

        The outer ``wait_for`` cancellation does not prove that adapter cleanup
        completed.  Preserve that uncertainty durably instead of claiming a
        verified timeout: CREATED (defensive) -> STARTING -> CANCEL_REQUESTED
        -> ORPHANED, or STARTING/RUNNING -> CANCEL_REQUESTED -> ORPHANED.
        Terminal states are left unchanged.
        """
        if run.state is RunState.CREATED:
            run.transition(RunState.STARTING)
        if run.state in (RunState.STARTING, RunState.RUNNING):
            run.transition(
                RunState.CANCEL_REQUESTED, reason=reason
            )
        if run.state is RunState.CANCEL_REQUESTED:
            run.transition(RunState.ORPHANED, reason=reason)

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
        A terminal COMPLETED / TIMED_OUT / CANCELLED / ORPHANED Run is NEVER
        regressed to FAILED.
        """
        # Never regress an already-terminal non-FAILED run.
        if run.state in (
            RunState.COMPLETED,
            RunState.TIMED_OUT,
            RunState.CANCELLED,
            RunState.ORPHANED,
        ):
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
          TIMED_OUT / CANCELLED / ORPHANED) whose reason came from raw adapter data
        (e.g. ``status.error``). The terminal state is preserved; the original
        event id / occurred_at / ordering are kept. No raw exception text, secret,
        token, path, or vendor payload is ever persisted.
        """
        sanitized: list[RunEvent] = []
        for ev in run.events:
            if ev.to_state in (
                RunState.FAILED,
                RunState.TIMED_OUT,
                RunState.CANCELLED,
                RunState.ORPHANED,
            ):
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

    def _fail_closed_council_interruption(
        self,
        council_run: Run,
        plan: CouncilPlan,
        *,
        extra_run_ids: set[str] | None = None,
    ) -> None:
        """Persist fail-closed states after outer Council interruption.

        ``asyncio.wait_for`` and explicit task cancellation can interrupt the
        participant gather without proving adapter cleanup. Every already-bound
        non-terminal child is therefore durably moved to ORPHANED, and the bound
        parent Council Run receives the same fail-closed treatment. This helper is
        synchronous so it can run after catching ``TimeoutError``/``CancelledError``
        before the owning task is allowed to unwind.
        """
        run_ids = {
            participant.analysis_run_id
            for participant in plan.participants
            if participant.analysis_run_id is not None
        }
        run_ids.update(extra_run_ids or ())
        for run_id in run_ids:
            run = self._run_repo.get(run_id)
            if run is None:
                continue
            self._apply_timeout_transition(run)
            participant = next(
                (
                    participant
                    for participant in plan.participants
                    if participant.analysis_run_id == run.id
                ),
                None,
            )
            if participant is not None:
                if run.state in (RunState.ORPHANED, RunState.TIMED_OUT):
                    participant.outcome = ParticipantOutcome.TIMED_OUT
                    participant.reason = _REASON_UNVERIFIED_CLEANUP
                elif run.state is RunState.CANCELLED:
                    participant.outcome = ParticipantOutcome.CANCELLED
                    participant.reason = _REASON_PARTICIPANT_CANCELLED
                elif run.state is RunState.FAILED:
                    participant.outcome = ParticipantOutcome.FAILED
                    participant.reason = _REASON_PARTICIPANT_FAILED
                elif run.state is RunState.COMPLETED:
                    participant.outcome = ParticipantOutcome.COMPLETED
            self._run_repo.update(run)

            if participant is None:
                run.result = None
                self._run_repo.update(run)

        self._apply_timeout_transition(
            council_run, reason=_REASON_COUNCIL_UNVERIFIED_CLEANUP
        )
        self._run_repo.update(council_run)
        plan.partial = True
        self._persist_plan(plan)
        self._s.commit()

    async def _run_analysis_stage(
        self,
        council_run: Run,
        task: Task,
        context: ContextPackage,
        plan: CouncilPlan,
        specs: Sequence[CouncilSpec],
        bound_run_ids: set[str] | None = None,
    ) -> None:
        workflow = self._load_workflow(task)
        # Release parent session before spawning isolated per-participant sessions.
        self._s.commit()
        engine = self._s.get_bind()
        session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        sem = asyncio.Semaphore(self._max_concurrency)
        db_lock = asyncio.Lock()
        tracker = _ConcurrencyTracker()
        tracked_run_ids = bound_run_ids if bound_run_ids is not None else set()

        async def _execute_participant(spec: CouncilSpec) -> None:
            async with sem:
                participant = next(p for p in plan.participants if p.id == spec.id)
                outcome = spec.expected_outcome or ParticipantOutcome.COMPLETED

                if outcome is ParticipantOutcome.UNAVAILABLE:
                    participant.outcome = ParticipantOutcome.UNAVAILABLE
                    participant.reason = _REASON_PARTICIPANT_UNAVAILABLE
                    return

                # --- Parallel analysis with isolated binding-aware sessions ---
                # Each participant owns a separate DB session. Creation and the
                # binding-first claim are serialized for SQLite, while the
                # adapter execution remains concurrent and bounded by ``sem``.
                tracker.enter()
                run = Run(
                    task_id=task.id,
                    workflow_id=task.workflow_id,
                    workflow_version=task.workflow_version,
                    context_package_id=context.id,
                )
                session = session_factory()
                binding_committed = False
                try:
                    execution_service = ExecutionService(
                        session, registry=self._registry
                    )
                    run_repo = SqlRunRepository(session)

                    # Persist the CREATED identity, then use the shared
                    # binding-aware claim boundary before any adapter call.
                    async with db_lock:
                        try:
                            run_repo.add(run)
                            session.flush()
                            run, profile = execution_service.prepare_claimed_run(
                                run, task, context, workflow, commit=False
                            )
                            participant.analysis_run_id = run.id
                            tracked_run_ids.add(run.id)
                            session.commit()
                            binding_committed = True
                        except Exception:
                            session.rollback()
                            raise

                    if outcome in _OUTCOME_TO_STATE:
                        reason = {
                            ParticipantOutcome.FAILED: _REASON_PARTICIPANT_FAILED,
                            ParticipantOutcome.TIMED_OUT: _REASON_PARTICIPANT_TIMEOUT,
                            ParticipantOutcome.CANCELLED: _REASON_PARTICIPANT_CANCELLED,
                        }[outcome]
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
                        async with db_lock:
                            run_repo.update(run)
                            session.commit()
                    else:
                        try:
                            execution = await asyncio.wait_for(
                                execution_service.execute_claimed_run(
                                    run, task, context, workflow, profile
                                ),
                                timeout=self._timeout,
                            )
                        except asyncio.TimeoutError:
                            # Cleanup is not verified at this outer boundary;
                            # preserve that uncertainty as a durable ORPHANED Run.
                            self._apply_timeout_transition(
                                run, reason=_REASON_PARTICIPANT_TIMEOUT
                            )
                            participant.outcome = ParticipantOutcome.TIMED_OUT
                            participant.reason = _REASON_PARTICIPANT_TIMEOUT
                            run_repo.update(run)
                            session.commit()
                        except Exception:
                            # The shared service may have already persisted a
                            # sanitized factory failure. Reload before mapping the
                            # participant outcome so Run and Council stay aligned.
                            run = run_repo.get(run.id) or run
                            # The shared service may have durably committed a
                            # COMPLETED Run before a post-runtime boundary
                            # failure reaches this handler. Preserve that
                            # terminal result and keep the Council participant
                            # aligned; never relabel a completed Run as failed.
                            if run.state is RunState.COMPLETED:
                                participant.outcome = ParticipantOutcome.COMPLETED
                                participant.output_ref = run.id
                            else:
                                run.result = None
                                if run.state is RunState.TIMED_OUT:
                                    participant.outcome = ParticipantOutcome.TIMED_OUT
                                    participant.reason = _REASON_PARTICIPANT_TIMEOUT
                                    self._sanitize_terminal_reason(run, _REASON_PARTICIPANT_TIMEOUT)
                                elif run.state is RunState.ORPHANED:
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
                                    self._apply_sanitized_failure(run, _REASON_PARTICIPANT_FAILED)
                                    participant.outcome = ParticipantOutcome.FAILED
                                    participant.reason = _REASON_PARTICIPANT_FAILED
                            run_repo.update(run)
                            session.commit()
                        else:
                            run = execution.run
                            exec_state = run.state
                            if exec_state is RunState.COMPLETED:
                                participant.outcome = ParticipantOutcome.COMPLETED
                                participant.output_ref = run.id
                            elif exec_state is RunState.FAILED:
                                participant.outcome = ParticipantOutcome.FAILED
                                participant.reason = _REASON_PARTICIPANT_FAILED
                            elif exec_state is RunState.TIMED_OUT:
                                participant.outcome = ParticipantOutcome.TIMED_OUT
                                participant.reason = _REASON_PARTICIPANT_TIMEOUT
                            elif exec_state is RunState.CANCELLED:
                                participant.outcome = ParticipantOutcome.CANCELLED
                                participant.reason = _REASON_PARTICIPANT_CANCELLED
                            elif exec_state is RunState.ORPHANED:
                                participant.outcome = ParticipantOutcome.TIMED_OUT
                                participant.reason = _REASON_UNVERIFIED_CLEANUP
                            else:
                                participant.outcome = ParticipantOutcome.FAILED
                                participant.reason = _REASON_PARTICIPANT_FAILED
                            # The shared service already persisted the execution;
                            # this update is only defensive for the Council view.
                            run_repo.update(run)
                            session.commit()
                except asyncio.CancelledError:
                    if not binding_committed:
                        session.rollback()
                        raise
                    try:
                        run = run_repo.get(run.id) or run
                        self._apply_timeout_transition(run)
                        run.result = None
                        participant.outcome = ParticipantOutcome.TIMED_OUT
                        participant.reason = _REASON_UNVERIFIED_CLEANUP
                        run_repo.update(run)
                        session.commit()
                    except Exception:
                        session.rollback()
                        raise
                    raise
                finally:
                    session.close()
                    tracker.exit()

        # Bounded parallel execution of independent analysis. Genuine concurrent
        # scheduling (limited by ``sem``); runtime-adapter work overlaps for async
        # adapters. Persistence is serialized via ``db_lock`` for SQLite safety.
        participant_tasks = [
            asyncio.create_task(_execute_participant(spec)) for spec in specs
        ]
        try:
            await asyncio.wait_for(
                asyncio.gather(*participant_tasks),
                timeout=self._timeout * len(specs) + 10,
            )
        except BaseException:
            # A setup error in one participant must not leave sibling adapter
            # tasks or already-bound Runs active while gather unwinds.
            for participant_task in participant_tasks:
                if not participant_task.done():
                    participant_task.cancel()
            await asyncio.gather(*participant_tasks, return_exceptions=True)
            raise
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

    async def _run_cross_review_stage(
        self,
        council_run: Run,
        plan: CouncilPlan,
        bound_run_ids: set[str] | None = None,
    ) -> None:
        completed = [p for p in plan.participants if p.outcome is ParticipantOutcome.COMPLETED and p.analysis_run_id is not None]
        if len(completed) < 2:
            # Cross-review requires a distinct reviewer and target.  Do not mark
            # the stage complete when a partial Council has no valid review pair;
            # synthesis must then take its deterministic missing-input path.
            plan.partial = True
            self._persist_plan(plan)
            return
        task = self._task_repo.get(council_run.task_id)
        if task is None:
            raise ValueError("Council Task not found during cross-review execution")
        context = self._cp_repo.get(council_run.context_package_id)
        if context is None:
            raise ValueError("Council ContextPackage not found during cross-review execution")
        workflow = self._load_workflow(task)
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
                review_run, profile = self._prepare_council_stage_run(
                    review_run, council_run, bound_run_ids
                )
                review_execution = await asyncio.wait_for(
                    self._execution_service.execute_claimed_run(
                        review_run,
                        task,
                        context,
                        workflow,
                        profile,
                        fail_closed_on_factory_error=True,
                    ),
                    timeout=self._timeout,
                )
                review_run = review_execution.run
                if review_run.state is not RunState.COMPLETED:
                    raise RuntimeError("Council cross-review runtime did not complete")

                self._persist_evidence(
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

        if not any(p.cross_review_run_ids for p in completed):
            # Defensive invariant: a completed cross-review stage must contain at
            # least one durable review Run, otherwise it is not valid synthesis
            # input and must remain incomplete.
            plan.partial = True
            self._persist_plan(plan)
            return
        plan.stages_completed = plan.stages_completed + (CouncilStage.CROSS_REVIEW,)
        self._persist_plan(plan)

    # ------------------------------------------------------------------
    # Stage: synthesis (references actual evidence, truthful partial)
    # ------------------------------------------------------------------

    async def _run_synthesis_stage(
        self,
        council_run: Run,
        plan: CouncilPlan,
        bound_run_ids: set[str] | None = None,
    ) -> None:
        completed = [p for p in plan.participants if p.outcome is ParticipantOutcome.COMPLETED]
        has_cross_review = any(p.cross_review_run_ids for p in plan.participants)
        task = self._task_repo.get(council_run.task_id)
        if task is None:
            raise ValueError("Council Task not found during synthesis execution")
        context = self._cp_repo.get(council_run.context_package_id)
        if context is None:
            raise ValueError("Council ContextPackage not found during synthesis execution")
        workflow = self._load_workflow(task)

        synthesis_run = Run(
            task_id=council_run.task_id,
            workflow_id=council_run.workflow_id,
            workflow_version=council_run.workflow_version,
            context_package_id=council_run.context_package_id,
        )
        synthesis_run, profile = self._prepare_council_stage_run(
            synthesis_run, council_run, bound_run_ids
        )

        if not completed or not has_cross_review:
            # No valid synthesis inputs exist.  This is a deterministic semantic
            # rejection, not a runtime execution claim; keep the existing truthful
            # FAILED stage result and do not invoke an adapter without inputs.
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

        synthesis_execution = await asyncio.wait_for(
            self._execution_service.execute_claimed_run(
                synthesis_run,
                task,
                context,
                workflow,
                profile,
                fail_closed_on_factory_error=True,
            ),
            timeout=self._timeout,
        )
        synthesis_run = synthesis_execution.run
        if synthesis_run.state is not RunState.COMPLETED:
            raise RuntimeError("Council synthesis runtime did not complete")

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
        self._persist_evidence(evidence)
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

    def _prepare_council_stage_run(
        self,
        run: Run,
        council_run: Run,
        bound_run_ids: set[str] | None = None,
    ) -> tuple[Run, RuntimeProfile]:
        """Persist and bind a Council-owned stage Run before its transitions."""
        task = self._task_repo.get(council_run.task_id)
        if task is None:
            raise ValueError("Council Task not found while preparing a stage Run")
        context = self._cp_repo.get(council_run.context_package_id)
        if context is None:
            raise ValueError(
                "Council ContextPackage not found while preparing a stage Run"
            )
        workflow = self._load_workflow(task)
        self._run_repo.add(run)
        self._s.flush()
        if bound_run_ids is not None:
            # Track from the point the durable identity exists. If binding then
            # fails, rollback removes the Run and cleanup safely ignores it; if
            # setup fails after binding, cleanup can reconcile this child even
            # before the plan receives its stage-specific reference.
            bound_run_ids.add(run.id)
        prepared, profile = self._execution_service.prepare_claimed_run(
            run, task, context, workflow
        )
        return prepared, profile

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
        event = sanitize_event(event)
        self._run_repo.append_event(event)
        council_run.events.append(event)

    def _persist_evidence(self, evidence: Evidence) -> None:
        """Persist Council evidence only after the shared output boundary."""

        self._evidence_repo.add(sanitize_evidence(evidence))

    def _persist_plan(self, plan: CouncilPlan) -> None:
        self._persist_evidence(
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
