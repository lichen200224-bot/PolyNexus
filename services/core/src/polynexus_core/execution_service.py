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
from polynexus_core.persistence.repository import (
    ArtifactRepository,
    ContextPackageRepository,
    EvidenceRepository,
    FindingRepository,
    ProjectRepository,
    RunRepository,
    RunEventRepository,
    SqlArtifactRepository,
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlFindingRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlRunEventRepository,
    SqlTaskRepository,
    TaskRepository,
)
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.supervisor import RunExecution, RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition
from polynexus_core.workflows.models import WorkflowDefinition


_REPO_ROOT = Path(__file__).resolve().parents[4]
_BUILTIN_WORKFLOWS_DIR = _REPO_ROOT / "workflows" / "builtin"

# Allowlist: only alphanumeric, hyphen, underscore workflow IDs.
# Rejects path separators, dots, and any traversal characters.
_WORKFLOW_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class ExecutionService:
    """Thin integration layer: load entities, execute via RunSupervisor, persist results."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._project_repo: ProjectRepository = SqlProjectRepository(session)
        self._task_repo: TaskRepository = SqlTaskRepository(session)
        self._cp_repo: ContextPackageRepository = SqlContextPackageRepository(session)
        self._run_repo: RunRepository = SqlRunRepository(session)
        self._finding_repo: FindingRepository = SqlFindingRepository(session)
        self._evidence_repo: EvidenceRepository = SqlEvidenceRepository(session)
        self._artifact_repo: ArtifactRepository = SqlArtifactRepository(session)

    async def execute_task(self, task_id: str) -> RunExecution:
        """Execute a task through RunSupervisor and persist all results.

        Steps:
        1. Load Task and ContextPackage from repositories, validate same project.
        2. Load WorkflowDefinition from builtin YAML, validate task workflow reference.
        3. Execute via RunSupervisor + ReferenceRuntimeAdapter.
        4. Persist Run, RunEvents, RunResult, Finding, Evidence, Artifact through repositories.
        5. Commit and return the RunExecution.

        Raises:
            ValueError: if Task/ContextPackage mismatch, workflow mismatch, or entity not found.
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

        # 3. Execute via RunSupervisor
        adapter = ReferenceRuntimeAdapter()
        supervisor = RunSupervisor(adapter)

        session_data = await supervisor.start(task, context, workflow)
        execution = await supervisor.collect(session_data)

        # 4. Persist all results
        self._persist_execution(execution)

        # 5. Gate evaluation (post-execution, before commit)
        from polynexus_core.domain.enums import RunState as _RunState
        from polynexus_core.workflows.gates import evaluate_workflow_gates, persist_gate_report
        if execution.run.state is _RunState.COMPLETED:
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

        # 6. Commit
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

        RunSupervisor is the sole lifecycle owner for FAILED transitions.
        ExecutionService only persists the final state.

        Raises:
            RunNotFoundError: if Run does not exist.
            ResourceNotFoundError: if Task or ContextPackage not found.
            ContractViolationError: if project/workflow mismatch.
            ClaimConflictError: if CAS claim fails.
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

        # --- Phase 2: CAS claim + commit (atomic, separate transaction) ---
        claimed = self._run_repo.claim_for_execution(run_id)
        if not claimed:
            raise ClaimConflictError(
                f"Run {run_id} is not in CREATED state (current: {run.state.value})"
            )

        # Persist the CREATED→STARTING event and commit the claim
        from polynexus_core.domain.enums import RunState
        from polynexus_core.domain.models import RunEvent
        claim_event = RunEvent(
            run_id=run_id,
            from_state=RunState.CREATED,
            to_state=RunState.STARTING,
        )
        self._run_repo.append_event(claim_event)
        self._session.commit()

        # Reload the Run (now in STARTING state, with claim event committed)
        run = self._run_repo.get(run_id)
        assert run is not None

        # --- Phase 3: Execute via RunSupervisor ---
        adapter = ReferenceRuntimeAdapter()
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
