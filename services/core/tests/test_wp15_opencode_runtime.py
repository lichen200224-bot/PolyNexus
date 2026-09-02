"""WP-15 OpenCode Runtime Adapter conformance tests.

Deterministic, no-network coverage for lifecycle, cancel/timeout cleanup
(PRE-WP14-A contract), result/error normalization, capabilities, version
identity, sanitization, and unknown-reference fail-closed behavior.
"""
from __future__ import annotations

import asyncio
import inspect
import traceback
from pathlib import Path

import pytest

from polynexus_core.domain.enums import EvidenceStatus, ResumeMode, RunState
from polynexus_core.domain.models import ContextPackage, Project, Run, Task
from polynexus_core.runtime.contracts import RuntimeAdapter
from polynexus_core.runtime.opencode import OpenCodeRuntimeAdapter
from polynexus_core.runtime.registry import build_default_registry
from polynexus_core.runtime.supervisor import RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition


ROOT = Path(__file__).resolve().parents[3]

SECRET_MARKER_WP15_DO_NOT_PERSIST = "SECRET_MARKER_WP15_TOKEN_COOKIE_SESSION_API_KEY"

_PROTOCOL_METHODS = frozenset(
    (
        "health",
        "readiness",
        "capabilities",
        "create_run",
        "submit",
        "status",
        "result",
        "cancel",
        "resume",
        "artifacts",
        "cleanup",
        "version_info",
    )
)


def _inputs(title: str = "OpenCode conformance run") -> tuple[Task, ContextPackage]:
    project = Project(name="WP15")
    context = ContextPackage(
        project_id=project.id,
        version=1,
        source_refs=("fixture:wp15",),
        project_facts={"note": f"innocent {SECRET_MARKER_WP15_DO_NOT_PERSIST} bait"},
    )
    task = Task(
        project_id=project.id,
        title=title,
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id=context.id,
    )
    return task, context


def _workflow():
    return load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")


def _run_supervised(adapter: OpenCodeRuntimeAdapter):
    task, context = _inputs()
    supervisor = RunSupervisor(adapter)
    session = asyncio.run(supervisor.start(task, context, _workflow()))
    return supervisor, session


def test_adapter_satisfies_runtime_protocol() -> None:
    adapter = OpenCodeRuntimeAdapter()
    protocol_attrs = getattr(RuntimeAdapter, "__protocol_attrs__", frozenset())
    assert protocol_attrs, "RuntimeAdapter must expose protocol attributes"
    assert _PROTOCOL_METHODS <= frozenset(protocol_attrs)
    # Signatures match the Protocol (async callables where the Protocol is async).
    for name in _PROTOCOL_METHODS:
        assert inspect.iscoroutinefunction(getattr(adapter, name)) == inspect.iscoroutinefunction(
            getattr(RuntimeAdapter, name)
        )


def test_health_readiness_and_capabilities_truthful() -> None:
    adapter = OpenCodeRuntimeAdapter()
    assert asyncio.run(adapter.health()) is True
    assert asyncio.run(adapter.readiness()) is True
    caps = adapter.capabilities()
    assert caps.cancel is True
    assert caps.resume is ResumeMode.NONE
    assert caps.artifacts is True
    assert caps.timeout_cleanup_verified is True
    from polynexus_core.domain.enums import AuthOwnership, UsageVisibility

    assert caps.usage_visibility is UsageVisibility.UNAVAILABLE
    assert caps.auth_ownership is AuthOwnership.NONE


def test_version_identity_is_stable_and_opencode_scoped() -> None:
    adapter = OpenCodeRuntimeAdapter()
    first = adapter.version_info()
    assert first == adapter.version_info()
    assert first.startswith("opencode-")
    assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in first


def test_lifecycle_create_submit_status_result_stable_ids() -> None:
    adapter = OpenCodeRuntimeAdapter()
    _, context = _inputs()

    ref_a = asyncio.run(adapter.create_run(context))
    ref_b = asyncio.run(adapter.create_run(context))
    assert ref_a != ref_b
    assert ref_a.startswith("opencode:") and len(ref_a.split(":", 1)[1]) == 32

    status = asyncio.run(adapter.status(ref_a))
    assert status.state is RunState.CREATED

    task, _ = _inputs()
    asyncio.run(adapter.submit(ref_a, task))
    assert asyncio.run(adapter.status(ref_a)).state is RunState.RUNNING

    result = asyncio.run(adapter.result(ref_a))
    assert result.summary == "OpenCode runtime completed deterministic local execution"
    assert result.evidence == () and result.findings == () and result.artifacts == ()
    assert asyncio.run(adapter.status(ref_a)).state is RunState.COMPLETED


def test_double_submit_fails_closed() -> None:
    adapter = OpenCodeRuntimeAdapter()
    _, context = _inputs()
    ref = asyncio.run(adapter.create_run(context))
    task, _ = _inputs()
    asyncio.run(adapter.submit(ref, task))
    with pytest.raises(ValueError, match="cannot submit"):
        asyncio.run(adapter.submit(ref, task))


def test_result_rejected_before_active_states() -> None:
    adapter = OpenCodeRuntimeAdapter()
    _, context = _inputs()
    ref = asyncio.run(adapter.create_run(context))
    with pytest.raises(ValueError, match="no result in state CREATED"):
        asyncio.run(adapter.result(ref))


def test_full_completion_through_supervisor() -> None:
    adapter = OpenCodeRuntimeAdapter()
    supervisor, session = _run_supervised(adapter)
    execution = asyncio.run(supervisor.collect(session))

    assert session.run.state is RunState.COMPLETED
    assert execution.result.status is RunState.COMPLETED
    assert execution.result.summary == "OpenCode runtime completed deterministic local execution"
    assert execution.evidence
    assert all(item.type.value != "AI_OPINION" for item in execution.evidence)
    assert execution.artifacts == ()
    _assert_marker_absent(execution)


def test_user_cancel_verifies_cleanup() -> None:
    adapter = OpenCodeRuntimeAdapter()
    supervisor, session = _run_supervised(adapter)
    execution = asyncio.run(supervisor.cancel(session))

    assert execution.run.state is RunState.CANCELLED
    assert adapter.was_cleaned(session.runtime_ref)
    event_states = [event.to_state for event in session.run.events]
    assert event_states[-2:] == [RunState.CANCEL_REQUESTED, RunState.CANCELLED]
    assert asyncio.run(adapter.status(session.runtime_ref)).state is RunState.CANCELLED
    for evidence in execution.evidence:
        assert evidence.status is EvidenceStatus.PASS  # cancel success yields PASS evidence per supervisor contract


def test_timeout_cleanup_verified_timed_out() -> None:
    adapter = OpenCodeRuntimeAdapter()
    supervisor, session = _run_supervised(adapter)
    adapter.simulate_timeout(session.runtime_ref)

    execution = asyncio.run(supervisor.collect(session))

    assert execution.run.state is RunState.TIMED_OUT
    assert adapter.was_cleaned(session.runtime_ref)
    event_states = [event.to_state for event in session.run.events]
    assert event_states[-1] is RunState.TIMED_OUT
    assert RunState.ORPHANED not in event_states
    assert asyncio.run(adapter.status(session.runtime_ref)).state is RunState.TIMED_OUT
    for evidence in execution.evidence:
        assert evidence.status is not EvidenceStatus.PASS
    _assert_marker_absent(execution)


class _CancelRaisesOpenCode(OpenCodeRuntimeAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.cancel_called = False

    async def cancel(self, runtime_ref: str) -> None:
        self.cancel_called = True
        raise RuntimeError(f"vendor abort token={SECRET_MARKER_WP15_DO_NOT_PERSIST}")


class _CleanupRaisesOpenCode(OpenCodeRuntimeAdapter):
    async def cleanup(self, runtime_ref: str) -> bool:
        raise RuntimeError(f"cleanup exploded cookie={SECRET_MARKER_WP15_DO_NOT_PERSIST}")


class _CleanupFalseOpenCode(OpenCodeRuntimeAdapter):
    async def cleanup(self, runtime_ref: str) -> bool:
        await super().cleanup(runtime_ref)
        return False


@pytest.mark.parametrize(
    "adapter_factory",
    [_CancelRaisesOpenCode, _CleanupRaisesOpenCode, _CleanupFalseOpenCode],
)
def test_timeout_cleanup_failure_paths_fail_closed_orphaned(adapter_factory) -> None:
    adapter = adapter_factory()
    supervisor, session = _run_supervised(adapter)
    adapter.simulate_timeout(session.runtime_ref)

    execution = asyncio.run(supervisor.collect(session))

    assert execution.run.state is RunState.ORPHANED
    event_states = [event.to_state for event in session.run.events]
    assert event_states[-1] is RunState.ORPHANED
    assert RunState.CANCEL_REQUESTED in event_states
    assert RunState.TIMED_OUT not in event_states
    for evidence in execution.evidence:
        assert evidence.status is not EvidenceStatus.PASS
    _assert_marker_absent(execution)


@pytest.mark.parametrize(
    "adapter_factory",
    [_CancelRaisesOpenCode, _CleanupRaisesOpenCode, _CleanupFalseOpenCode],
)
def test_user_cancel_failure_paths_fail_closed_orphaned(adapter_factory) -> None:
    adapter = adapter_factory()
    supervisor, session = _run_supervised(adapter)

    execution = asyncio.run(supervisor.cancel(session))

    assert execution.run.state is RunState.ORPHANED
    event_states = [event.to_state for event in session.run.events]
    assert event_states[-1] is RunState.ORPHANED
    assert RunState.CANCEL_REQUESTED in event_states
    _assert_marker_absent(execution)


def test_normalized_failure_error_sanitized() -> None:
    adapter = OpenCodeRuntimeAdapter()
    supervisor, session = _run_supervised(adapter)
    adapter.simulate_failure(session.runtime_ref)

    status = asyncio.run(adapter.status(session.runtime_ref))
    assert status.state is RunState.FAILED
    assert status.error == "OpenCode runtime reported execution failure"
    assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in (status.error or "")

    execution = asyncio.run(supervisor.collect(session))
    assert execution.run.state is RunState.FAILED
    last_reason = execution.run.events[-1].reason or ""
    assert last_reason == "Runtime boundary error"
    assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in last_reason
    for evidence in execution.evidence:
        assert evidence.status is not EvidenceStatus.PASS
    _assert_marker_absent(execution)


@pytest.mark.parametrize(
    "method_name",
    ("status", "result", "cancel", "cleanup", "artifacts", "resume"),
)
def test_unknown_reference_fails_closed_without_echo(method_name: str) -> None:
    adapter = OpenCodeRuntimeAdapter()
    poisoned_ref = f"opencode:{SECRET_MARKER_WP15_DO_NOT_PERSIST}"
    with pytest.raises(KeyError) as excinfo:
        asyncio.run(getattr(adapter, method_name)(poisoned_ref))

    exc = excinfo.value
    assert "Unknown OpenCode runtime reference" in str(exc)
    assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in str(exc)
    assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in repr(exc.args)
    assert exc.__cause__ is None
    assert exc.__context__ is None
    assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in "".join(
        traceback.format_exception(exc)
    )


class _PoisonedStr(str):
    """str subclass whose conversion methods expose a marker."""

    def __str__(self) -> str:  # type: ignore[override]
        return SECRET_MARKER_WP15_DO_NOT_PERSIST

    def __repr__(self) -> str:  # type: ignore[override]
        return SECRET_MARKER_WP15_DO_NOT_PERSIST


@pytest.mark.parametrize(
    "method_name",
    ("status", "result", "cancel", "cleanup", "artifacts", "resume"),
)
def test_poisoned_str_subclass_fails_closed_without_echo(method_name: str) -> None:
    adapter = OpenCodeRuntimeAdapter()
    poisoned_ref = _PoisonedStr("opencode:legitimate-missing-ref")  # type: ignore[arg-type]
    with pytest.raises(KeyError) as excinfo:
        asyncio.run(getattr(adapter, method_name)(poisoned_ref))  # type: ignore[arg-type]
    exc = excinfo.value
    assert "Unknown OpenCode runtime reference" in str(exc), method_name
    assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in str(exc), method_name
    assert exc.args and exc.args[0] == "Unknown OpenCode runtime reference", method_name
    assert exc.__cause__ is None and exc.__context__ is None, method_name
    assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    ), method_name


def test_resume_never_fakes_native_resume() -> None:
    adapter = OpenCodeRuntimeAdapter()
    _, context = _inputs()
    ref = asyncio.run(adapter.create_run(context))
    with pytest.raises(NotImplementedError):
        asyncio.run(adapter.resume(ref, checkpoint="ckpt"))
    # Failed resume must not corrupt state.
    assert asyncio.run(adapter.status(ref)).state is RunState.CREATED


def test_artifacts_never_fabricated() -> None:
    adapter = OpenCodeRuntimeAdapter()
    _, context = _inputs()
    ref = asyncio.run(adapter.create_run(context))
    assert asyncio.run(adapter.artifacts(ref)) == ()
    assert asyncio.run(adapter.artifacts(ref)) == ()


def test_no_secrets_in_adapter_derived_outputs() -> None:
    """Secret-bearing caller input must never reach adapter-derived surfaces.

    The adapter retains only the caller-provided ContextPackage/Task objects
    themselves (contract-mandated, same as the reference adapter); every
    adapter-derived output stays marker-free.
    """
    adapter = OpenCodeRuntimeAdapter()
    task, context = _inputs(title=f"task with {SECRET_MARKER_WP15_DO_NOT_PERSIST}")
    completed_ref = asyncio.run(adapter.create_run(context))
    asyncio.run(adapter.submit(completed_ref, task))

    status = asyncio.run(adapter.status(completed_ref))
    result = asyncio.run(adapter.result(completed_ref))
    artifacts = asyncio.run(adapter.artifacts(completed_ref))

    timeout_ref = asyncio.run(adapter.create_run(context))
    asyncio.run(adapter.submit(timeout_ref, task))
    adapter.simulate_timeout(timeout_ref)
    timed_out_status = asyncio.run(adapter.status(timeout_ref))
    asyncio.run(adapter.cancel(timeout_ref))
    asyncio.run(adapter.cleanup(timeout_ref))

    surfaces = (
        status.error or "",
        timed_out_status.error or "",
        result.summary,
        adapter.version_info(),
        repr(result.evidence),
        repr(result.findings),
        repr(artifacts),
    )
    for surface in surfaces:
        assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in surface


def test_simulate_hooks_guard_transitions() -> None:
    adapter = OpenCodeRuntimeAdapter()
    _, context = _inputs()
    ref = asyncio.run(adapter.create_run(context))
    with pytest.raises(ValueError, match="cannot time out"):
        adapter.simulate_timeout(ref)
    with pytest.raises(ValueError, match="cannot fail"):
        adapter.simulate_failure(ref)


def test_cleanup_is_idempotent_and_status_stays_queryable() -> None:
    adapter = OpenCodeRuntimeAdapter()
    _, context = _inputs()
    ref = asyncio.run(adapter.create_run(context))
    assert asyncio.run(adapter.cleanup(ref)) is True
    assert asyncio.run(adapter.cleanup(ref)) is True
    assert adapter.was_cleaned(ref) is True
    assert asyncio.run(adapter.status(ref)).state is RunState.CREATED


def test_execute_existing_run_completes_with_opencode_adapter() -> None:
    adapter = OpenCodeRuntimeAdapter()
    task, context = _inputs()
    supervisor = RunSupervisor(adapter)
    run = Run(
        task_id=task.id,
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id=context.id,
    )
    execution = asyncio.run(supervisor.execute_run(run, task, context, _workflow()))

    assert execution.run.state is RunState.COMPLETED
    assert execution.result is not None
    assert any(
        item.metadata.get("runtime_version") == adapter.version_info()
        for item in execution.evidence
    )


def test_execute_claimed_run_completes_with_opencode_adapter() -> None:
    adapter = OpenCodeRuntimeAdapter()
    task, context = _inputs()
    supervisor = RunSupervisor(adapter)
    run = Run(
        task_id=task.id,
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id=context.id,
    )
    run.transition(RunState.STARTING)
    execution = asyncio.run(supervisor.execute_claimed_run(run, task, context, _workflow()))
    assert execution.run.state is RunState.COMPLETED
    assert execution.result.status is RunState.COMPLETED
    _assert_marker_absent(execution)


def test_core_has_no_vendor_specific_branches() -> None:
    """Static guard: Core must contain no provider-specific 'opencode' branch."""
    import polynexus_core.runtime.registry as registry_mod
    import polynexus_core.runtime.supervisor as supervisor_mod
    import polynexus_core.workflows.execution as execution_mod

    for module in (registry_mod, supervisor_mod, execution_mod):
        source = inspect.getsource(module)
        assert "opencode" not in source.lower(), module.__name__
    # The registry's built-in composition root registers only the reference.
    registry = build_default_registry()
    profile = registry.resolve("reference.local")
    assert profile.adapter_id == "builtin.reference"


def _assert_marker_absent(execution) -> None:
    if execution.result is not None and execution.result.summary:
        assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in execution.result.summary
    for evidence in execution.evidence:
        for value in evidence.metadata.values():
            if isinstance(value, str):
                assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in value
    for event in execution.run.events:
        if event.reason:
            assert SECRET_MARKER_WP15_DO_NOT_PERSIST not in event.reason
