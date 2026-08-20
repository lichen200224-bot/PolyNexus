from __future__ import annotations

from dataclasses import dataclass

from polynexus_core.domain.enums import EvidenceStatus, EvidenceType, RunState
from polynexus_core.domain.models import (
    Artifact,
    ContextPackage,
    Evidence,
    Finding,
    Run,
    RunResult,
    Task,
)
from polynexus_core.runtime.contracts import RuntimeAdapter, RuntimeResult
from polynexus_core.workflows.execution import (
    ReferenceWorkflowExecutor,
    WorkflowExecutionRequest,
    WorkflowExecutor,
)
from polynexus_core.workflows.models import WorkflowDefinition


# Public-safe sanitized reason for runtime boundary failures.
# Never contains raw exception messages, vendor payloads, paths, tokens,
# or credential fragments.
_RUNTIME_FAILURE_REASON = "Runtime boundary error"


@dataclass
class RunSession:
    run: Run
    runtime_ref: str


@dataclass(frozen=True)
class RunExecution:
    run: Run
    result: RunResult | None
    findings: tuple[Finding, ...]
    evidence: tuple[Evidence, ...]
    artifacts: tuple[Artifact, ...]


class RunSupervisor:
    """Owns normalized PolyNexus Run lifecycle around an adapter boundary."""

    def __init__(
        self,
        adapter: RuntimeAdapter,
        workflow_executor: WorkflowExecutor | None = None,
    ) -> None:
        self._adapter = adapter
        self._workflow_executor = workflow_executor or ReferenceWorkflowExecutor()

    async def start(
        self,
        task: Task,
        context: ContextPackage,
        workflow: WorkflowDefinition,
    ) -> RunSession:
        if task.project_id != context.project_id:
            raise ValueError("Task and ContextPackage must belong to the same project")
        if task.workflow_id != workflow.id or task.workflow_version != workflow.version:
            raise ValueError("Task workflow reference must match the WorkflowDefinition")

        run = Run(
            task_id=task.id,
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            context_package_id=context.id,
        )
        run.transition(RunState.STARTING)
        try:
            execution = await self._workflow_executor.execute(
                WorkflowExecutionRequest(task=task, context=context, workflow=workflow),
                self._adapter,
            )
        except Exception as exc:
            run.transition(RunState.FAILED, reason=str(exc))
            raise

        run.runtime_ref = execution.runtime_ref
        run.transition(RunState.RUNNING)
        return RunSession(run=run, runtime_ref=execution.runtime_ref)

    async def execute_claimed_run(
        self,
        run: Run,
        task: Task,
        context: ContextPackage,
        workflow: WorkflowDefinition,
    ) -> RunExecution:
        """Execute a Run that was already claimed (CREATED → STARTING via CAS).

        The caller is responsible for the CAS claim and the CREATED→STARTING
        event.  This method transitions STARTING → RUNNING → terminal.

        RunSupervisor is the sole lifecycle owner — it catches runtime-boundary
        failures from the workflow executor and adapter calls, transitions to
        FAILED with a sanitized public-safe reason, and returns RunExecution
        with result=None (no fabricated Result/Evidence/Finding/Artifact).

        Programmer/domain validation errors (ValueError) are NOT caught —
        they propagate to the caller.

        On success, all adapter boundary calls (status/result/artifacts) are
        individually wrapped so a failure in one does not leave the Run in
        an inconsistent state.
        """
        if task.project_id != context.project_id:
            raise ValueError("Task and ContextPackage must belong to the same project")
        if task.workflow_id != workflow.id or task.workflow_version != workflow.version:
            raise ValueError("Task workflow reference must match the WorkflowDefinition")

        # Workflow executor boundary: create_run + submit
        try:
            execution = await self._workflow_executor.execute(
                WorkflowExecutionRequest(task=task, context=context, workflow=workflow),
                self._adapter,
            )
        except Exception:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
            return RunExecution(
                run=run,
                result=None,
                findings=(),
                evidence=(),
                artifacts=(),
            )

        run.runtime_ref = execution.runtime_ref
        run.transition(RunState.RUNNING)

        # Adapter boundary: status call
        try:
            adapter_status = await self._adapter.status(run.runtime_ref)
        except Exception:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
            return RunExecution(
                run=run,
                result=None,
                findings=(),
                evidence=(),
                artifacts=(),
            )

        if adapter_status.state in {RunState.FAILED, RunState.TIMED_OUT}:
            run.transition(adapter_status.state, reason=_RUNTIME_FAILURE_REASON)
            return RunExecution(
                run=run,
                result=None,
                findings=(),
                evidence=(),
                artifacts=(),
            )

        if adapter_status.state is RunState.ORPHANED:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
            return RunExecution(
                run=run,
                result=None,
                findings=(),
                evidence=(),
                artifacts=(),
            )

        if adapter_status.state is RunState.CANCELLED:
            run.transition(RunState.CANCEL_REQUESTED)
            run.transition(RunState.CANCELLED, reason=_RUNTIME_FAILURE_REASON)
            return RunExecution(
                run=run,
                result=None,
                findings=(),
                evidence=(),
                artifacts=(),
            )

        # Adapter boundary: result call
        try:
            runtime_result = await self._adapter.result(run.runtime_ref)
        except Exception:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
            return RunExecution(
                run=run,
                result=None,
                findings=(),
                evidence=(),
                artifacts=(),
            )

        # Adapter boundary: artifacts call
        try:
            adapter_artifacts = await self._adapter.artifacts(run.runtime_ref)
        except Exception:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
            return RunExecution(
                run=run,
                result=None,
                findings=(),
                evidence=(),
                artifacts=(),
            )

        # Guarded success preparation: fetch runtime metadata BEFORE transitioning COMPLETED
        try:
            runtime_version = self._adapter.version_info()
        except Exception:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
            return RunExecution(
                run=run,
                result=None,
                findings=(),
                evidence=(),
                artifacts=(),
            )

        run.transition(RunState.COMPLETED)
        return self._build_execution_from_existing(
            run, runtime_result, adapter_artifacts, runtime_version=runtime_version
        )

    async def execute_run(
        self,
        run: Run,
        task: Task,
        context: ContextPackage,
        workflow: WorkflowDefinition,
    ) -> RunExecution:
        """Execute an existing persisted Run through the full lifecycle.

        Unlike start(), this method uses the provided Run object instead of
        creating a new one.  It transitions CREATED → STARTING → RUNNING →
        terminal and returns the RunExecution with durable events/result.

        The caller is responsible for persisting the Run and its events.
        """
        if task.project_id != context.project_id:
            raise ValueError("Task and ContextPackage must belong to the same project")
        if task.workflow_id != workflow.id or task.workflow_version != workflow.version:
            raise ValueError("Task workflow reference must match the WorkflowDefinition")

        run.transition(RunState.STARTING)
        try:
            execution = await self._workflow_executor.execute(
                WorkflowExecutionRequest(task=task, context=context, workflow=workflow),
                self._adapter,
            )
        except Exception as exc:
            run.transition(RunState.FAILED, reason=str(exc))
            raise

        run.runtime_ref = execution.runtime_ref
        run.transition(RunState.RUNNING)

        # Collect results from the adapter
        status = await self._adapter.status(run.runtime_ref)
        if status.state in {RunState.FAILED, RunState.TIMED_OUT}:
            run.transition(status.state, reason=status.error)
            return self._build_execution_from_existing(run, RuntimeResult(summary=status.error or status.state))
        if status.state is RunState.ORPHANED:
            raise ValueError("Runtime reported ORPHANED before cancel cleanup")
        if status.state is RunState.CANCELLED:
            run.transition(RunState.CANCEL_REQUESTED)
            run.transition(RunState.CANCELLED, reason=status.error)
            return self._build_execution_from_existing(run, RuntimeResult(summary="Run cancelled"))

        runtime_result = await self._adapter.result(run.runtime_ref)
        adapter_artifacts = await self._adapter.artifacts(run.runtime_ref)
        run.transition(RunState.COMPLETED)
        return self._build_execution_from_existing(run, runtime_result, adapter_artifacts)

    async def collect(self, session: RunSession) -> RunExecution:
        self._require_active(session)
        status = await self._adapter.status(session.runtime_ref)
        if status.state in {RunState.FAILED, RunState.TIMED_OUT}:
            session.run.transition(status.state, reason=status.error)
            return self._build_execution(session, RuntimeResult(summary=status.error or status.state))
        if status.state is RunState.ORPHANED:
            raise ValueError("Runtime reported ORPHANED before cancel cleanup")
        if status.state is RunState.CANCELLED:
            session.run.transition(RunState.CANCEL_REQUESTED)
            session.run.transition(RunState.CANCELLED, reason=status.error)
            return self._build_execution(session, RuntimeResult(summary="Run cancelled"))

        runtime_result = await self._adapter.result(session.runtime_ref)
        adapter_artifacts = await self._adapter.artifacts(session.runtime_ref)
        session.run.transition(RunState.COMPLETED)
        return self._build_execution(session, runtime_result, adapter_artifacts)

    async def cancel(self, session: RunSession) -> RunExecution:
        self._require_active(session)
        session.run.transition(RunState.CANCEL_REQUESTED)
        await self._adapter.cancel(session.runtime_ref)
        cleanup_ok = await self._adapter.cleanup(session.runtime_ref)
        status = await self._adapter.status(session.runtime_ref)
        if cleanup_ok and status.state is RunState.CANCELLED:
            session.run.transition(RunState.CANCELLED, reason="cancelled and cleanup verified")
            summary = "Run cancelled and cleanup verified"
        else:
            session.run.transition(
                RunState.ORPHANED,
                reason="runtime cleanup verification failed",
            )
            summary = "Run orphaned because cleanup verification failed"
        return self._build_execution(session, RuntimeResult(summary=summary))

    def _require_active(self, session: RunSession) -> None:
        if session.run.state is not RunState.RUNNING:
            raise ValueError(f"Run is not active: {session.run.state}")

    def _build_execution_from_existing(
        self,
        run: Run,
        runtime_result: RuntimeResult,
        adapter_artifacts: tuple[Artifact, ...] = (),
        runtime_version: str | None = None,
    ) -> RunExecution:
        """Build RunExecution for an existing Run (not wrapped in RunSession)."""
        if runtime_version is None:
            runtime_version = self._adapter.version_info()
        evidence = list(runtime_result.evidence)
        evidence_status = (
            EvidenceStatus.PASS
            if run.state in {RunState.COMPLETED, RunState.CANCELLED}
            else EvidenceStatus.FAIL
        )
        evidence.append(
            Evidence(
                task_id=run.task_id,
                run_id=run.id,
                actor_id="system:run-supervisor",
                source="runtime-adapter",
                type=EvidenceType.RUNTIME_EVIDENCE,
                status=evidence_status,
                metadata={"runtime_version": runtime_version},
            )
        )
        artifacts = tuple(runtime_result.artifacts) + tuple(
            artifact
            for artifact in adapter_artifacts
            if artifact.id not in {item.id for item in runtime_result.artifacts}
        )
        result = RunResult(
            run_id=run.id,
            status=run.state,
            summary=runtime_result.summary,
            finding_ids=tuple(finding.id for finding in runtime_result.findings),
            evidence_ids=tuple(item.id for item in evidence),
            artifact_ids=tuple(artifact.id for artifact in artifacts),
        )
        run.result = result
        return RunExecution(
            run=run,
            result=result,
            findings=runtime_result.findings,
            evidence=tuple(evidence),
            artifacts=artifacts,
        )

    def _build_execution(
        self,
        session: RunSession,
        runtime_result: RuntimeResult,
        adapter_artifacts: tuple[Artifact, ...] = (),
    ) -> RunExecution:
        evidence = list(runtime_result.evidence)
        evidence_status = (
            EvidenceStatus.PASS
            if session.run.state in {RunState.COMPLETED, RunState.CANCELLED}
            else EvidenceStatus.FAIL
        )
        evidence.append(
            Evidence(
                task_id=session.run.task_id,
                run_id=session.run.id,
                actor_id="system:run-supervisor",
                source="runtime-adapter",
                type=EvidenceType.RUNTIME_EVIDENCE,
                status=evidence_status,
                metadata={"runtime_version": self._adapter.version_info()},
            )
        )
        artifacts = tuple(runtime_result.artifacts) + tuple(
            artifact
            for artifact in adapter_artifacts
            if artifact.id not in {item.id for item in runtime_result.artifacts}
        )
        result = RunResult(
            run_id=session.run.id,
            status=session.run.state,
            summary=runtime_result.summary,
            finding_ids=tuple(finding.id for finding in runtime_result.findings),
            evidence_ids=tuple(item.id for item in evidence),
            artifact_ids=tuple(artifact.id for artifact in artifacts),
        )
        session.run.result = result
        return RunExecution(
            run=session.run,
            result=result,
            findings=runtime_result.findings,
            evidence=tuple(evidence),
            artifacts=artifacts,
        )
