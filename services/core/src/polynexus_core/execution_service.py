"""Minimal integration service — executes a Task through RunSupervisor and persists results.

This is a thin orchestration layer that connects:
- Repository layer (persistence) for loading Task/ContextPackage and saving results
- Workflow loader for loading WorkflowDefinition
- RunSupervisor + ReferenceRuntimeAdapter for execution

It does NOT own Domain logic, persistence schema, or runtime adapter internals.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from sqlalchemy.orm import Session

from polynexus_core.errors import (
    ClaimConflictError,
    ContractViolationError,
    ResourceNotFoundError,
    RunNotFoundError,
)
from polynexus_core.domain.models import (
    ContextPackage,
    Finding,
    Evidence,
    Project,
    Task,
    Run,
    RunResult,
)
from polynexus_core.domain.runtime_binding import RuntimeBindingError
from polynexus_core.persistence.repository import (
    ArtifactRepository,
    ContextPackageRepository,
    EvidenceRepository,
    FindingRepository,
    ProjectRepository,
    RunRepository,
    RunEventRepository,
    RuntimeBindingSnapshotRepository,
    SqlArtifactRepository,
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlFindingRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlRunEventRepository,
    SqlRuntimeBindingSnapshotRepository,
    SqlTaskRepository,
    TaskRepository,
)
from polynexus_core.runtime.registry import (
    REFERENCE_PROFILE_REF,
    RuntimeProfile,
    RuntimeRegistry,
    build_default_registry,
)
from polynexus_core.runtime.supervisor import RunExecution, RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition
from polynexus_core.workflows.models import WorkflowDefinition


_REPO_ROOT = Path(__file__).resolve().parents[4]
_BUILTIN_WORKFLOWS_DIR = _REPO_ROOT / "workflows" / "builtin"

# Allowlist: only alphanumeric, hyphen, underscore workflow IDs.
# Rejects path separators, dots, and any traversal characters.
_WORKFLOW_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# Public-safe sanitized reason for adapter factory construction failure after
# the binding-first transaction committed. Never contains raw exception
# messages, vendor payloads, paths, tokens, or credential fragments.
_ADAPTER_CONSTRUCTION_FAILURE_REASON = "Runtime adapter construction failed"


class ExecutionService:
    """Thin integration layer: load entities, execute via RunSupervisor, persist results."""

    def __init__(self, session: Session, registry: RuntimeRegistry | None = None) -> None:
        self._session = session
        self._project_repo: ProjectRepository = SqlProjectRepository(session)
        self._task_repo: TaskRepository = SqlTaskRepository(session)
        self._cp_repo: ContextPackageRepository = SqlContextPackageRepository(session)
        self._run_repo: RunRepository = SqlRunRepository(session)
        self._finding_repo: FindingRepository = SqlFindingRepository(session)
        self._evidence_repo: EvidenceRepository = SqlEvidenceRepository(session)
        self._artifact_repo: ArtifactRepository = SqlArtifactRepository(session)
        self._binding_repo: RuntimeBindingSnapshotRepository = (
            SqlRuntimeBindingSnapshotRepository(session)
        )
        # Composition-root injectable; default registers only reference.local.
        self._registry: RuntimeRegistry = registry or build_default_registry()

    def prepare_claimed_run(
        self,
        run: Run,
        task: Task,
        context: ContextPackage,
        workflow: WorkflowDefinition,
        *,
        commit: bool = True,
    ) -> tuple[Run, RuntimeProfile]:
        """Claim and bind a persisted Run before any adapter invocation.

        This is the shared binding-aware boundary used by Council-created Runs.
        The caller must persist the CREATED Run first. Validation, the CAS
        claim, the CREATED->STARTING event, and the immutable snapshot are
        committed atomically before the caller can invoke a runtime adapter.
        Callers that already own a larger transaction may pass ``commit=False``;
        the claim and immutable binding remain in that transaction and the
        caller must commit before invoking an adapter.
        """
        from polynexus_core.domain.enums import RunState
        from polynexus_core.domain.models import RunEvent

        if task.project_id != context.project_id:
            raise ContractViolationError(
                "Task and ContextPackage must belong to the same project"
            )
        if task.workflow_id != workflow.id or task.workflow_version != workflow.version:
            raise ContractViolationError(
                "Task workflow reference must match the WorkflowDefinition"
            )
        if (
            run.task_id != task.id
            or run.context_package_id != context.id
            or run.workflow_id != workflow.id
            or run.workflow_version != workflow.version
        ):
            raise ContractViolationError(
                "Run references do not match the Task, ContextPackage, and WorkflowDefinition"
            )

        try:
            # Resolve before the CAS claim so an unknown/unavailable profile leaves
            # the CREATED Run untouched. The rollback guard also covers callers
            # that flushed that identity in a larger transaction.
            profile = self._registry.resolve(REFERENCE_PROFILE_REF)
            if not self._run_repo.claim_for_execution(run.id):
                raise ClaimConflictError(
                    f"Run {run.id} is not in CREATED state (current: {run.state.value})"
                )

            claim_event = RunEvent(
                run_id=run.id,
                from_state=RunState.CREATED,
                to_state=RunState.STARTING,
            )
            self._run_repo.append_event(claim_event)
            self._binding_repo.insert_once(
                self._registry.bind(
                    REFERENCE_PROFILE_REF,
                    run_id=run.id,
                    resolved_at=claim_event.occurred_at,
                )
            )
        except Exception:
            self._session.rollback()
            raise
        if commit:
            self._session.commit()

        stored = self._run_repo.get(run.id)
        assert stored is not None
        return stored, profile

    async def execute_claimed_run(
        self,
        run: Run,
        task: Task,
        context: ContextPackage,
        workflow: WorkflowDefinition,
        profile: RuntimeProfile,
        *,
        fail_closed_on_factory_error: bool = False,
    ) -> RunExecution:
        """Execute a Run prepared by :meth:`prepare_claimed_run`.

        The binding snapshot must already exist. This method is deliberately
        separate from preparation so deterministic Council outcomes can bind a
        Run without invoking an adapter, while real analysis stages use the
        same Registry -> Adapter -> Supervisor path as normal execution.
        """
        from polynexus_core.domain.enums import RunState
        from polynexus_core.workflows.gates import (
            evaluate_workflow_gates,
            persist_gate_report,
        )

        if run.state is not RunState.STARTING:
            raise ClaimConflictError(
                "Claimed Run must be in STARTING state before adapter execution"
            )
        if self._binding_repo.get_by_run(run.id) is None:
            raise RuntimeBindingError(
                "Claimed Run has no immutable runtime binding"
            )

        adapter = self._construct_adapter_or_fail_closed(
            run.id,
            profile,
            orphan_on_failure=fail_closed_on_factory_error,
        )
        supervisor = RunSupervisor(adapter)
        execution = await supervisor.execute_claimed_run(
            run, task, context, workflow
        )

        self._run_repo.update(execution.run)
        if execution.result is not None:
            for finding in execution.findings:
                self._finding_repo.add(finding)
            for evidence in execution.evidence:
                self._evidence_repo.add(evidence)
            for artifact in execution.artifacts:
                self._artifact_repo.add(artifact)

        if execution.run.state is RunState.COMPLETED:
            gate_report = evaluate_workflow_gates(
                workflow, task, execution.run, self._evidence_repo
            )
            gate_ev = persist_gate_report(gate_report, self._evidence_repo)
            all_evidence = list(execution.evidence) + [gate_ev]
            new_result = RunResult(
                run_id=execution.result.run_id,
                status=execution.result.status,
                summary=execution.result.summary,
                finding_ids=execution.result.finding_ids,
                evidence_ids=tuple(e.id for e in all_evidence),
                artifact_ids=execution.result.artifact_ids,
            ) if execution.result is not None else None
            execution.run.result = new_result
            self._run_repo.update(execution.run)
            execution = RunExecution(
                run=execution.run,
                result=new_result,
                findings=execution.findings,
                evidence=tuple(all_evidence),
                artifacts=execution.artifacts,
            )

        self._session.commit()
        return execution

    async def execute_task(self, task_id: str) -> RunExecution:
        """Execute a task through RunSupervisor and persist all results.

        Binding-first transaction boundary (PRE-WP14-B):
          1. Load and validate Task / ContextPackage / workflow.
          2. Resolve the RuntimeProfile via the Registry (fail closed).
          3. ONE atomic transaction: new CREATED Run identity + immutable
             RuntimeBindingSnapshot insert_once + CREATED→STARTING event,
             committed BEFORE any adapter invocation.
          4. Execute via RunSupervisor (starting from STARTING state).
          5. Persist all runtime outputs, evaluate gates, commit.

        If binding/event persistence fails, the whole transaction rolls back:
        no half-created Run, no orphan snapshot, and the adapter is never
        invoked.

        Raises:
            ValueError: if Task/ContextPackage mismatch, workflow mismatch, or entity not found.
            RuntimeBindingError: if registry resolution or binding fails.
        """
        # 1. Load Task and ContextPackage
        task = self._task_repo.get(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        if task.context_package_id is None:
            raise ValueError(f"Task {task_id} has no ContextPackage")

        context = self._cp_repo.get(task.context_package_id)
        if context is None:
            raise ValueError(f"ContextPackage {task.context_package_id} not found")

        if task.project_id != context.project_id:
            raise ValueError("Task and ContextPackage belong to different projects")

        # 2. Load WorkflowDefinition from builtin YAML
        workflow = self._load_workflow(task.workflow_id, task.workflow_version)

        # 2b. Resolve the RuntimeProfile via the Registry — fail closed before
        # any Run identity or adapter work happens.
        profile = self._registry.resolve(REFERENCE_PROFILE_REF)

        # 3. Binding-first atomic transaction: Run identity + snapshot +
        #    STARTING event committed together BEFORE adapter execution.
        from polynexus_core.domain.enums import RunState
        from polynexus_core.domain.models import RunEvent

        run = Run(
            task_id=task.id,
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            context_package_id=context.id,
        )
        self._run_repo.add(run)
        # Claim the freshly created Run identity (CREATED -> STARTING) inside
        # the same binding-first transaction.
        if not self._run_repo.claim_for_execution(run.id):
            raise RuntimeError("Failed to claim the newly created Run identity")
        claim_event = RunEvent(
            run_id=run.id,
            from_state=RunState.CREATED,
            to_state=RunState.STARTING,
        )
        try:
            self._run_repo.append_event(claim_event)
            self._binding_repo.insert_once(
                self._registry.bind(
                    REFERENCE_PROFILE_REF,
                    run_id=run.id,
                    resolved_at=claim_event.occurred_at,
                )
            )
        except Exception:
            self._session.rollback()
            raise
        self._session.commit()

        # 4. Execute via RunSupervisor with the Registry-resolved adapter.
        # The Run is reloaded in its claimed STARTING state.
        adapter = self._construct_adapter_or_fail_closed(run.id, profile)
        supervisor = RunSupervisor(adapter)

        stored_run = self._run_repo.get(run.id)
        assert stored_run is not None

        execution = await supervisor.execute_claimed_run(
            stored_run, task, context, workflow
        )

        # 5. Persist runtime outputs. The Run identity was already persisted
        # and committed in the binding-first transaction (step 3) — update it
        # instead of re-adding, and only persist real adapter outputs.
        self._run_repo.update(execution.run)
        for finding in execution.findings:
            self._finding_repo.add(finding)
        for evidence in execution.evidence:
            self._evidence_repo.add(evidence)
        for artifact in execution.artifacts:
            self._artifact_repo.add(artifact)

        # 6. Gate evaluation (post-execution, before commit)
        from polynexus_core.workflows.gates import evaluate_workflow_gates, persist_gate_report
        if execution.run.state is RunState.COMPLETED:
            gate_report = evaluate_workflow_gates(
                workflow, task, execution.run, self._evidence_repo
            )
            gate_ev = persist_gate_report(gate_report, self._evidence_repo)
            gate_evidence = [gate_ev]
            all_evidence = list(execution.evidence) + gate_evidence
            new_result = RunResult(
                run_id=execution.result.run_id,
                status=execution.result.status,
                summary=execution.result.summary,
                finding_ids=execution.result.finding_ids,
                evidence_ids=tuple(e.id for e in all_evidence),
                artifact_ids=execution.result.artifact_ids,
            ) if execution.result is not None else None
            # Update the persisted Run with gate evidence in RunResult.
            execution.run.result = new_result
            self._run_repo.update(execution.run)
            execution = RunExecution(
                run=execution.run,
                result=new_result,
                findings=execution.findings,
                evidence=tuple(all_evidence),
                artifacts=execution.artifacts,
            )

        # 7. Commit — the binding snapshot was already persisted and committed
        # in the binding-first transaction (step 3), before adapter execution.
        self._session.commit()

        return execution

    async def execute_existing_run(self, run_id: str) -> RunExecution:
        """Execute an existing persisted Run through the full lifecycle.

        Flow:
          1. Load and validate all references (no CAS yet).
          2. CAS claim: CREATED → STARTING, commit immediately.
          3. Execute via RunSupervisor (starting from STARTING state).
          4. Persist all runtime outputs.

        The CAS claim and the CREATED→STARTING event are committed in the
        same atomic transaction BEFORE the runtime adapter is invoked.
        Validation happens before the claim so no adapter work is wasted
        on an invalid Run.

        Lifecycle failure ownership is split:
        - RunSupervisor owns lifecycle failures at the adapter EXECUTION
          boundary: it catches runtime-boundary exceptions and transitions
          to FAILED with a sanitized reason.
        - ExecutionService owns adapter FACTORY CONSTRUCTION failure after
          the binding-first commit: `_construct_adapter_or_fail_closed()`
          legally transitions STARTING -> FAILED with a sanitized constant
          reason/event, commits, and raises a sanitized RuntimeBindingError.

        Raises:
            RunNotFoundError: if Run does not exist.
            ResourceNotFoundError: if Task or ContextPackage not found.
            ContractViolationError: if project/workflow mismatch.
            ClaimConflictError: if CAS claim fails.
            RuntimeBindingError: if registry resolution fails before the claim,
                binding persistence fails (transaction rolls back), or adapter
                factory construction fails after the claim (Run is recovered
                to FAILED).
        """
        # --- Phase 1: Validate all references (no CAS yet) ---
        run = self._run_repo.get(run_id)
        if run is None:
            raise RunNotFoundError(f"Run {run_id} not found")

        task = self._task_repo.get(run.task_id)
        if task is None:
            raise ResourceNotFoundError(f"Task {run.task_id} not found")

        context = self._cp_repo.get(run.context_package_id)
        if context is None:
            raise ResourceNotFoundError(f"ContextPackage {run.context_package_id} not found")

        if task.project_id != context.project_id:
            raise ContractViolationError("Task and ContextPackage belong to different projects")

        if run.workflow_id != task.workflow_id or run.workflow_version != task.workflow_version:
            raise ContractViolationError("Run workflow reference does not match Task workflow")

        workflow = self._load_workflow(run.workflow_id, run.workflow_version)

        # --- Phase 1b: Resolve the RuntimeProfile via the Registry ---
        # Fail closed BEFORE any CAS claim or adapter work: an unknown or
        # unavailable profile must leave the Run untouched (still CREATED).
        profile = self._registry.resolve(REFERENCE_PROFILE_REF)

        # --- Phase 2: CAS claim + immutable binding + STARTING event ---
        # All three happen in ONE transaction committed atomically BEFORE the
        # runtime adapter is invoked. Any failure rolls back the whole
        # transaction — no claimed Run without a binding snapshot can exist,
        # and no adapter is started after a rollback.
        claimed = self._run_repo.claim_for_execution(run_id)
        if not claimed:
            raise ClaimConflictError(
                f"Run {run_id} is not in CREATED state (current: {run.state.value})"
            )

        from polynexus_core.domain.enums import RunState
        from polynexus_core.domain.models import RunEvent
        claim_event = RunEvent(
            run_id=run_id,
            from_state=RunState.CREATED,
            to_state=RunState.STARTING,
        )
        try:
            self._run_repo.append_event(claim_event)
            # Bind before execution: resolved_at is the deterministic
            # CREATED→STARTING claim event timestamp; rebinding a Run is
            # rejected by insert_once.
            self._binding_repo.insert_once(
                self._registry.bind(
                    REFERENCE_PROFILE_REF,
                    run_id=run_id,
                    resolved_at=claim_event.occurred_at,
                )
            )
        except Exception:
            self._session.rollback()
            raise
        self._session.commit()

        # Reload the Run (now in STARTING state, with claim event committed)
        run = self._run_repo.get(run_id)
        assert run is not None

        # --- Phase 3: Execute via RunSupervisor ---
        # Adapter comes from the Registry (no vendor-specific Core branch).
        adapter = self._construct_adapter_or_fail_closed(run.id, profile)
        supervisor = RunSupervisor(adapter)

        # Supervisor is the sole lifecycle owner — it catches runtime-boundary
        # failures internally, transitions to FAILED with sanitized reason,
        # and returns RunExecution with result=None on failure.
        # Programmer/domain validation errors (ValueError) propagate to caller.
        execution = await supervisor.execute_claimed_run(run, task, context, workflow)

        # --- Phase 4: Persist runtime outputs ---
        # Always persist the Run state and events.
        self._run_repo.update(execution.run)

        # Only persist Finding/Evidence/Artifact when runtime produced a real result.
        # When result is None, the runtime failed before producing outputs —
        # do not fabricate any Finding/Evidence/Artifact.
        if execution.result is not None:
            for finding in execution.findings:
                self._finding_repo.add(finding)
            for evidence in execution.evidence:
                self._evidence_repo.add(evidence)
            for artifact in execution.artifacts:
                self._artifact_repo.add(artifact)

        # --- Phase 5: Gate evaluation (post-execution) ---
        # Evaluate deterministic gates and persist the gate report as
        # DOCUMENT_EVIDENCE. This is an additive evaluation layer that does
        # not alter the Run state or lifecycle events.
        # Only evaluate on COMPLETED runs — terminal failed runs cannot
        # produce PASS, and gate evaluation is not needed for the failure path.
        # Gate evidence is included in RunResult.evidence_ids for exact parity.
        from polynexus_core.domain.enums import RunState as _RunState
        from polynexus_core.workflows.gates import evaluate_workflow_gates, persist_gate_report
        if execution.run.state is _RunState.COMPLETED:
            gate_report = evaluate_workflow_gates(
                workflow, task, execution.run, self._evidence_repo
            )
            gate_ev = persist_gate_report(gate_report, self._evidence_repo)
            # Rebuild RunResult to include gate evidence in evidence_ids.
            gate_evidence = [gate_ev]
            all_evidence = list(execution.evidence) + gate_evidence
            execution = RunExecution(
                run=execution.run,
                result=RunResult(
                    run_id=execution.result.run_id,
                    status=execution.result.status,
                    summary=execution.result.summary,
                    finding_ids=execution.result.finding_ids,
                    evidence_ids=tuple(e.id for e in all_evidence),
                    artifact_ids=execution.result.artifact_ids,
                ) if execution.result is not None else None,
                findings=execution.findings,
                evidence=tuple(all_evidence),
                artifacts=execution.artifacts,
            )
            # Persist the updated RunResult to the database so the API
            # returns result.evidence_ids with gate evidence included.
            if execution.result is not None:
                execution.run.result = execution.result
                self._run_repo.update(execution.run)

        self._session.commit()

        return execution

    def _construct_adapter_or_fail_closed(
        self,
        run_id: str,
        profile: RuntimeProfile,
        *,
        orphan_on_failure: bool = False,
    ) -> object:
        """Construct the adapter for a claimed Run; fail closed on factory error.

        The binding-first transaction is already committed at this point, so a
        factory construction failure must NOT leave the Run stuck in STARTING.
        Council-owned Runs can request STARTING -> CANCEL_REQUESTED -> ORPHANED
        because adapter cleanup is unverified; the established normal execution
        path retains its sanitized FAILED mapping.
        """
        from polynexus_core.domain.enums import RunState

        try:
            return self._registry.create_adapter(profile)
        except Exception:
            stored = self._run_repo.get(run_id)
            assert stored is not None
            if orphan_on_failure:
                stored.transition(
                    RunState.CANCEL_REQUESTED,
                    reason=_ADAPTER_CONSTRUCTION_FAILURE_REASON,
                )
                stored.transition(
                    RunState.ORPHANED,
                    reason=_ADAPTER_CONSTRUCTION_FAILURE_REASON,
                )
            else:
                stored.transition(
                    RunState.FAILED, reason=_ADAPTER_CONSTRUCTION_FAILURE_REASON
                )
            self._run_repo.update(stored)
            self._session.commit()
            raise RuntimeBindingError(
                _ADAPTER_CONSTRUCTION_FAILURE_REASON
            ) from None

    def _persist_run_update(self, execution: RunExecution) -> None:
        """Persist updated Run, Evidence, Finding, Artifact through repositories."""
        # Update the Run (state, events, result)
        self._run_repo.update(execution.run)

        # Persist Finding
        for finding in execution.findings:
            self._finding_repo.add(finding)

        # Persist Evidence
        for evidence in execution.evidence:
            self._evidence_repo.add(evidence)

        # Persist Artifact
        for artifact in execution.artifacts:
            self._artifact_repo.add(artifact)

    def _load_workflow(self, workflow_id: str, workflow_version: int) -> WorkflowDefinition:
        """Load a workflow from builtin YAML and validate it matches the task reference.

        Security: workflow_id is validated against an allowlist pattern and the resolved
        path must remain within the builtin workflows directory (no traversal).
        """
        workflow_path = self._check_workflow_path_containment(workflow_id)

        if not workflow_path.exists():
            raise ValueError(f"Workflow definition not found: {workflow_id}")

        workflow = load_workflow_definition(workflow_path)

        if workflow.id != workflow_id:
            raise ValueError(f"Workflow id mismatch: expected {workflow_id}, got {workflow.id}")
        if workflow.version != workflow_version:
            raise ValueError(
                f"Workflow version mismatch: expected {workflow_version}, got {workflow.version}"
            )

        return workflow

    @staticmethod
    def _check_workflow_path_containment(workflow_id: str) -> Path:
        """Validate workflow_id format and resolve path containment.

        Returns the resolved workflow path if containment passes.
        Raises ValueError if the workflow_id fails regex validation or path containment.

        This is the production security logic — tests should call this method
        (or _load_workflow) rather than duplicating Path.is_relative_to().
        """
        if not _WORKFLOW_ID_PATTERN.match(workflow_id):
            raise ValueError(
                f"Invalid workflow_id format: {workflow_id!r}. "
                "Workflow IDs must contain only alphanumeric, hyphen, or underscore characters."
            )

        workflow_path = (_BUILTIN_WORKFLOWS_DIR / f"{workflow_id}.yaml").resolve()

        if not workflow_path.is_relative_to(_BUILTIN_WORKFLOWS_DIR.resolve()):
            raise ValueError(
                f"Workflow path traversal rejected: {workflow_id!r} resolves outside builtin directory."
            )

        return workflow_path

    def _persist_execution(self, execution: RunExecution) -> None:
        """Persist Run, RunEvents, RunResult, Finding, Evidence, Artifact through repositories."""
        # Persist the Run (includes state and events)
        self._run_repo.add(execution.run)

        # Persist Finding (ReferenceRuntimeAdapter produces no findings, but persist if present)
        for finding in execution.findings:
            self._finding_repo.add(finding)

        # Persist Evidence (RunSupervisor always produces RUNTIME_EVIDENCE)
        for evidence in execution.evidence:
            self._evidence_repo.add(evidence)

        # Persist Artifact (ReferenceRuntimeAdapter produces none, but persist if present)
        for artifact in execution.artifacts:
            self._artifact_repo.add(artifact)
