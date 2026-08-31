"""G15 output-redaction gate tests.

These tests exercise the shared boundary at both the runtime/persistence edge
and the read-only API serializers.  They intentionally use secret markers,
absolute paths, and oversized values to prove that raw values do not cross the
public or durable output surfaces.
"""

from __future__ import annotations

import asyncio

import pytest

from polynexus_core.api.run_outputs import (
    _artifact_to_response,
    _evidence_to_response,
    _event_to_response,
    _finding_to_response,
)
from polynexus_core.api.runs import _run_to_response
from polynexus_core.domain.enums import (
    ArtifactType,
    EvidenceType,
    FindingSeverity,
    RunState,
)
from polynexus_core.domain.models import (
    Artifact,
    ContextPackage,
    Evidence,
    Finding,
    Run,
    RunEvent,
    RunResult,
    Task,
)
from polynexus_core.execution_service import ExecutionService
from polynexus_core.runtime.contracts import RuntimeResult
from polynexus_core.runtime.redaction import (
    MAX_TEXT_LENGTH,
    PATH_REDACTED,
    REDACTED,
    TRUNCATED,
    redact_text,
    redact_value,
)
from polynexus_core.runtime.supervisor import RunSession, RunSupervisor
from polynexus_core.workflows.execution import RuntimeExecution
from polynexus_core.workflows.models import WorkflowDefinition, WorkflowStep


SECRET = "SECRET_MARKER_G15_opaque_value"
SECRET_PATH = r"C:\private\credential\secret.key"


class _VersionAdapter:
    def version_info(self) -> str:
        return f"runtime-version token={SECRET} {SECRET_PATH}"


class _RaisingExecutor:
    async def execute(self, request, runtime) -> RuntimeExecution:
        raise RuntimeError(f"vendor failure token={SECRET} path={SECRET_PATH}")


def _inputs() -> tuple[Task, ContextPackage, WorkflowDefinition]:
    task = Task(
        project_id="project_g15",
        title="G15",
        workflow_id="review-minimal",
        workflow_version=1,
    )
    context = ContextPackage(project_id=task.project_id, version=1)
    workflow = WorkflowDefinition(
        id=task.workflow_id,
        version=task.workflow_version,
        steps=(WorkflowStep(id="step-1", type="TOOL"),),
    )
    return task, context, workflow


def _raw_outputs(run_id: str) -> tuple[Finding, Evidence, Artifact]:
    finding = Finding(
        task_id="task_g15",
        run_id=run_id,
        title=f"Finding token={SECRET}",
        description=f"Failure at {SECRET_PATH}; {SECRET}",
        severity=FindingSeverity.HIGH,
        evidence_refs=(SECRET_PATH,),
    )
    evidence = Evidence(
        task_id="task_g15",
        run_id=run_id,
        actor_id=f"actor-{SECRET}",
        source=f"vendor://{SECRET}",
        type=EvidenceType.RUNTIME_EVIDENCE,
        metadata={
            "secret": SECRET,
            "nested": {"path": SECRET_PATH},
            "oversized": "x" * (MAX_TEXT_LENGTH + 100),
        },
    )
    artifact = Artifact(
        project_id="project_g15",
        task_id="task_g15",
        run_id=run_id,
        artifact_type=ArtifactType.REPORT,
        mime_type="text/plain",
        source_type="vendor",
        storage_ref=SECRET_PATH,
        sha256="a" * 64,
    )
    return finding, evidence, artifact


def test_redaction_masks_secrets_paths_and_bounds_text() -> None:
    raw = f"token={SECRET} path={SECRET_PATH} " + ("x" * MAX_TEXT_LENGTH)
    safe = redact_text(raw)

    assert SECRET not in safe
    assert SECRET_PATH not in safe
    assert PATH_REDACTED in safe
    assert TRUNCATED in safe
    assert len(safe) <= MAX_TEXT_LENGTH


def test_redaction_bounds_nested_metadata() -> None:
    raw = {str(i): {"secret": SECRET} for i in range(100)}
    safe = redact_value(raw)
    rendered = repr(safe)

    assert isinstance(safe, dict)
    assert SECRET not in rendered
    assert len(safe) == 65  # 64 bounded entries plus the truncation marker
    assert safe[TRUNCATED] == TRUNCATED


def test_supervisor_does_not_rethrow_raw_exception_text() -> None:
    task, context, workflow = _inputs()
    supervisor = RunSupervisor(_VersionAdapter(), workflow_executor=_RaisingExecutor())
    run = Run(
        task_id=task.id,
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        context_package_id=context.id,
    )

    with pytest.raises(RuntimeError, match="Runtime boundary error"):
        asyncio.run(supervisor.execute_run(run, task, context, workflow))

    assert run.state is RunState.FAILED
    assert SECRET not in repr(run.events)
    assert SECRET_PATH not in repr(run.events)
    assert run.events[-1].reason == "Runtime boundary error"


def test_supervisor_builder_sanitizes_runtime_result_and_adapter_version() -> None:
    task, context, workflow = _inputs()
    run = Run(
        task_id=task.id,
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        context_package_id=context.id,
    )
    finding, evidence, artifact = _raw_outputs(run.id)
    runtime_result = RuntimeResult(
        summary=f"summary token={SECRET} path={SECRET_PATH}",
        findings=(finding,),
        evidence=(evidence,),
        artifacts=(artifact,),
    )

    execution = RunSupervisor(_VersionAdapter())._build_execution(
        RunSession(run=run, runtime_ref="runtime-ref"), runtime_result
    )
    rendered = repr(execution)

    assert SECRET not in rendered
    assert SECRET_PATH not in rendered
    assert len(execution.result.summary) <= MAX_TEXT_LENGTH
    assert execution.evidence[0].metadata["secret"] == REDACTED
    assert execution.artifacts[0].storage_ref == PATH_REDACTED


def test_execution_service_boundary_sanitizes_direct_execution() -> None:
    task, context, workflow = _inputs()
    run = Run(
        task_id=task.id,
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        context_package_id=context.id,
    )
    finding, evidence, artifact = _raw_outputs(run.id)
    result = RunResult(
        run_id=run.id,
        status=RunState.COMPLETED,
        summary=f"result token={SECRET} path={SECRET_PATH}",
        finding_ids=(finding.id,),
        evidence_ids=(evidence.id,),
        artifact_ids=(artifact.id,),
    )
    from polynexus_core.runtime.supervisor import RunExecution

    execution = RunExecution(
        run=run,
        result=result,
        findings=(finding,),
        evidence=(evidence,),
        artifacts=(artifact,),
    )

    safe = ExecutionService._sanitize_execution(execution)

    assert SECRET not in repr(safe)
    assert SECRET_PATH not in repr(safe)
    assert safe.result is not None
    assert safe.result.summary != result.summary
    assert safe.evidence[0].metadata["secret"] == REDACTED


def test_all_api_output_serializers_redact_untrusted_fields() -> None:
    run = Run(
        task_id="task_g15",
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id="context_g15",
        runtime_ref=f"runtime:{SECRET_PATH}",
    )
    run.events.append(
        RunEvent(
            run_id=run.id,
            from_state=RunState.CREATED,
            to_state=RunState.FAILED,
            reason=f"vendor token={SECRET} path={SECRET_PATH}",
        )
    )
    run.result = RunResult(
        run_id=run.id,
        status=RunState.FAILED,
        summary=f"vendor token={SECRET} path={SECRET_PATH}",
    )
    finding, evidence, artifact = _raw_outputs(run.id)

    payloads = [
        _run_to_response(run).model_dump(mode="json"),
        _finding_to_response(finding).model_dump(mode="json"),
        _evidence_to_response(evidence).model_dump(mode="json"),
        _artifact_to_response(artifact).model_dump(mode="json"),
        _event_to_response(run.events[0]).model_dump(mode="json"),
    ]
    rendered = repr(payloads)

    assert SECRET not in rendered
    assert SECRET_PATH not in rendered
    assert PATH_REDACTED in rendered
