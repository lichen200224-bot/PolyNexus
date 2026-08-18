from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from polynexus_core.domain.enums import ResumeMode, RunState
from polynexus_core.domain.models import Artifact, ContextPackage, Evidence, Finding, Task


@dataclass(frozen=True)
class RuntimeCapabilities:
    cancel: bool = True
    resume: ResumeMode = ResumeMode.NONE
    artifacts: bool = True


@dataclass(frozen=True)
class RuntimeStatus:
    state: RunState
    error: str | None = None


@dataclass(frozen=True)
class RuntimeResult:
    summary: str
    evidence: tuple[Evidence, ...] = ()
    findings: tuple[Finding, ...] = ()
    artifacts: tuple[Artifact, ...] = ()


class RuntimeAdapter(Protocol):
    async def health(self) -> bool: ...

    async def readiness(self) -> bool: ...

    def capabilities(self) -> RuntimeCapabilities: ...

    async def create_run(self, context: ContextPackage) -> str: ...

    async def submit(self, runtime_ref: str, task: Task) -> None: ...

    async def status(self, runtime_ref: str) -> RuntimeStatus: ...

    async def result(self, runtime_ref: str) -> RuntimeResult: ...

    async def cancel(self, runtime_ref: str) -> None: ...

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None: ...

    async def artifacts(self, runtime_ref: str) -> tuple[Artifact, ...]: ...

    async def cleanup(self, runtime_ref: str) -> bool: ...

    def version_info(self) -> str: ...
