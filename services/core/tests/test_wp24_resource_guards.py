"""WP-24 deterministic resource-guard and cleanup acceptance tests."""

import asyncio
from pathlib import Path

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.models import ContextPackage, Project, Run, Task
from polynexus_core.runtime import supervisor as supervisor_module
from polynexus_core.runtime.contracts import (
    RuntimeCapabilities,
    RuntimeResult,
    RuntimeStatus,
)
from polynexus_core.runtime.supervisor import RunSession, RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = load_workflow_definition(ROOT / "workflows" / "builtin" / "review-minimal.yaml")


def _inputs() -> tuple[Task, ContextPackage]:
    project = Project(name="WP24")
    context = ContextPackage(project_id=project.id, version=1, source_refs=("fixture:wp24",))
    task = Task(
        project_id=project.id,
        title="WP24 resource guard",
        workflow_id=WORKFLOW.id,
        workflow_version=WORKFLOW.version,
        context_package_id=context.id,
    )
    return task, context


class GuardProbeAdapter:
    def __init__(
        self,
        *,
        operation_delay: float = 0.0,
        block_status: bool = False,
        block_cleanup: bool = False,
        fail_submit: bool = False,
        cancel_state: RunState = RunState.TIMED_OUT,
        shared_tracker: dict[str, int] | None = None,
    ) -> None:
        self.operation_delay = operation_delay
        self.block_status = block_status
        self.block_cleanup = block_cleanup
        self.fail_submit = fail_submit
        self.cancel_state = cancel_state
        self.shared_tracker = shared_tracker
        self.state = RunState.CREATED
        self.active = False
        self.cleanup_called = False
        self.status_calls = 0
        self.status_entered = asyncio.Event()
        self.cleanup_entered = asyncio.Event()

    async def _delay(self) -> None:
        if self.shared_tracker is not None:
            self.shared_tracker["current"] += 1
            self.shared_tracker["max"] = max(
                self.shared_tracker["max"], self.shared_tracker["current"]
            )
        try:
            await asyncio.sleep(self.operation_delay)
        finally:
            if self.shared_tracker is not None:
                self.shared_tracker["current"] -= 1

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
        await self._delay()
        self.active = True
        return "wp24:runtime"

    async def submit(self, runtime_ref: str, task: Task) -> None:
        del runtime_ref, task
        await self._delay()
        if self.fail_submit:
            raise RuntimeError("setup failure marker")
        self.state = RunState.RUNNING

    async def status(self, runtime_ref: str) -> RuntimeStatus:
        del runtime_ref
        self.status_calls += 1
        if self.block_status and self.status_calls == 1:
            self.status_entered.set()
            await asyncio.Event().wait()
        return RuntimeStatus(state=self.state)

    async def result(self, runtime_ref: str) -> RuntimeResult:
        del runtime_ref
        await self._delay()
        return RuntimeResult(summary="wp24 result")

    async def cancel(self, runtime_ref: str) -> None:
        del runtime_ref
        await self._delay()
        self.state = self.cancel_state

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None:
        del runtime_ref, checkpoint
        raise NotImplementedError

    async def artifacts(self, runtime_ref: str):
        del runtime_ref
        await self._delay()
        return ()

    async def cleanup(self, runtime_ref: str) -> bool:
        del runtime_ref
        self.cleanup_called = True
        if self.block_cleanup:
            self.cleanup_entered.set()
            await asyncio.Event().wait()
        self.active = False
        return True

    def version_info(self) -> str:
        return "wp24-probe/1"


def _active_session(adapter):
    task, context = _inputs()
    run = Run(task_id=task.id, workflow_id=WORKFLOW.id, workflow_version=WORKFLOW.version,
              context_package_id=context.id, runtime_ref="wp24:runtime")
    run.transition(RunState.STARTING)
    run.transition(RunState.RUNNING)
    adapter.active = True
    adapter.state = RunState.RUNNING
    return RunSession(run, run.runtime_ref)


def _expire_blocked_call(monkeypatch, supervisor, name, entered):
    """Expire the real wait_for only after the selected coroutine is suspended."""
    original = supervisor._wait_for_operation
    fired = False

    async def controlled(operation, *, timeout):
        nonlocal fired
        if not fired and operation.cr_code.co_name == name:
            fired = True
            pending = asyncio.create_task(operation)
            await entered.wait()
            return await original(pending, timeout=0)
        return await original(operation, timeout=timeout)

    monkeypatch.setattr(supervisor, "_wait_for_operation", controlled)


def test_operation_timeout_reuses_cleanup_and_never_claims_completion(monkeypatch) -> None:
    task, context = _inputs()
    adapter = GuardProbeAdapter(block_status=True)
    supervisor = RunSupervisor(adapter)
    _expire_blocked_call(monkeypatch, supervisor, "status", adapter.status_entered)

    async def run() -> object:
        session = _active_session(adapter)
        return await supervisor.collect(session)

    execution = asyncio.run(run())

    assert execution.run.state is RunState.TIMED_OUT
    assert execution.result is not None
    assert execution.result.status is RunState.TIMED_OUT
    assert adapter.cleanup_called
    assert not adapter.active
    assert RunState.COMPLETED not in [event.to_state for event in execution.run.events]


def test_cleanup_timeout_fails_closed_as_orphaned(monkeypatch) -> None:
    monkeypatch.setattr(supervisor_module, "_DEFAULT_CLEANUP_TIMEOUT_SECONDS", 0.01)
    task, context = _inputs()
    adapter = GuardProbeAdapter(block_cleanup=True)
    supervisor = RunSupervisor(adapter)
    _expire_blocked_call(monkeypatch, supervisor, "cleanup", adapter.cleanup_entered)

    async def run() -> object:
        session = _active_session(adapter)
        return await supervisor.cancel(session)

    execution = asyncio.run(run())

    assert execution.run.state is RunState.ORPHANED
    assert adapter.cleanup_called
    assert adapter.active
    assert [event.to_state for event in execution.run.events][-2:] == [
        RunState.CANCEL_REQUESTED,
        RunState.ORPHANED,
    ]


def test_cancel_success_verifies_cleanup_and_terminal_state() -> None:
    task, context = _inputs()
    adapter = GuardProbeAdapter(cancel_state=RunState.CANCELLED)
    supervisor = RunSupervisor(adapter)

    async def run() -> object:
        session = await supervisor.start(task, context, WORKFLOW)
        return await supervisor.cancel(session)

    execution = asyncio.run(run())

    assert execution.run.state is RunState.CANCELLED
    assert adapter.cleanup_called
    assert not adapter.active
    assert [event.to_state for event in execution.run.events][-2:] == [
        RunState.CANCEL_REQUESTED,
        RunState.CANCELLED,
    ]


def test_setup_failure_cleans_allocated_runtime_and_fails_closed() -> None:
    task, context = _inputs()
    adapter = GuardProbeAdapter(fail_submit=True, cancel_state=RunState.CANCELLED)
    run = Run(
        task_id=task.id,
        workflow_id=WORKFLOW.id,
        workflow_version=WORKFLOW.version,
        context_package_id=context.id,
    )
    run.transition(RunState.STARTING)
    execution = asyncio.run(
        RunSupervisor(adapter).execute_claimed_run(run, task, context, WORKFLOW)
    )

    assert execution.run.state is RunState.FAILED
    assert execution.result is None
    assert adapter.cleanup_called
    assert not adapter.active
    assert RunState.ORPHANED not in [event.to_state for event in execution.run.events]


def test_operation_budget_is_bounded_and_uses_cleanup(monkeypatch) -> None:
    monkeypatch.setattr(supervisor_module, "_MAX_RUN_OPERATIONS", 2)
    task, context = _inputs()
    adapter = GuardProbeAdapter()
    supervisor = RunSupervisor(adapter)

    execution = asyncio.run(
        supervisor.execute_run(
            Run(
                task_id=task.id,
                workflow_id=WORKFLOW.id,
                workflow_version=WORKFLOW.version,
                context_package_id=context.id,
            ),
            task,
            context,
            WORKFLOW,
        )
    )

    assert execution.run.state is RunState.TIMED_OUT
    assert adapter.cleanup_called
    assert not adapter.active


def test_runtime_operation_concurrency_is_globally_bounded() -> None:
    tracker = {"current": 0, "max": 0}
    adapters = [GuardProbeAdapter(operation_delay=0.02, shared_tracker=tracker) for _ in range(8)]

    async def run() -> list[object]:
        task, context = _inputs()
        return await asyncio.gather(
            *[
                RunSupervisor(adapter).start(task, context, WORKFLOW)
                for adapter in adapters
            ]
        )

    sessions = asyncio.run(run())

    assert len(sessions) == 8
    assert tracker["max"] <= supervisor_module._MAX_CONCURRENT_RUNTIME_OPERATIONS
    assert tracker["max"] >= 2
    assert all(session.run.state is RunState.RUNNING for session in sessions)
