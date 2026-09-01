"""CP06 WP28 deterministic failure-injection and cleanup acceptance tests."""

import asyncio
import subprocess
import sys
from pathlib import Path

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.models import ContextPackage, Project, Task
from polynexus_core.runtime.contracts import (
    RuntimeCapabilities,
    RuntimeResult,
    RuntimeStatus,
)
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime import supervisor as supervisor_module
from polynexus_core.runtime.supervisor import RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")
UNSAFE_ADAPTER_DETAIL = "fixture-only adapter detail must not cross the runtime boundary"


def _inputs() -> tuple[Task, ContextPackage]:
    project = Project(name="CP06 WP28")
    context = ContextPackage(project_id=project.id, version=1, source_refs=("fixture:cp06-wp28",))
    task = Task(
        project_id=project.id,
        title="CP06 WP28 failure injection",
        workflow_id=WORKFLOW.id,
        workflow_version=WORKFLOW.version,
        context_package_id=context.id,
    )
    return task, context


class ChildProcessProbeAdapter:
    """Adapter double with an owned child process and injectable failures."""

    def __init__(
        self,
        *,
        crash_on_status: bool = False,
        block_status: bool = False,
        cleanup_returns: bool = True,
    ) -> None:
        self.crash_on_status = crash_on_status
        self.block_status = block_status
        self.cleanup_returns = cleanup_returns
        self.state = RunState.CREATED
        self.process: subprocess.Popen[bytes] | None = None
        self.cleanup_called = False
        self.status_calls = 0

    async def health(self) -> bool:
        return True

    async def readiness(self) -> bool:
        return True

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            cancel=True,
            artifacts=True,
            timeout_cleanup_verified=True,
        )

    async def create_run(self, context: ContextPackage) -> str:
        del context
        self.process = subprocess.Popen(
            [sys.executable, "-B", "-c", "import time; time.sleep(60)"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return "fixture:cp06-wp28"

    async def submit(self, runtime_ref: str, task: Task) -> None:
        del runtime_ref, task
        self.state = RunState.RUNNING

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        del runtime_ref
        self.status_calls += 1
        if self.block_status and self.status_calls == 1:
            await asyncio.sleep(60)
        if self.crash_on_status and self.status_calls == 1:
            # The injected adapter crash owns and stops its child before the
            # boundary raises, so this test cannot leave an orphaned process.
            self._stop_child()
            raise RuntimeError(UNSAFE_ADAPTER_DETAIL)
        return RuntimeStatus(state=self.state)

    async def result(self, runtime_ref: str) -> RuntimeResult:
        del runtime_ref
        return RuntimeResult(summary="fixture result")

    async def cancel(self, runtime_ref: str) -> None:
        del runtime_ref
        if self.cleanup_returns:
            self._stop_child()
        self.state = RunState.TIMED_OUT if self.block_status else RunState.CANCELLED

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None:
        del runtime_ref, checkpoint
        raise NotImplementedError

    async def artifacts(self, runtime_ref: str):
        del runtime_ref
        return ()

    async def cleanup(self, runtime_ref: str) -> bool:
        del runtime_ref
        self.cleanup_called = True
        if self.cleanup_returns:
            self._stop_child()
        return self.cleanup_returns

    def version_info(self) -> str:
        return "fixture-adapter/1"

    def child_alive(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def _stop_child(self) -> None:
        if self.process is None or self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=2)


def _assert_safe_execution(execution) -> None:
    assert execution.result is not None
    assert UNSAFE_ADAPTER_DETAIL not in (execution.result.summary or "")
    assert all(
        UNSAFE_ADAPTER_DETAIL not in str(event.reason or "")
        for event in execution.run.events
    )
    for evidence in execution.evidence:
        assert all(UNSAFE_ADAPTER_DETAIL not in str(value) for value in evidence.metadata.values())


def test_adapter_crash_isolated_and_core_remains_available() -> None:
    task, context = _inputs()
    failing_adapter = ChildProcessProbeAdapter(crash_on_status=True)
    failing_supervisor = RunSupervisor(failing_adapter)

    async def fail_once():
        session = await failing_supervisor.start(task, context, WORKFLOW)
        return await failing_supervisor.collect(session)

    failed = asyncio.run(fail_once())

    assert failed.run.state is RunState.FAILED
    assert failed.result is not None
    assert failed.result.status is RunState.FAILED
    assert not failing_adapter.child_alive()
    _assert_safe_execution(failed)

    healthy_task, healthy_context = _inputs()
    healthy_supervisor = RunSupervisor(ReferenceRuntimeAdapter())

    async def complete_once():
        session = await healthy_supervisor.start(healthy_task, healthy_context, WORKFLOW)
        return await healthy_supervisor.collect(session)

    healthy = asyncio.run(complete_once())

    assert healthy.run.state is RunState.COMPLETED
    assert healthy.result is not None
    assert healthy.result.status is RunState.COMPLETED


def test_cancel_terminates_owned_child_and_verifies_cleanup() -> None:
    task, context = _inputs()
    adapter = ChildProcessProbeAdapter()
    supervisor = RunSupervisor(adapter)

    async def cancel_once():
        session = await supervisor.start(task, context, WORKFLOW)
        assert adapter.child_alive()
        return await supervisor.cancel(session)

    execution = asyncio.run(cancel_once())

    assert execution.run.state is RunState.CANCELLED
    assert adapter.cleanup_called
    assert not adapter.child_alive()
    assert execution.result is not None
    assert execution.result.status is RunState.CANCELLED


def test_timeout_terminates_owned_child_and_never_claims_completion(monkeypatch) -> None:
    monkeypatch.setattr(supervisor_module, "_DEFAULT_OPERATION_TIMEOUT_SECONDS", 0.01)
    task, context = _inputs()
    adapter = ChildProcessProbeAdapter(block_status=True)
    supervisor = RunSupervisor(adapter)

    async def collect_once():
        session = await supervisor.start(task, context, WORKFLOW)
        assert adapter.child_alive()
        return await supervisor.collect(session)

    execution = asyncio.run(collect_once())

    assert execution.run.state is RunState.TIMED_OUT
    assert execution.result is not None
    assert execution.result.status is RunState.TIMED_OUT
    assert adapter.cleanup_called
    assert not adapter.child_alive()
    assert RunState.COMPLETED not in [event.to_state for event in execution.run.events]


def test_cleanup_failure_is_orphaned_and_does_not_claim_child_stopped() -> None:
    task, context = _inputs()
    adapter = ChildProcessProbeAdapter(cleanup_returns=False)
    supervisor = RunSupervisor(adapter)

    async def cancel_once():
        session = await supervisor.start(task, context, WORKFLOW)
        assert adapter.child_alive()
        return await supervisor.cancel(session)

    try:
        execution = asyncio.run(cancel_once())
        assert execution.run.state is RunState.ORPHANED
        assert execution.result is not None
        assert execution.result.status is RunState.ORPHANED
        assert adapter.cleanup_called
        assert adapter.child_alive()
        assert RunState.CANCELLED not in [event.to_state for event in execution.run.events]
    finally:
        adapter._stop_child()
