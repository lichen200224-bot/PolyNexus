"""Codex Runtime Adapter (WP-14).

Deterministic, no-network conformance adapter for the Codex runtime identity.
All vendor knowledge lives inside this adapter; Core contains no
``if provider == ...`` branches on this module.

Truthful-maturity contract:
  - cancel/cleanup follow the PRE-WP14-A shared verification machinery:
    adapter.cancel -> adapter.cleanup -> adapter.status must prove owned work
    stopped in exactly TIMED_OUT (timeout) or CANCELLED (cancel).
  - resume is ResumeMode.NONE; native resume is never faked.
  - no credential, token, cookie, session, or endpoint secret is stored;
    auth_ownership is NONE and usage visibility is UNAVAILABLE.
  - error normalization is fail-closed: raw vendor/exception text never
    enters RuntimeStatus.error, RuntimeResult.summary, or Evidence metadata.
  - the adapter retains only caller-provided ContextPackage/Task references
    (contract-mandated); it derives no new durable surface from their content.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from polynexus_core.domain.enums import AuthOwnership, ResumeMode, RunState, UsageVisibility
from polynexus_core.domain.models import Artifact, ContextPackage, Task
from polynexus_core.runtime.contracts import (
    RuntimeCapabilities,
    RuntimeResult,
    RuntimeStatus,
)

# Public-safe normalized failure reason. Raw vendor payloads, exception text,
# paths, tokens, and credentials are never stored or echoed.
_NORMALIZED_FAILURE_ERROR = "Codex runtime reported execution failure"

_UNKNOWN_REF_ERROR = "Unknown Codex runtime reference"

_NO_RESUME_ERROR = "Codex runtime has no resume capability"

_RESULT_SUMMARY = "Codex runtime completed deterministic local execution"


@dataclass
class _CodexRun:
    context: ContextPackage
    task: Task | None = None
    state: RunState = RunState.CREATED
    cleaned: bool = False


class CodexRuntimeAdapter:
    """Deterministic local Codex runtime adapter satisfying RuntimeAdapter."""

    def __init__(self) -> None:
        self._runs: dict[str, _CodexRun] = {}

    async def health(self) -> bool:
        return True

    async def readiness(self) -> bool:
        return True

    def capabilities(self) -> RuntimeCapabilities:
        # Truthful capability set: cancel and timeout cleanup are verified by
        # WP-14 targeted evidence; no usage data and no managed credentials.
        return RuntimeCapabilities(
            cancel=True,
            resume=ResumeMode.NONE,
            artifacts=True,
            timeout_cleanup_verified=True,
            usage_visibility=UsageVisibility.UNAVAILABLE,
            auth_ownership=AuthOwnership.NONE,
        )

    async def create_run(self, context: ContextPackage) -> str:
        runtime_ref = f"codex:{uuid4().hex}"
        self._runs[runtime_ref] = _CodexRun(context=context)
        return runtime_ref

    async def submit(self, runtime_ref: str, task: Task) -> None:
        record = self._get(runtime_ref)
        if record.state is not RunState.CREATED:
            raise ValueError(f"Codex runtime cannot submit from state {record.state.value}")
        record.task = task
        record.state = RunState.RUNNING

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        record = self._get(runtime_ref)
        if record.state is RunState.FAILED:
            # Normalized constant only; raw vendor error text is never exposed.
            return RuntimeStatus(state=record.state, error=_NORMALIZED_FAILURE_ERROR)
        return RuntimeStatus(state=record.state)

    async def result(self, runtime_ref: str) -> RuntimeResult:
        record = self._get(runtime_ref)
        if record.state not in {RunState.RUNNING, RunState.COMPLETED}:
            raise ValueError(f"Codex runtime has no result in state {record.state.value}")
        record.state = RunState.COMPLETED
        # No fabricated Evidence/Finding/Artifact: the supervisor owns durable
        # evidence construction from boundary calls; this summary is constant.
        return RuntimeResult(summary=_RESULT_SUMMARY)

    async def cancel(self, runtime_ref: str) -> None:
        record = self._get(runtime_ref)
        # Only active work can be stopped. Terminal states (including
        # TIMED_OUT) stay unchanged so the shared cleanup machinery's
        # post-cleanup status verification observes the expected state.
        if record.state in {RunState.CREATED, RunState.STARTING, RunState.RUNNING}:
            record.state = RunState.CANCELLED

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None:
        del checkpoint
        self._get(runtime_ref)
        raise NotImplementedError(_NO_RESUME_ERROR)

    async def artifacts(self, runtime_ref: str) -> tuple[Artifact, ...]:
        self._get(runtime_ref)
        return ()

    async def cleanup(self, runtime_ref: str) -> bool:
        record = self._get(runtime_ref)
        record.cleaned = True
        return True

    def version_info(self) -> str:
        return "codex-local-adapter/0.1"

    def was_cleaned(self, runtime_ref: str) -> bool:
        return self._get(runtime_ref).cleaned

    def simulate_timeout(self, runtime_ref: str) -> None:
        """Driver-only hook: simulate the vendor deadline expiring for a run."""
        record = self._get(runtime_ref)
        if record.state is not RunState.RUNNING:
            raise ValueError(f"Codex runtime cannot time out from state {record.state.value}")
        record.state = RunState.TIMED_OUT

    def simulate_failure(self, runtime_ref: str) -> None:
        """Driver-only hook: simulate a vendor-side execution failure."""
        record = self._get(runtime_ref)
        if record.state is not RunState.RUNNING:
            raise ValueError(f"Codex runtime cannot fail from state {record.state.value}")
        record.state = RunState.FAILED

    def _get(self, runtime_ref: str) -> _CodexRun:
        if type(runtime_ref) is not str:
            raise KeyError(_UNKNOWN_REF_ERROR)
        record = self._runs.get(runtime_ref)
        if record is None:
            raise KeyError(_UNKNOWN_REF_ERROR)
        return record
