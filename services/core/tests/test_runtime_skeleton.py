import asyncio
from pathlib import Path

import pytest

from polynexus_core.domain.enums import EvidenceStatus, EvidenceType, RunState
from polynexus_core.domain.models import ContextPackage, Project, Run, Task
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


# Secret marker for testing - must not appear in any persisted reason/result/evidence
SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST = "SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST"


class FakeTimeoutAdapter:
    """Fake adapter for testing timeout cleanup paths."""

    def __init__(
        self,
        initial_state: RunState = RunState.RUNNING,
        cancel_raises: bool = False,
        cleanup_returns: bool = True,
        cleanup_raises: bool = False,
        post_cleanup_state: RunState | None = None,
        status_after_cleanup_raises: bool = False,
        first_status_error: str | None = None,
    ) -> None:
        self._state = initial_state
        self._cancel_raises = cancel_raises
        self._cleanup_returns = cleanup_returns
        self._cleanup_raises = cleanup_raises
        self._post_cleanup_state = post_cleanup_state
        self._status_after_cleanup_raises = status_after_cleanup_raises
        self._first_status_error = first_status_error
        self._cancel_called = False
        self._cleanup_called = False
        self._status_count = 0

    async def health(self) -> bool:
        return True

    async def readiness(self) -> bool:
        return True

    def capabilities(self):
        from polynexus_core.runtime.contracts import RuntimeCapabilities, ResumeMode
        return RuntimeCapabilities(cancel=True, resume=ResumeMode.NONE, artifacts=True)

    async def create_run(self, context) -> str:
        return "fake:ref"

    async def submit(self, runtime_ref: str, task) -> None:
        pass

    async def status(self, runtime_ref: str):
        from polynexus_core.runtime.contracts import RuntimeStatus
        self._status_count += 1
        if self._status_after_cleanup_raises and self._cancel_called:
            raise RuntimeError("Status check failed after cleanup")
        if self._post_cleanup_state and self._cancel_called:
            return RuntimeStatus(state=self._post_cleanup_state)
        return RuntimeStatus(state=self._state, error=self._first_status_error)

    async def result(self, runtime_ref: str):
        from polynexus_core.runtime.contracts import RuntimeResult
        return RuntimeResult(summary="fake result")

    async def cancel(self, runtime_ref: str) -> None:
        self._cancel_called = True
        if self._cancel_raises:
            raise RuntimeError(f"Cancel failed with secret: {SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST}")

    async def resume(self, runtime_ref: str, checkpoint=None) -> None:
        raise NotImplementedError

    async def artifacts(self, runtime_ref: str):
        return ()

    async def cleanup(self, runtime_ref: str) -> bool:
        self._cleanup_called = True
        if self._cleanup_raises:
            raise RuntimeError(f"Cleanup failed with secret: {SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST}")
        return self._cleanup_returns

    def version_info(self) -> str:
        return "fake-adapter/0.1"


def _create_fake_task_context() -> tuple[Task, ContextPackage]:
    """Create minimal task/context for fake adapter tests."""
    project = Project(name="FakeTest")
    context = ContextPackage(project_id=project.id, version=1, source_refs=("fixture:fake",))
    task = Task(
        project_id=project.id,
        title="Fake test task",
        workflow_id="review-minimal",
        workflow_version=1,
        context_package_id=context.id,
    )
    return task, context


def test_collect_timeout_cleanup_success() -> None:
    """Test 1: collect timeout with successful cleanup."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(initial_state=RunState.TIMED_OUT)
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.collect(session))

    assert execution.run.state is RunState.TIMED_OUT
    assert adapter._cancel_called
    assert adapter._cleanup_called
    # Check event sequence
    event_states = [event.to_state for event in session.run.events]
    assert RunState.TIMED_OUT in event_states
    # No PASS evidence
    for evidence in execution.evidence:
        assert evidence.status != EvidenceStatus.PASS
    # No secret marker in reason/result/evidence
    _assert_no_secret_marker(execution)


def test_execute_run_timeout_cleanup_success() -> None:
    """Test 2: execute_run timeout with successful cleanup."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(initial_state=RunState.TIMED_OUT)
    supervisor = RunSupervisor(adapter)

    run = Run(
        task_id=task.id,
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        context_package_id=context.id,
    )
    # execute_run transitions CREATED -> STARTING -> RUNNING -> terminal
    execution = asyncio.run(supervisor.execute_run(run, task, context, workflow))

    assert execution.run.state is RunState.TIMED_OUT
    assert adapter._cancel_called
    assert adapter._cleanup_called
    # No fabricated PASS/verified output
    assert execution.result.status is RunState.TIMED_OUT
    # No PASS evidence
    for evidence in execution.evidence:
        assert evidence.status != EvidenceStatus.PASS
    _assert_no_secret_marker(execution)


def test_execute_claimed_run_timeout_cleanup_success() -> None:
    """Test 3: execute_claimed_run timeout with successful cleanup."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(initial_state=RunState.TIMED_OUT)
    supervisor = RunSupervisor(adapter)

    run = Run(
        task_id=task.id,
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        context_package_id=context.id,
    )
    # execute_claimed_run expects STARTING state (CAS claim already done)
    run.transition(RunState.STARTING)
    # execute_claimed_run transitions STARTING -> RUNNING -> terminal
    execution = asyncio.run(supervisor.execute_claimed_run(run, task, context, workflow))

    assert execution.run.state is RunState.TIMED_OUT
    assert adapter._cancel_called
    assert adapter._cleanup_called
    # Result/output stays truthful (None for timeout)
    assert execution.result is None
    _assert_no_secret_marker(execution)


def test_timeout_cleanup_returns_false_orphaned() -> None:
    """Test 4: cleanup() returns False -> ORPHANED."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(initial_state=RunState.TIMED_OUT, cleanup_returns=False)
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.collect(session))

    assert execution.run.state is RunState.ORPHANED
    # Event sequence must go through CANCEL_REQUESTED
    event_states = [event.to_state for event in session.run.events]
    assert RunState.CANCEL_REQUESTED in event_states
    assert RunState.ORPHANED in event_states
    # No PASS
    for evidence in execution.evidence:
        assert evidence.status != EvidenceStatus.PASS
    _assert_no_secret_marker(execution)


def test_timeout_cancel_raises_secret_orphaned() -> None:
    """Test 5: adapter.cancel() raises secret-bearing exception -> ORPHANED."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(initial_state=RunState.TIMED_OUT, cancel_raises=True)
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.collect(session))

    assert execution.run.state is RunState.ORPHANED
    # Secret marker must not appear in reason, result, evidence
    _assert_no_secret_marker(execution)


def test_timeout_cleanup_raises_secret_orphaned() -> None:
    """Test 6: adapter.cleanup() raises secret-bearing exception -> ORPHANED."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(initial_state=RunState.TIMED_OUT, cleanup_raises=True)
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.collect(session))

    assert execution.run.state is RunState.ORPHANED
    # Secret marker must not leak
    _assert_no_secret_marker(execution)


def test_timeout_post_cleanup_status_raises_orphaned() -> None:
    """Test 7: post-cleanup status() raises -> ORPHANED."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(
        initial_state=RunState.TIMED_OUT,
        status_after_cleanup_raises=True,
    )
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.collect(session))

    assert execution.run.state is RunState.ORPHANED
    # Cannot claim cleanup verified
    _assert_no_secret_marker(execution)


def test_user_cancel_success_regression() -> None:
    """Test 8: existing user cancel success path unchanged."""
    _, task, context = _slice_inputs()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = ReferenceRuntimeAdapter()
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.cancel(session))

    assert execution.run.state is RunState.CANCELLED
    assert adapter.was_cleaned(session.runtime_ref)
    event_states = [event.to_state for event in session.run.events]
    assert RunState.CANCEL_REQUESTED in event_states
    assert RunState.CANCELLED in event_states


def test_user_cancel_cleanup_failure_regression() -> None:
    """Test 9: user cancel cleanup failure -> ORPHANED."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(initial_state=RunState.RUNNING, cleanup_returns=False)
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.cancel(session))

    assert execution.run.state is RunState.ORPHANED
    event_states = [event.to_state for event in session.run.events]
    assert RunState.CANCEL_REQUESTED in event_states
    assert RunState.ORPHANED in event_states


def test_terminal_state_immutability() -> None:
    """Test 10: TIMED_OUT/ORPHANED cannot be rewritten by later paths."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    # First: timeout with successful cleanup -> TIMED_OUT
    adapter = FakeTimeoutAdapter(initial_state=RunState.TIMED_OUT)
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.collect(session))
    assert execution.run.state is RunState.TIMED_OUT

    # Second: try to collect again (should fail because run is terminal)
    with pytest.raises(ValueError, match="Run is not active"):
        asyncio.run(supervisor.collect(session))


def _assert_no_secret_marker(execution) -> None:
    """Assert that SECRET_MARKER does not appear in reason, result, evidence."""
    from polynexus_core.runtime.supervisor import (
        _RUNTIME_FAILURE_REASON,
        _TIMEOUT_CLEANUP_REASON,
        _CLEANUP_FAILED_REASON,
        _ORPHANED_REASON,
    )

    # Check run result summary
    if execution.result and execution.result.summary:
        assert SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST not in execution.result.summary

    # Check evidence metadata
    for evidence in execution.evidence:
        if evidence.metadata:
            for key, value in evidence.metadata.items():
                if isinstance(value, str):
                    assert SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST not in value

    # Check event reasons (if accessible)
    if hasattr(execution.run, 'events'):
        for event in execution.run.events:
            if hasattr(event, 'reason') and event.reason:
                assert SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST not in event.reason


def test_cancel_exception_paths_fail_closed_orphaned() -> None:
    """Attempt 2: cancel/cleanup/post-cleanup-status exceptions during user
    cancel are contained by the shared machinery; no raw exception reaches the
    caller and the Run converges CANCEL_REQUESTED -> ORPHANED."""
    cases = (
        ("cancel-raises", {"cancel_raises": True}),
        ("cleanup-raises", {"cleanup_raises": True}),
        ("post-cleanup-status-raises", {"status_after_cleanup_raises": True}),
    )
    for label, kwargs in cases:
        task, context = _create_fake_task_context()
        workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
        adapter = FakeTimeoutAdapter(initial_state=RunState.RUNNING, **kwargs)
        supervisor = RunSupervisor(adapter)

        session = asyncio.run(supervisor.start(task, context, workflow))
        # Must NOT raise despite adapter exceptions carrying secret markers.
        execution = asyncio.run(supervisor.cancel(session))

        assert execution is not None, label
        assert execution.run.state is RunState.ORPHANED, label
        event_states = [event.to_state for event in session.run.events]
        assert RunState.CANCEL_REQUESTED in event_states, label
        assert event_states[-1] is RunState.ORPHANED, label
        assert adapter._cancel_called or kwargs.get("cancel_raises"), label
        for evidence in execution.evidence:
            assert evidence.status != EvidenceStatus.PASS, label
        _assert_no_secret_marker(execution)


def test_timeout_wrong_post_cleanup_status_fails_closed_orphaned() -> None:
    """Attempt 2: timeout with wrong post-cleanup statuses (CANCELLED/FAILED/
    ORPHANED) must fail closed via CANCEL_REQUESTED -> ORPHANED, never TIMED_OUT."""
    for wrong_state in (RunState.CANCELLED, RunState.FAILED, RunState.ORPHANED):
        task, context = _create_fake_task_context()
        workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
        adapter = FakeTimeoutAdapter(
            initial_state=RunState.TIMED_OUT,
            post_cleanup_state=wrong_state,
        )
        supervisor = RunSupervisor(adapter)

        session = asyncio.run(supervisor.start(task, context, workflow))
        execution = asyncio.run(supervisor.collect(session))

        assert execution.run.state is RunState.ORPHANED, wrong_state
        event_states = [event.to_state for event in session.run.events]
        assert event_states[-1] is RunState.ORPHANED, wrong_state
        assert RunState.CANCEL_REQUESTED in event_states, wrong_state
        assert RunState.TIMED_OUT not in event_states, wrong_state
        for evidence in execution.evidence:
            assert evidence.status != EvidenceStatus.PASS, wrong_state
        _assert_no_secret_marker(execution)


def test_execute_run_cancellation_sanitizes_adapter_error() -> None:
    """Attempt 2: execute_run adapter-reported CANCELLED persists a sanitized
    reason; raw status.error (secret marker) never enters events/result/evidence."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(
        initial_state=RunState.CANCELLED,
        first_status_error=(
            f"vendor abort secret={SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST}"
        ),
    )
    supervisor = RunSupervisor(adapter)

    run = Run(
        task_id=task.id,
        workflow_id=workflow.id,
        workflow_version=workflow.version,
        context_package_id=context.id,
    )
    execution = asyncio.run(supervisor.execute_run(run, task, context, workflow))

    assert execution.run.state is RunState.CANCELLED
    last_event = execution.run.events[-1]
    assert last_event.to_state is RunState.CANCELLED
    assert SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST not in (last_event.reason or "")
    _assert_no_secret_marker(execution)


def test_collect_cancellation_sanitizes_adapter_error() -> None:
    """Attempt 2: collect adapter-reported CANCELLED persists a sanitized
    reason; raw status.error (secret marker) never enters events/result/evidence."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(
        initial_state=RunState.CANCELLED,
        first_status_error=(
            f"vendor abort secret={SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST}"
        ),
    )
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.collect(session))

    assert execution.run.state is RunState.CANCELLED
    last_event = execution.run.events[-1]
    assert last_event.to_state is RunState.CANCELLED
    assert SECRET_MARKER_PRE_WP14_A_DO_NOT_PERSIST not in (last_event.reason or "")
    _assert_no_secret_marker(execution)


def test_cancel_uses_shared_cleanup_machinery() -> None:
    """Attempt 2: user cancel success path goes through the same shared
    cleanup/verification machinery as timeout (cancel called before cleanup)."""
    task, context = _create_fake_task_context()
    workflow = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
    adapter = FakeTimeoutAdapter(
        initial_state=RunState.RUNNING,
        post_cleanup_state=RunState.CANCELLED,
    )
    supervisor = RunSupervisor(adapter)

    session = asyncio.run(supervisor.start(task, context, workflow))
    execution = asyncio.run(supervisor.cancel(session))

    assert execution.run.state is RunState.CANCELLED
    assert adapter._cancel_called
    assert adapter._cleanup_called
    event_states = [event.to_state for event in session.run.events]
    assert event_states[-2:] == [RunState.CANCEL_REQUESTED, RunState.CANCELLED]
