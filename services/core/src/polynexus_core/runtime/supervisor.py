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


@dataclass
class RunSession:
    run: Run
    runtime_ref: str


@dataclass(frozen=True)
class RunExecution:
    run: Run
    result: RunResult
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
