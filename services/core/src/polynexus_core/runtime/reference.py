from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from polynexus_core.domain.enums import ResumeMode, RunState
from polynexus_core.domain.models import Artifact, ContextPackage, Task
from polynexus_core.runtime.contracts import (
    RuntimeCapabilities,
    RuntimeResult,
    RuntimeStatus,
)


@dataclass
class _ReferenceRun:
    context: ContextPackage
    task: Task | None = None
    state: RunState = RunState.CREATED
    cleaned: bool = False


class ReferenceRuntimeAdapter:
    """Deterministic in-memory adapter used only to prove Core boundaries."""

    def __init__(self) -> None:
        self._runs: dict[str, _ReferenceRun] = {}

    async def health(self) -> bool:
        return True

    async def readiness(self) -> bool:
        return True

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(cancel=True, resume=ResumeMode.NONE, artifacts=True)

    async def create_run(self, context: ContextPackage) -> str:
        runtime_ref = f"reference:{uuid4().hex}"
        self._runs[runtime_ref] = _ReferenceRun(context=context)
        return runtime_ref

    async def submit(self, runtime_ref: str, task: Task) -> None:
        record = self._get(runtime_ref)
        if record.state is not RunState.CREATED:
            raise ValueError(f"Reference runtime cannot submit from {record.state}")
        record.task = task
        record.state = RunState.RUNNING

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        return RuntimeStatus(state=self._get(runtime_ref).state)

    async def result(self, runtime_ref: str) -> RuntimeResult:
        record = self._get(runtime_ref)
        if record.state not in {RunState.RUNNING, RunState.COMPLETED}:
            raise ValueError(f"Reference runtime has no result in state {record.state}")
        record.state = RunState.COMPLETED
        return RuntimeResult(summary="Reference runtime completed without vendor execution")

    async def cancel(self, runtime_ref: str) -> None:
        record = self._get(runtime_ref)
        if record.state in {RunState.CREATED, RunState.STARTING, RunState.RUNNING}:
            record.state = RunState.CANCELLED

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None:
        del checkpoint
        self._get(runtime_ref)
        raise NotImplementedError("Reference runtime has no resume capability")

    async def artifacts(self, runtime_ref: str) -> tuple[Artifact, ...]:
        self._get(runtime_ref)
        return ()

    async def cleanup(self, runtime_ref: str) -> bool:
        record = self._get(runtime_ref)
        record.cleaned = True
        return True

    def version_info(self) -> str:
        return "reference-runtime/0.1"

    def was_cleaned(self, runtime_ref: str) -> bool:
        return self._get(runtime_ref).cleaned

    def _get(self, runtime_ref: str) -> _ReferenceRun:
        try:
            return self._runs[runtime_ref]
        except KeyError as exc:
            raise KeyError(f"Unknown runtime reference: {runtime_ref}") from exc
