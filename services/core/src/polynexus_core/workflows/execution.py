from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from polynexus_core.domain.models import ContextPackage, Task
from polynexus_core.runtime.contracts import RuntimeAdapter
from polynexus_core.workflows.models import WorkflowDefinition


@dataclass(frozen=True)
class WorkflowExecutionRequest:
    task: Task
    context: ContextPackage
    workflow: WorkflowDefinition


@dataclass(frozen=True)
class RuntimeExecution:
    runtime_ref: str


class WorkflowExecutor(Protocol):
    async def execute(
        self,
        request: WorkflowExecutionRequest,
        runtime: RuntimeAdapter,
    ) -> RuntimeExecution: ...


class ReferenceWorkflowExecutor:
    """Minimal execution boundary; workflow step semantics remain future work."""

    async def execute(
        self,
        request: WorkflowExecutionRequest,
        runtime: RuntimeAdapter,
    ) -> RuntimeExecution:
        runtime_ref = await runtime.create_run(request.context)
        await runtime.submit(runtime_ref, request.task)
        return RuntimeExecution(runtime_ref=runtime_ref)
