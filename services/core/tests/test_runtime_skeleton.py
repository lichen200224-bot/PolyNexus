import asyncio
from pathlib import Path

from polynexus_core.domain.enums import EvidenceType, RunState
from polynexus_core.domain.models import ContextPackage, Project, Task
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.supervisor import RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition


ROOT = Path(__file__).resolve().parents[3]


def _slice_inputs() -> tuple[Project, Task, ContextPackage]:
    project = Project(name="FVS")
    context = ContextPackage(project_id=project.id, version=1, source_refs=("fixture:fvs",))
    task = Task(
        project_id=project.id,
        title="Run reference review",
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id=context.id,
    )
    return project, task, context


def test_reference_runtime_completes_through_supervisor() -> None:
    _, task, context = _slice_inputs()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = ReferenceRuntimeAdapter()
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.collect(session))

    assert session.run.state is RunState.COMPLETED
    assert execution.result.status is RunState.COMPLETED
    assert execution.evidence
    assert execution.artifacts == ()
    assert all(item.type is EvidenceType.RUNTIME_EVIDENCE for item in execution.evidence)
    assert not any(item.type is EvidenceType.AI_OPINION for item in execution.evidence)


def test_cancel_verifies_reference_runtime_cleanup() -> None:
    _, task, context = _slice_inputs()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = ReferenceRuntimeAdapter()
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.cancel(session))

    assert execution.run.state is RunState.CANCELLED
    assert adapter.was_cleaned(session.runtime_ref)
    assert [event.to_state for event in session.run.events][-2:] == [
        RunState.CANCEL_REQUESTED,
        RunState.CANCELLED,
    ]
