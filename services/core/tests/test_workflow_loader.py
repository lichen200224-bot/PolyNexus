import asyncio
from pathlib import Path

import pytest

from polynexus_core.domain.models import ContextPackage, Task
from polynexus_core.workflows.execution import ReferenceWorkflowExecutor, WorkflowExecutionRequest
from polynexus_core.workflows.loader import (
    WorkflowValidationError,
    load_workflow,
    load_workflow_definition,
)

ROOT = Path(__file__).resolve().parents[3]
BUILTIN_WORKFLOWS = (
    "review-minimal",
    "release-validation",
    "bug-incident-analysis",
    "technical-design-review",
    "requirement-review",
    "change-impact-review",
    "document-review",
    "sop-review",
    "decision-proposal-comparison",
)


class FakeRuntime:
    def __init__(self) -> None:
        self.created_context = None
        self.submitted_task = None

    async def create_run(self, context: ContextPackage) -> str:
        self.created_context = context
        return "runtime-ref"

    async def submit(self, runtime_ref: str, task: Task) -> None:
        self.submitted_task = (runtime_ref, task)


def test_builtin_review_workflow_validates() -> None:
    workflow = load_workflow(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    assert workflow["id"] == "review-minimal"
    assert workflow["version"] == 1


def test_builtin_workflow_normalizes_to_canonical_definition() -> None:
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")

    assert workflow.id == "review-minimal"
    assert workflow.version == 1
    assert [step.type for step in workflow.steps] == ["CONTEXT", "AI_TASK", "SYNTHESIS"]


@pytest.mark.parametrize("workflow_id", BUILTIN_WORKFLOWS)
def test_all_v1_builtin_workflows_validate_and_normalize(workflow_id: str) -> None:
    path = ROOT / "workflows" / "builtin" / f"{workflow_id}.yaml"
    workflow = load_workflow_definition(path)

    assert workflow.id == workflow_id
    assert workflow.version == 1
    assert workflow.steps[-1].type == "SYNTHESIS"
    assert all(step.type in {
        "CONTEXT",
        "AI_TASK",
        "PARALLEL_AI",
        "CROSS_REVIEW",
        "TOOL",
        "EVIDENCE_CHECK",
        "HUMAN_GATE",
        "SYNTHESIS",
        "CONDITION",
    } for step in workflow.steps)


@pytest.mark.parametrize("workflow_id", ["review-minimal", "release-validation", "decision-proposal-comparison"])
def test_representative_builtin_workflows_execute_through_existing_boundary(workflow_id: str) -> None:
    async def execute() -> None:
        workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / f"{workflow_id}.yaml")
        context = ContextPackage(project_id="project-test", version=1)
        task = Task(
            project_id="project-test",
            title="workflow regression",
            workflow_id=workflow.id,
            workflow_version=workflow.version,
        )
        runtime = FakeRuntime()

        result = await ReferenceWorkflowExecutor().execute(
            WorkflowExecutionRequest(task=task, context=context, workflow=workflow),
            runtime,
        )

        assert result.runtime_ref == "runtime-ref"
        assert runtime.created_context == context
        assert runtime.submitted_task == ("runtime-ref", task)

    asyncio.run(execute())


def test_invalid_node_is_rejected(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text(
        "id: invalid\nversion: 1\nsteps:\n  - id: bad\n    type: ARBITRARY_SCRIPT\n",
        encoding="utf-8",
    )
    with pytest.raises(WorkflowValidationError):
        load_workflow(invalid)
