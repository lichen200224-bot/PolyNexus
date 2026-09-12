from __future__ import annotations

import asyncio
import weakref
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, TypeVar

from polynexus_core.domain.enums import EvidenceStatus, EvidenceType, RunState
from polynexus_core.domain.models import (
    Artifact,
    ContextPackage,
    Evidence,
    Finding,
    Run,
    RunResult,
    Task,
)
from polynexus_core.runtime.contracts import RuntimeAdapter, RuntimeResult
from polynexus_core.runtime.redaction import (
    redact_exception,
    redact_text,
    sanitize_artifact,
    sanitize_finding,
    sanitize_run,
    sanitize_runtime_result,
)
from polynexus_core.workflows.execution import (
    ReferenceWorkflowExecutor,
    WorkflowExecutionRequest,
    WorkflowExecutor,
)
from polynexus_core.workflows.models import WorkflowDefinition


# Public-safe sanitized reason for runtime boundary failures.
# Never contains raw exception messages, vendor payloads, paths, tokens,
# or credential fragments.
_RUNTIME_FAILURE_REASON = "Runtime boundary error"

# Public-safe sanitized reason for timeout with successful cleanup.
_TIMEOUT_CLEANUP_REASON = "Runtime timed out and cleanup verified"

# Public-safe sanitized reason for cleanup verification failure.
_CLEANUP_FAILED_REASON = "Runtime cleanup verification failed"

# Public-safe sanitized reason for orphaned runs (cleanup failed).
_ORPHANED_REASON = "Run orphaned because cleanup verification failed"

# Public-safe sanitized reason for adapter-reported cancellation.
_CANCELLED_REASON = "Run cancelled"

# These are deliberately internal V1 safety bounds.  They are not persisted,
# configurable through the public API, or used as a silent downgrade.  A
# runtime that cannot finish inside these bounds fails closed through the
# existing timeout/cancel cleanup path.
_DEFAULT_OPERATION_TIMEOUT_SECONDS = 30.0
_DEFAULT_CLEANUP_TIMEOUT_SECONDS = 30.0
_MAX_RUN_OPERATIONS = 8
_MAX_CONCURRENT_RUNTIME_OPERATIONS = 4

_T = TypeVar("_T")


class _ResourceTimeout(Exception):
    """Internal marker for a bounded runtime operation timeout."""


class _ResourceBudgetExceeded(Exception):
    """Internal marker for a bounded per-run operation budget."""


class _WorkflowExecutionFailure(Exception):
    """Runtime workflow setup failed after optionally allocating a runtime."""

    def __init__(self, runtime_ref: str | None) -> None:
        super().__init__("workflow execution failed")
        self.runtime_ref = runtime_ref


@dataclass
class _RunResourceBudget:
    operations: int = 0
    max_operations: int = _MAX_RUN_OPERATIONS

    def consume(self) -> None:
        if self.operations >= self.max_operations:
            raise _ResourceBudgetExceeded
        self.operations += 1


class _RuntimeOperationGate:
    """One bounded runtime-operation gate per active asyncio event loop."""

    _gates: weakref.WeakKeyDictionary[Any, asyncio.Semaphore] = (
        weakref.WeakKeyDictionary()
    )

    @classmethod
    def for_current_loop(cls) -> asyncio.Semaphore:
        loop = asyncio.get_running_loop()
        gate = cls._gates.get(loop)
        if gate is None:
            gate = asyncio.Semaphore(_MAX_CONCURRENT_RUNTIME_OPERATIONS)
            cls._gates[loop] = gate
        return gate


class _GuardedRuntimeAdapter:
    """Adapter view used by workflow executors to retain the runtime ref."""

    def __init__(self, supervisor: "RunSupervisor", budget: _RunResourceBudget, run: Run) -> None:
        self._supervisor = supervisor
        self._adapter = supervisor._adapter
        self._budget = budget
        self.runtime_ref: str | None = None
        self._run = run

    async def create_run(self, context: ContextPackage) -> str:
        runtime_ref = await self._supervisor._invoke(
            lambda: self._adapter.create_run(context), self._budget
        )
        self.runtime_ref = runtime_ref
        self._run.runtime_ref = runtime_ref
        return runtime_ref

    async def submit(self, runtime_ref: str, task: Task) -> None:
        await self._supervisor._invoke(
            lambda: self._adapter.submit(runtime_ref, task), self._budget
        )

    async def status(self, runtime_ref: str):
        return await self._supervisor._invoke(
            lambda: self._adapter.status(runtime_ref), self._budget
        )

    async def result(self, runtime_ref: str):
        return await self._supervisor._invoke(
            lambda: self._adapter.result(runtime_ref), self._budget
        )

    async def cancel(self, runtime_ref: str) -> None:
        await self._supervisor._invoke(
            lambda: self._adapter.cancel(runtime_ref), self._budget
        )

    async def resume(self, runtime_ref: str, checkpoint: str | None = None) -> None:
        await self._supervisor._invoke(
            lambda: self._adapter.resume(runtime_ref, checkpoint), self._budget
        )

    async def artifacts(self, runtime_ref: str):
        return await self._supervisor._invoke(
            lambda: self._adapter.artifacts(runtime_ref), self._budget
        )

    async def cleanup(self, runtime_ref: str) -> bool:
        return await self._supervisor._invoke(
            lambda: self._adapter.cleanup(runtime_ref), self._budget
        )

    def capabilities(self):
        return self._adapter.capabilities()

    def version_info(self) -> str:
        return self._adapter.version_info()


@dataclass
class RunSession:
    run: Run
    runtime_ref: str
    _resource_budget: _RunResourceBudget | None = field(default=None, repr=False)


@dataclass(frozen=True)
class RunExecution:
    run: Run
    result: RunResult | None
    findings: tuple[Finding, ...]
    evidence: tuple[Evidence, ...]
    artifacts: tuple[Artifact, ...]


class RunSupervisor:
    """Owns normalized PolyNexus Run lifecycle around an adapter boundary."""

    def __init__(
        self,
        adapter: RuntimeAdapter,
        workflow_executor: WorkflowExecutor | None = None,
    ) -> None:
        self._adapter = adapter
        self._workflow_executor = workflow_executor or ReferenceWorkflowExecutor()

    @asynccontextmanager
    async def _runtime_slot(self):
        gate = _RuntimeOperationGate.for_current_loop()
        acquired = False
        try:
            await gate.acquire()
            acquired = True
            yield
        finally:
            if acquired:
                gate.release()

    async def _invoke(
        self,
        operation: Callable[[], Awaitable[_T]],
        budget: _RunResourceBudget,
        *,
        count_budget: bool = True,
        cleanup: bool = False,
    ) -> _T:
        """Run one adapter boundary call under a slot, timeout, and budget."""
        if count_budget:
            budget.consume()
        async with self._runtime_slot():
            try:
                return await self._wait_for_operation(
                    operation(), timeout=(
                        _DEFAULT_CLEANUP_TIMEOUT_SECONDS if cleanup
                        else _DEFAULT_OPERATION_TIMEOUT_SECONDS
                    ),
                )
            except asyncio.TimeoutError:
                raise _ResourceTimeout from None

    async def _wait_for_operation(self, operation: Awaitable[_T], *, timeout: float) -> _T:
        """Internal deadline seam; no public runtime policy or API exposure."""
        return await asyncio.wait_for(operation, timeout=timeout)

    @asynccontextmanager
    async def _cancellation_guard(self, run: Run):
        try:
            yield
        except asyncio.CancelledError:
            run.result = None
            if run.state in {RunState.STARTING, RunState.RUNNING}:
                run.transition(RunState.CANCEL_REQUESTED)
            if run.state is RunState.CANCEL_REQUESTED:
                verified = False
                if run.runtime_ref is not None:
                    async def bounded_cleanup():
                        try:
                            return await asyncio.wait_for(
                                self._cleanup_and_verify(run.runtime_ref, RunState.CANCELLED),
                                timeout=3 * _DEFAULT_CLEANUP_TIMEOUT_SECONDS,
                            )
                        except (Exception, asyncio.CancelledError):
                            return False

                    cleanup_task = asyncio.create_task(bounded_cleanup())
                    interrupted = False
                    while not cleanup_task.done():
                        try:
                            await asyncio.shield(cleanup_task)
                        except asyncio.CancelledError:
                            # A repeated caller cancellation cannot cancel verification.
                            # Conservatively retain uncertainty in the terminal state.
                            interrupted = True
                    verified = cleanup_task.result() and not interrupted
                run.transition(
                    RunState.CANCELLED if verified else RunState.ORPHANED,
                    reason=_CANCELLED_REASON if verified else _CLEANUP_FAILED_REASON,
                )
            raise

    async def _execute_workflow(
        self,
        task: Task,
        context: ContextPackage,
        workflow: WorkflowDefinition,
        budget: _RunResourceBudget,
        run: Run,
    ):
        """Execute workflow setup through the same bounded adapter boundary."""
        guarded_adapter = _GuardedRuntimeAdapter(self, budget, run)
        request = WorkflowExecutionRequest(task=task, context=context, workflow=workflow)
        try:
            # The workflow coroutine itself is bounded, while its adapter
            # calls use _invoke.  Wrapping both layers in the same semaphore
            # would deadlock when create_run/submit is called by the workflow.
            execution = await asyncio.wait_for(
                self._workflow_executor.execute(request, guarded_adapter),
                timeout=_DEFAULT_OPERATION_TIMEOUT_SECONDS,
            )
        except (asyncio.TimeoutError, _ResourceTimeout, _ResourceBudgetExceeded):
            return None, guarded_adapter.runtime_ref, True
        except Exception as exc:
            # Preserve the allocated reference so callers can run the same
            # cleanup verification path even when submit/executor fails.
            raise _WorkflowExecutionFailure(guarded_adapter.runtime_ref) from exc
        return execution, guarded_adapter.runtime_ref, False

    async def _failure_cleanup(
        self,
        run: Run,
        runtime_ref: str | None,
        budget: _RunResourceBudget,
    ) -> bool:
        """Stop partially-created runtime work before recording setup failure."""
        if runtime_ref is None:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
            return True

        cleanup_ok = await self._cleanup_and_verify(
            runtime_ref, expected_state=RunState.CANCELLED, budget=budget
        )
        if cleanup_ok:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
            return True

        if run.state in {RunState.STARTING, RunState.RUNNING}:
            run.transition(RunState.CANCEL_REQUESTED)
        if run.state is RunState.CANCEL_REQUESTED:
            run.transition(RunState.ORPHANED, reason=_CLEANUP_FAILED_REASON)
        return False

    async def _timeout_cleanup(
        self,
        run: Run,
        runtime_ref: str | None,
        budget: _RunResourceBudget,
    ) -> bool:
        """Fail closed after a guard trip, retaining legal Run transitions."""
        if runtime_ref is None:
            run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
            return False

        run.runtime_ref = runtime_ref
        cleanup_ok = await self._cleanup_and_verify(
            runtime_ref, expected_state=RunState.TIMED_OUT, budget=budget
        )
        if cleanup_ok:
            if run.state is RunState.STARTING:
                run.transition(RunState.RUNNING)
            run.transition(RunState.TIMED_OUT, reason=_TIMEOUT_CLEANUP_REASON)
            return True

        if run.state in {RunState.STARTING, RunState.RUNNING}:
            run.transition(RunState.CANCEL_REQUESTED)
        if run.state is RunState.CANCEL_REQUESTED:
            run.transition(RunState.ORPHANED, reason=_CLEANUP_FAILED_REASON)
        return False

    def _new_budget(self) -> _RunResourceBudget:
        return _RunResourceBudget(max_operations=_MAX_RUN_OPERATIONS)

    async def start(
        self,
        task: Task,
        context: ContextPackage,
        workflow: WorkflowDefinition,
    ) -> RunSession:
        if task.project_id != context.project_id:
            raise ValueError("Task and ContextPackage must belong to the same project")
        if task.workflow_id != workflow.id or task.workflow_version != workflow.version:
            raise ValueError("Task workflow reference must match the WorkflowDefinition")

        run = Run(
            task_id=task.id,
            workflow_id=workflow.id,
            workflow_version=workflow.version,
            context_package_id=context.id,
        )
        run.transition(RunState.STARTING)
        async with self._cancellation_guard(run):
            budget = self._new_budget()
            try:
                execution, runtime_ref, guard_tripped = await self._execute_workflow(
                    task, context, workflow, budget, run
                )
            except _WorkflowExecutionFailure as exc:
                cleanup_ok = await self._failure_cleanup(run, exc.runtime_ref, budget)
                reason = _RUNTIME_FAILURE_REASON if cleanup_ok else _CLEANUP_FAILED_REASON
                raise RuntimeError(reason) from None
            except Exception as exc:
                reason = redact_exception(exc, fallback=_RUNTIME_FAILURE_REASON)
                run.transition(RunState.FAILED, reason=reason)
                raise RuntimeError(reason) from None

            if guard_tripped:
                await self._timeout_cleanup(run, runtime_ref, budget)
                raise RuntimeError(
                    _TIMEOUT_CLEANUP_REASON
                    if run.state is RunState.TIMED_OUT
                    else _CLEANUP_FAILED_REASON
                ) from None

            run.runtime_ref = execution.runtime_ref
            run.transition(RunState.RUNNING)
            return RunSession(
                run=run,
                runtime_ref=execution.runtime_ref,
                _resource_budget=budget,
            )

    async def execute_claimed_run(
        self,
        run: Run,
        task: Task,
        context: ContextPackage,
        workflow: WorkflowDefinition,
    ) -> RunExecution:
        """Execute a Run that was already claimed (CREATED → STARTING via CAS).

        The caller is responsible for the CAS claim and the CREATED→STARTING
        event.  This method transitions STARTING → RUNNING → terminal.

        RunSupervisor is the sole lifecycle owner — it catches runtime-boundary
        failures from the workflow executor and adapter calls, transitions to
        FAILED with a sanitized public-safe reason, and returns RunExecution
        with result=None (no fabricated Result/Evidence/Finding/Artifact).

        Programmer/domain validation errors (ValueError) are NOT caught —
        they propagate to the caller.

        On success, all adapter boundary calls (status/result/artifacts) are
        individually wrapped so a failure in one does not leave the Run in
        an inconsistent state.
        """
        if task.project_id != context.project_id:
            raise ValueError("Task and ContextPackage must belong to the same project")
        if task.workflow_id != workflow.id or task.workflow_version != workflow.version:
            raise ValueError("Task workflow reference must match the WorkflowDefinition")

        async with self._cancellation_guard(run):
            budget = self._new_budget()
            # Workflow executor boundary: create_run + submit
            try:
                execution, runtime_ref, guard_tripped = await self._execute_workflow(
                    task, context, workflow, budget, run
                )
            except _WorkflowExecutionFailure as exc:
                await self._failure_cleanup(run, exc.runtime_ref, budget)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )
            except Exception:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            if guard_tripped:
                await self._timeout_cleanup(run, runtime_ref, budget)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            run.runtime_ref = execution.runtime_ref
            run.transition(RunState.RUNNING)

            # Adapter boundary: status call
            try:
                adapter_status = await self._invoke(
                    lambda: self._adapter.status(run.runtime_ref), budget
                )
            except (_ResourceTimeout, _ResourceBudgetExceeded):
                await self._timeout_cleanup(run, run.runtime_ref, budget)
                return RunExecution(run=run, result=None, findings=(), evidence=(), artifacts=())
            except Exception:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            if adapter_status.state is RunState.FAILED:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            if adapter_status.state is RunState.TIMED_OUT:
                # Timeout: perform cleanup/verify before transitioning
                cleanup_ok = await self._cleanup_and_verify(
                    run.runtime_ref, expected_state=RunState.TIMED_OUT, budget=budget
                )
                if cleanup_ok:
                    # Cleanup succeeded: RUNNING -> TIMED_OUT
                    run.transition(RunState.TIMED_OUT, reason=_TIMEOUT_CLEANUP_REASON)
                else:
                    # Cleanup failed: RUNNING -> CANCEL_REQUESTED -> ORPHANED
                    run.transition(RunState.CANCEL_REQUESTED)
                    run.transition(RunState.ORPHANED, reason=_CLEANUP_FAILED_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            if adapter_status.state is RunState.ORPHANED:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            if adapter_status.state is RunState.CANCELLED:
                run.transition(RunState.CANCEL_REQUESTED)
                run.transition(RunState.CANCELLED, reason=_RUNTIME_FAILURE_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            # Adapter boundary: result call
            try:
                runtime_result = await self._invoke(
                    lambda: self._adapter.result(run.runtime_ref), budget
                )
            except (_ResourceTimeout, _ResourceBudgetExceeded):
                await self._timeout_cleanup(run, run.runtime_ref, budget)
                return RunExecution(run=run, result=None, findings=(), evidence=(), artifacts=())
            except Exception:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            # Adapter boundary: artifacts call
            try:
                adapter_artifacts = await self._invoke(
                    lambda: self._adapter.artifacts(run.runtime_ref), budget
                )
            except (_ResourceTimeout, _ResourceBudgetExceeded):
                await self._timeout_cleanup(run, run.runtime_ref, budget)
                return RunExecution(run=run, result=None, findings=(), evidence=(), artifacts=())
            except Exception:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            # Guarded success preparation: fetch runtime metadata BEFORE transitioning COMPLETED
            try:
                runtime_version = self._adapter.version_info()
            except Exception:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )

            run.transition(RunState.COMPLETED)
            return self._build_execution_from_existing(
                run, runtime_result, adapter_artifacts,
                runtime_version=runtime_version,
            )

    async def execute_run(
        self,
        run: Run,
        task: Task,
        context: ContextPackage,
        workflow: WorkflowDefinition,
    ) -> RunExecution:
        """Execute an existing persisted Run through the full lifecycle.

        Unlike start(), this method uses the provided Run object instead of
        creating a new one.  It transitions CREATED → STARTING → RUNNING →
        terminal and returns the RunExecution with durable events/result.

        The caller is responsible for persisting the Run and its events.
        """
        if task.project_id != context.project_id:
            raise ValueError("Task and ContextPackage must belong to the same project")
        if task.workflow_id != workflow.id or task.workflow_version != workflow.version:
            raise ValueError("Task workflow reference must match the WorkflowDefinition")

        async with self._cancellation_guard(run):
            budget = self._new_budget()
            run.transition(RunState.STARTING)
            try:
                execution, runtime_ref, guard_tripped = await self._execute_workflow(
                    task, context, workflow, budget, run
                )
            except _WorkflowExecutionFailure as exc:
                cleanup_ok = await self._failure_cleanup(run, exc.runtime_ref, budget)
                reason = _RUNTIME_FAILURE_REASON if cleanup_ok else _CLEANUP_FAILED_REASON
                raise RuntimeError(reason) from None
            except Exception as exc:
                reason = redact_exception(exc, fallback=_RUNTIME_FAILURE_REASON)
                run.transition(RunState.FAILED, reason=reason)
                raise RuntimeError(reason) from None

            if guard_tripped:
                await self._timeout_cleanup(run, runtime_ref, budget)
                return self._build_execution_from_existing(
                    run,
                    RuntimeResult(
                        summary=(
                            _TIMEOUT_CLEANUP_REASON
                            if run.state is RunState.TIMED_OUT
                            else _CLEANUP_FAILED_REASON
                        )
                    ),
                )

            run.runtime_ref = execution.runtime_ref
            run.transition(RunState.RUNNING)

            # Collect results from the adapter
            try:
                status = await self._invoke(
                    lambda: self._adapter.status(run.runtime_ref), budget
                )
            except (_ResourceTimeout, _ResourceBudgetExceeded):
                cleanup_ok = await self._timeout_cleanup(run, run.runtime_ref, budget)
                return self._build_execution_from_existing(
                    run,
                    RuntimeResult(
                        summary=(
                            _TIMEOUT_CLEANUP_REASON
                            if cleanup_ok
                            else _CLEANUP_FAILED_REASON
                        )
                    ),
                )
            except Exception:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return self._build_execution_from_existing(
                    run, RuntimeResult(summary=_RUNTIME_FAILURE_REASON)
                )
            if status.state is RunState.FAILED:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return self._build_execution_from_existing(run, RuntimeResult(summary=_RUNTIME_FAILURE_REASON))
            if status.state is RunState.TIMED_OUT:
                # Timeout: perform cleanup/verify before transitioning
                cleanup_ok = await self._cleanup_and_verify(
                    run.runtime_ref, expected_state=RunState.TIMED_OUT, budget=budget
                )
                if cleanup_ok:
                    # Cleanup succeeded: RUNNING -> TIMED_OUT
                    run.transition(RunState.TIMED_OUT, reason=_TIMEOUT_CLEANUP_REASON)
                else:
                    # Cleanup failed: RUNNING -> CANCEL_REQUESTED -> ORPHANED
                    run.transition(RunState.CANCEL_REQUESTED)
                    run.transition(RunState.ORPHANED, reason=_CLEANUP_FAILED_REASON)
                return self._build_execution_from_existing(run, RuntimeResult(summary=_TIMEOUT_CLEANUP_REASON if cleanup_ok else _CLEANUP_FAILED_REASON))
            if status.state is RunState.ORPHANED:
                raise ValueError("Runtime reported ORPHANED before cancel cleanup")
            if status.state is RunState.CANCELLED:
                run.transition(RunState.CANCEL_REQUESTED)
                run.transition(RunState.CANCELLED, reason=_CANCELLED_REASON)
                return self._build_execution_from_existing(run, RuntimeResult(summary=_CANCELLED_REASON))

            try:
                runtime_result = await self._invoke(
                    lambda: self._adapter.result(run.runtime_ref), budget
                )
                adapter_artifacts = await self._invoke(
                    lambda: self._adapter.artifacts(run.runtime_ref), budget
                )
            except (_ResourceTimeout, _ResourceBudgetExceeded):
                cleanup_ok = await self._timeout_cleanup(run, run.runtime_ref, budget)
                return self._build_execution_from_existing(
                    run,
                    RuntimeResult(
                        summary=(
                            _TIMEOUT_CLEANUP_REASON
                            if cleanup_ok
                            else _CLEANUP_FAILED_REASON
                        )
                    ),
                )
            except Exception:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return self._build_execution_from_existing(
                    run, RuntimeResult(summary=_RUNTIME_FAILURE_REASON)
                )
            # Guarded success preparation: fetch runtime metadata BEFORE transitioning
            # COMPLETED so a version_info failure cannot leave a COMPLETED event with a
            # Run state that is later regressed to FAILED (ADR-007 lifecycle).
            try:
                runtime_version = self._adapter.version_info()
            except Exception:
                run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return RunExecution(
                    run=run,
                    result=None,
                    findings=(),
                    evidence=(),
                    artifacts=(),
                )
            run.transition(RunState.COMPLETED)
            return self._build_execution_from_existing(
                run, runtime_result, adapter_artifacts, runtime_version=runtime_version
            )

    async def collect(self, session: RunSession) -> RunExecution:
        self._require_active(session)
        async with self._cancellation_guard(session.run):
            budget = session._resource_budget or self._new_budget()
            session._resource_budget = budget
            try:
                status = await self._invoke(
                    lambda: self._adapter.status(session.runtime_ref), budget
                )
            except (_ResourceTimeout, _ResourceBudgetExceeded):
                cleanup_ok = await self._timeout_cleanup(session.run, session.runtime_ref, budget)
                return self._build_execution(
                    session,
                    RuntimeResult(
                        summary=(
                            _TIMEOUT_CLEANUP_REASON
                            if cleanup_ok
                            else _CLEANUP_FAILED_REASON
                        )
                    ),
                )
            except Exception:
                session.run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return self._build_execution(
                    session, RuntimeResult(summary=_RUNTIME_FAILURE_REASON)
                )
            if status.state is RunState.FAILED:
                session.run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return self._build_execution(session, RuntimeResult(summary=_RUNTIME_FAILURE_REASON))
            if status.state is RunState.TIMED_OUT:
                # Timeout: perform cleanup/verify before transitioning
                cleanup_ok = await self._cleanup_and_verify(
                    session.runtime_ref, expected_state=RunState.TIMED_OUT, budget=budget
                )
                if cleanup_ok:
                    # Cleanup succeeded: RUNNING -> TIMED_OUT
                    session.run.transition(RunState.TIMED_OUT, reason=_TIMEOUT_CLEANUP_REASON)
                else:
                    # Cleanup failed: RUNNING -> CANCEL_REQUESTED -> ORPHANED
                    session.run.transition(RunState.CANCEL_REQUESTED)
                    session.run.transition(RunState.ORPHANED, reason=_CLEANUP_FAILED_REASON)
                return self._build_execution(session, RuntimeResult(summary=_TIMEOUT_CLEANUP_REASON if cleanup_ok else _CLEANUP_FAILED_REASON))
            if status.state is RunState.ORPHANED:
                raise ValueError("Runtime reported ORPHANED before cancel cleanup")
            if status.state is RunState.CANCELLED:
                session.run.transition(RunState.CANCEL_REQUESTED)
                session.run.transition(RunState.CANCELLED, reason=_CANCELLED_REASON)
                return self._build_execution(session, RuntimeResult(summary=_CANCELLED_REASON))

            try:
                runtime_result = await self._invoke(
                    lambda: self._adapter.result(session.runtime_ref), budget
                )
                adapter_artifacts = await self._invoke(
                    lambda: self._adapter.artifacts(session.runtime_ref), budget
                )
            except (_ResourceTimeout, _ResourceBudgetExceeded):
                cleanup_ok = await self._timeout_cleanup(session.run, session.runtime_ref, budget)
                return self._build_execution(
                    session,
                    RuntimeResult(
                        summary=(
                            _TIMEOUT_CLEANUP_REASON
                            if cleanup_ok
                            else _CLEANUP_FAILED_REASON
                        )
                    ),
                )
            except Exception:
                session.run.transition(RunState.FAILED, reason=_RUNTIME_FAILURE_REASON)
                return self._build_execution(
                    session, RuntimeResult(summary=_RUNTIME_FAILURE_REASON)
                )
            session.run.transition(RunState.COMPLETED)
            return self._build_execution(session, runtime_result, adapter_artifacts)

    async def cancel(self, session: RunSession) -> RunExecution:
        self._require_active(session)
        async with self._cancellation_guard(session.run):
            session.run.transition(RunState.CANCEL_REQUESTED)
            # Shared cleanup/verification machinery (same standard as timeout):
            # adapter cancel/cleanup/status exceptions are contained inside
            # _cleanup_and_verify; raw errors never reach the caller or persistence.
            cleanup_ok = await self._cleanup_and_verify(
                session.runtime_ref,
                expected_state=RunState.CANCELLED,
                budget=session._resource_budget or self._new_budget(),
            )
            if cleanup_ok:
                session.run.transition(
                    RunState.CANCELLED, reason="cancelled and cleanup verified"
                )
                summary = "Run cancelled and cleanup verified"
            else:
                session.run.transition(RunState.ORPHANED, reason=_CLEANUP_FAILED_REASON)
                summary = "Run orphaned because cleanup verification failed"
            return self._build_execution(session, RuntimeResult(summary=summary))

    def _require_active(self, session: RunSession) -> None:
        if session.run.state is not RunState.RUNNING:
            raise ValueError(f"Run is not active: {session.run.state}")

    async def _cleanup_and_verify(
        self,
        runtime_ref: str,
        expected_state: RunState,
        budget: _RunResourceBudget | None = None,
    ) -> bool:
        """Shared cleanup/verification machinery for timeout and cancel paths.

        Calls adapter.cancel -> adapter.cleanup -> adapter.status and verifies
        the post-cleanup status proves owned work stopped in the expected
        terminal state. Any exception from any step is contained here and
        yields False — raw exceptions never propagate to the caller and raw
        error text is never persisted.

        Returns True only when cleanup succeeded AND the post-cleanup status
        state is exactly ``expected_state``:
          - timeout path: expected_state=RunState.TIMED_OUT
          - cancel path:  expected_state=RunState.CANCELLED
        Any other state (FAILED/ORPHANED/RUNNING/STARTING/CREATED/...) is a
        verification failure; the caller must fail closed via
        CANCEL_REQUESTED -> ORPHANED.
        """
        cleanup_budget = budget or self._new_budget()
        try:
            await self._invoke(
                lambda: self._adapter.cancel(runtime_ref),
                cleanup_budget,
                count_budget=False,
                cleanup=True,
            )
        except Exception:
            return False

        try:
            cleanup_ok = await self._invoke(
                lambda: self._adapter.cleanup(runtime_ref),
                cleanup_budget,
                count_budget=False,
                cleanup=True,
            )
        except Exception:
            return False

        try:
            status = await self._invoke(
                lambda: self._adapter.status(runtime_ref),
                cleanup_budget,
                count_budget=False,
                cleanup=True,
            )
        except Exception:
            return False

        if not cleanup_ok:
            return False

        # Fail closed unless the post-cleanup state exactly matches the
        # expected terminal state proving owned work stopped.
        if status.state is not expected_state:
            return False

        return True

    def _build_execution_from_existing(
        self,
        run: Run,
        runtime_result: RuntimeResult,
        adapter_artifacts: tuple[Artifact, ...] = (),
        runtime_version: str | None = None,
    ) -> RunExecution:
        """Build RunExecution for an existing Run (not wrapped in RunSession)."""
        if runtime_version is None:
            runtime_version = self._safe_runtime_version()
        safe_result = sanitize_runtime_result(runtime_result)
        evidence = list(safe_result.evidence)
        evidence_status = (
            EvidenceStatus.PASS
            if run.state in {RunState.COMPLETED, RunState.CANCELLED}
            else EvidenceStatus.FAIL
        )
        evidence.append(
            Evidence(
                task_id=run.task_id,
                run_id=run.id,
                actor_id="system:run-supervisor",
                source="runtime-adapter",
                type=EvidenceType.RUNTIME_EVIDENCE,
                status=evidence_status,
                metadata={"runtime_version": redact_text(runtime_version, max_length=256)},
            )
        )
        artifacts = tuple(sanitize_artifact(artifact) for artifact in safe_result.artifacts) + tuple(
            sanitize_artifact(artifact)
            for artifact in adapter_artifacts
            if artifact.id not in {item.id for item in safe_result.artifacts}
        )
        result = RunResult(
            run_id=run.id,
            status=run.state,
            summary=safe_result.summary,
            finding_ids=tuple(finding.id for finding in safe_result.findings),
            evidence_ids=tuple(item.id for item in evidence),
            artifact_ids=tuple(artifact.id for artifact in artifacts),
        )
        run.result = result
        sanitize_run(run)
        return RunExecution(
            run=run,
            result=result,
            findings=tuple(sanitize_finding(finding) for finding in safe_result.findings),
            evidence=tuple(evidence),
            artifacts=artifacts,
        )

    def _build_execution(
        self,
        session: RunSession,
        runtime_result: RuntimeResult,
        adapter_artifacts: tuple[Artifact, ...] = (),
    ) -> RunExecution:
        safe_result = sanitize_runtime_result(runtime_result)
        evidence = list(safe_result.evidence)
        evidence_status = (
            EvidenceStatus.PASS
            if session.run.state in {RunState.COMPLETED, RunState.CANCELLED}
            else EvidenceStatus.FAIL
        )
        evidence.append(
            Evidence(
                task_id=session.run.task_id,
                run_id=session.run.id,
                actor_id="system:run-supervisor",
                source="runtime-adapter",
                type=EvidenceType.RUNTIME_EVIDENCE,
                status=evidence_status,
                metadata={"runtime_version": self._safe_runtime_version()},
            )
        )
        artifacts = tuple(sanitize_artifact(artifact) for artifact in safe_result.artifacts) + tuple(
            sanitize_artifact(artifact)
            for artifact in adapter_artifacts
            if artifact.id not in {item.id for item in safe_result.artifacts}
        )
        result = RunResult(
            run_id=session.run.id,
            status=session.run.state,
            summary=safe_result.summary,
            finding_ids=tuple(finding.id for finding in safe_result.findings),
            evidence_ids=tuple(item.id for item in evidence),
            artifact_ids=tuple(artifact.id for artifact in artifacts),
        )
        session.run.result = result
        sanitize_run(session.run)
        return RunExecution(
            run=session.run,
            result=result,
            findings=tuple(sanitize_finding(finding) for finding in safe_result.findings),
            evidence=tuple(evidence),
            artifacts=artifacts,
        )

    def _safe_runtime_version(self) -> str:
        try:
            return redact_text(self._adapter.version_info(), max_length=256)
        except Exception as exc:
            return redact_exception(exc, fallback="runtime version unavailable")
