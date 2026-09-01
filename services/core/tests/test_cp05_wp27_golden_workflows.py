"""CP-05 WP-27 deterministic regression for the four Golden flows."""

import asyncio
from pathlib import Path

import pytest

from polynexus_core.domain.enums import ExecutionTarget, RunState
from polynexus_core.domain.models import ContextPackage, Project, Run, Task
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.supervisor import RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition


ROOT = Path(__file__).resolve().parents[3]

GOLDEN_WORKFLOWS = (
    pytest.param(
        "technical-design-review",
        ("CONTEXT", "PARALLEL_AI", "CROSS_REVIEW", "SYNTHESIS"),
        id="discuss-council",
    ),
    pytest.param(
        "review-minimal",
        ("CONTEXT", "AI_TASK", "SYNTHESIS"),
        id="code-artifact-review",
    ),
    pytest.param(
        "release-validation",
        (
            "CONTEXT",
            "PARALLEL_AI",
            "CROSS_REVIEW",
            "TOOL",
            "EVIDENCE_CHECK",
            "SYNTHESIS",
        ),
        id="release-validation",
    ),
    pytest.param(
        "decision-proposal-comparison",
        ("CONTEXT", "PARALLEL_AI", "CROSS_REVIEW", "SYNTHESIS"),
        id="web-ai-decision-review",
    ),
)


def _workflow_path(workflow_id: str) -> Path:
    return ROOT / "workflows" / "builtin" / f"{workflow_id}.yaml"


@pytest.mark.parametrize("workflow_id, expected_steps", GOLDEN_WORKFLOWS)
def test_golden_workflow_loads_with_expected_canonical_steps(
    workflow_id: str, expected_steps: tuple[str, ...]
) -> None:
    workflow = load_workflow_definition(_workflow_path(workflow_id))

    assert workflow.id == workflow_id
    assert workflow.version == 1
    assert tuple(step.type for step in workflow.steps) == expected_steps
    assert workflow.steps[-1].type == "SYNTHESIS"


@pytest.mark.parametrize("workflow_id, _expected_steps", GOLDEN_WORKFLOWS)
def test_golden_workflow_executes_through_local_supervisor(
    workflow_id: str, _expected_steps: tuple[str, ...]
) -> None:
    async def execute() -> object:
        workflow = load_workflow_definition(_workflow_path(workflow_id))
        project = Project(name="WP27 Golden")
        context = ContextPackage(project_id=project.id, version=1)
        task = Task(
            project_id=project.id,
            title=f"Golden workflow {workflow_id}",
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            context_package_id=context.id,
        )
        run = Run(
            task_id=task.id,
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            context_package_id=context.id,
            execution_target=ExecutionTarget.LOCAL,
        )

        execution = await RunSupervisor(ReferenceRuntimeAdapter()).execute_run(
            run, task, context, workflow
        )

        assert execution.run.id == run.id
        assert execution.run.execution_target is ExecutionTarget.LOCAL
        assert execution.run.state is RunState.COMPLETED
        assert execution.result is not None
        assert execution.result.status is RunState.COMPLETED
        assert execution.result.run_id == run.id
        assert execution.result.summary
        return execution

    asyncio.run(execute())
