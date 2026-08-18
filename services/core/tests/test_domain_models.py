from polynexus_core.domain.enums import (
    ArtifactType,
    EvidenceStatus,
    EvidenceType,
    FindingSeverity,
    FindingStatus,
    RunState,
    WorkMode,
)
from polynexus_core.domain.models import (
    Artifact,
    ContextPackage,
    Evidence,
    Finding,
    Project,
    Run,
    Task,
)


def test_fvs_entities_use_stable_ids_and_structured_context() -> None:
    project = Project(name="Review project")
    context = ContextPackage(
        project_id=project.id,
        version=1,
        instructions=("Review the supplied artifact",),
        project_facts={"language": "Python"},
        source_refs=("source:readme",),
    )
    task = Task(
        project_id=project.id,
        title="Review scaffold",
        workflow_id="review-minimal",
        workflow_version=1,
        mode=WorkMode.REVIEW,
        context_package_id=context.id,
    )
    artifact = Artifact(
        project_id=project.id,
        task_id=task.id,
        artifact_type=ArtifactType.DOCUMENT,
        mime_type="text/plain",
        source_type="user",
        storage_ref="artifacts/readme.txt",
        sha256="a" * 64,
    )

    assert project.id.startswith("project_")
    assert task.id.startswith("task_")
    assert artifact.id.startswith("artifact_")
    assert context.instructions == ("Review the supplied artifact",)
    assert not hasattr(context, "prompt")
    assert artifact.size == 0


def test_evidence_types_and_statuses_are_explicit() -> None:
    assert {item.value for item in EvidenceType} == {
        "AI_OPINION",
        "RUNTIME_EVIDENCE",
        "TOOL_EVIDENCE",
        "DOCUMENT_EVIDENCE",
        "HUMAN_EVIDENCE",
    }
    assert EvidenceType.AI_OPINION != EvidenceType.TOOL_EVIDENCE
    assert {item.value for item in EvidenceStatus} == {
        "OBSERVED",
        "PASS",
        "FAIL",
        "NEED_ACTION",
        "HUMAN_DECISION",
    }


def test_finding_references_evidence_and_run_records_transitions() -> None:
    evidence = Evidence(
        task_id="task-1",
        run_id="run-1",
        actor_id="tool:test",
        source="pytest",
        type=EvidenceType.TOOL_EVIDENCE,
        status=EvidenceStatus.PASS,
    )
    finding = Finding(
        task_id="task-1",
        run_id="run-1",
        title="Example finding",
        description="Example description",
        severity=FindingSeverity.LOW,
        evidence_refs=(evidence.id,),
        status=FindingStatus.OPEN,
    )
    run = Run(
        task_id="task-1",
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id="context-1",
    )
    run.transition(RunState.STARTING)
    run.transition(RunState.RUNNING)
    run.transition(RunState.COMPLETED)

    assert finding.evidence_refs == (evidence.id,)
    assert [event.to_state for event in run.events] == [
        RunState.STARTING,
        RunState.RUNNING,
        RunState.COMPLETED,
    ]
