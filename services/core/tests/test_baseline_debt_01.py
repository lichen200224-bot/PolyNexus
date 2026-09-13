"""ADR-014 adversarial regressions; original red repro identities retained."""

from dataclasses import replace
from datetime import datetime, timezone
import asyncio

from d1a_fixtures import d1a_content_environment,prepare_generation,migrate_fixture_engine
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.models import ContextPackage, Project, Run, Task
from polynexus_core.persistence.models import Base
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlProjectRepository,
    SqlRunEventRepository,
    SqlRunRepository,
    SqlTaskRepository,
)


@pytest.mark.parametrize("write_path", ["add", "update", "append", "event_repository"])
@pytest.mark.parametrize("read_path", ["get", "list_by_task", "list_by_run"])
def test_equal_timestamp_reverse_ids_preserve_append_order(tmp_path, write_path, read_path):
    url = f"sqlite:///{tmp_path / 'ordering.db'}"
    engine = create_engine(url)
    # Test fixture only; Alembic remains the production migration authority.
    Base.metadata.create_all(engine)
    project = Project(name="Ordering repro")
    context = ContextPackage(project_id=project.id, version=1)
    task = Task(project_id=project.id, title="Ordering", workflow_id="review-minimal",
                workflow_version=1, context_package_id=context.id)
    run = Run(task_id=task.id, workflow_id=task.workflow_id, workflow_version=1,
              context_package_id=context.id)
    stamp = datetime(2026, 9, 12, tzinfo=timezone.utc)
    for state, identity in zip(
        [RunState.STARTING, RunState.RUNNING, RunState.COMPLETED],
        ["event_z", "event_m", "event_a"],
    ):
        event = run.transition(state)
        run.events[-1] = replace(event, id=identity, occurred_at=stamp)
    run.updated_at = stamp
    expected = [(event.id, event.from_state, event.to_state) for event in run.events]
    try:
        with Session(engine) as session:
            SqlProjectRepository(session).add(project)
            session.flush()
            SqlContextPackageRepository(session).add(context)
            SqlTaskRepository(session).add(task)
            session.flush()
            repo = SqlRunRepository(session)
            if write_path == "add":
                repo.add(run)
            else:
                repo.add(replace(run, events=[]))
                session.flush()
                if write_path == "update":
                    repo.update(run)
                else:
                    for event in run.events:
                        if write_path == "append":
                            repo.append_event(event)
                        else:
                            SqlRunEventRepository(session).add(event)
            session.commit()
    finally:
        engine.dispose()

    # New engine and session: no Python event-list or identity-map order survives.
    reopened = create_engine(url)
    try:
        with Session(reopened) as session:
            repo = SqlRunRepository(session)
            if read_path == "get":
                events = repo.get(run.id).events
            elif read_path == "list_by_task":
                events = repo.list_by_task(task.id)[0].events
            else:
                events = SqlRunEventRepository(session).list_by_run(run.id)
            assert [(event.id, event.from_state, event.to_state) for event in events] == expected
    finally:
        reopened.dispose()


def test_outer_collect_cancellation_does_not_leave_active_runtime():
    from test_wp24_resource_guards import GuardProbeAdapter, WORKFLOW, _inputs
    from polynexus_core.runtime.supervisor import RunSupervisor

    async def scenario():
        entered = asyncio.Event()
        stopped = asyncio.Event()

        class BlockingStatusAdapter(GuardProbeAdapter):
            async def status(self, runtime_ref):
                if not entered.is_set():
                    entered.set()
                    try:
                        await asyncio.Event().wait()
                    finally:
                        stopped.set()
                return await super().status(runtime_ref)

        adapter = BlockingStatusAdapter(cancel_state=RunState.CANCELLED)
        task, context = _inputs()
        supervisor = RunSupervisor(adapter)
        session = await supervisor.start(task, context, WORKFLOW)
        collecting = asyncio.create_task(supervisor.collect(session))
        await entered.wait()
        collecting.cancel()
        with pytest.raises(asyncio.CancelledError):
            await collecting
        assert stopped.is_set(), "cancel must reach the blocked operation"
        assert session.run.state in {RunState.CANCELLED, RunState.ORPHANED}
        if session.run.state is RunState.CANCELLED:
            assert adapter.cleanup_called and not adapter.active
        assert session.run.result is None

    asyncio.run(scenario())


@pytest.mark.parametrize("entry", ["task", "existing", "claimed"])
@pytest.mark.parametrize("case", ["success", "false", "exception", "timeout", "mismatch", "unknown_ref", "starting", "second"])
def test_service_cancellation_durable_after_reopen(tmp_path, monkeypatch, entry, case):
    from sqlalchemy import text
    from test_wp24_resource_guards import GuardProbeAdapter, WORKFLOW, _inputs
    from polynexus_core.execution_service import ExecutionService
    from polynexus_core.runtime import supervisor as module
    from polynexus_core.runtime.registry import RuntimeRegistry, build_reference_profile

    path = tmp_path / 'cancel.db'
    engine = create_engine(f'sqlite:///{path}')
    migrate_fixture_engine(engine)
    task, context = _inputs()
    context=replace(context,source_refs=(),instructions=(*context.instructions,"fixture:wp24"))
    with Session(engine) as s:
        SqlProjectRepository(s).add(Project(id=task.project_id, name='Cancellation'))
        s.flush()
        SqlContextPackageRepository(s).add(context)
        SqlTaskRepository(s).add(task)
        prepare_generation(s,task.id)
        s.commit()

    async def scenario():
        entered = asyncio.Event()
        cleanup_entered = asyncio.Event()
        release = asyncio.Event()
        trace = []

        class Probe(GuardProbeAdapter):
            async def create_run(self, context):
                if case == 'unknown_ref':
                    self.active = True
                    entered.set()
                    await asyncio.Event().wait()
                return await super().create_run(context)

            async def submit(self, runtime_ref, task):
                if case == 'starting':
                    entered.set()
                    await asyncio.Event().wait()
                await super().submit(runtime_ref, task)

            async def status(self, runtime_ref):
                if not entered.is_set():
                    entered.set()
                    await asyncio.Event().wait()
                trace.append('verify')
                if case == 'mismatch':
                    self.state = RunState.RUNNING
                return await super().status(runtime_ref)

            async def cancel(self, runtime_ref):
                trace.append('cancel')
                await super().cancel(runtime_ref)

            async def cleanup(self, runtime_ref):
                trace.append('cleanup')
                self.cleanup_called = True
                cleanup_entered.set()
                if case == 'exception':
                    raise RuntimeError('PRIVATE_CLEANUP_MARKER')
                if case == 'false':
                    return False
                if case == 'timeout':
                    await asyncio.Event().wait()
                if case == 'second':
                    await release.wait()
                return await super().cleanup(runtime_ref)

        adapter = Probe(cancel_state=RunState.CANCELLED)
        registry = RuntimeRegistry()
        registry.register(build_reference_profile(), lambda: adapter)
        if case == 'timeout':
            original = module.RunSupervisor._wait_for_operation
            monkeypatch.setattr(module, '_DEFAULT_CLEANUP_TIMEOUT_SECONDS', 0.01)

            async def controlled(self, operation, *, timeout):
                if operation.cr_code.co_name == 'cleanup':
                    pending = asyncio.create_task(operation)
                    await cleanup_entered.wait()
                    assert timeout == 0.01
                    return await original(self, pending, timeout=0)
                return await original(self, operation, timeout=timeout)

            monkeypatch.setattr(module.RunSupervisor, '_wait_for_operation', controlled)
        with Session(engine) as s:
            service = ExecutionService(s, registry)
            if entry == 'task':
                operation = service.execute_task(task.id, generation_revision=1)
            else:
                run = Run(task_id=task.id, workflow_id=WORKFLOW.id,
                          workflow_version=WORKFLOW.version, context_package_id=context.id,generation_revision=1)
                SqlRunRepository(s).add(run)
                s.commit()
                if entry == 'existing':
                    operation = service.execute_existing_run(run.id)
                else:
                    run, profile = service.prepare_claimed_run(run, task, context, WORKFLOW)
                    operation = service.execute_claimed_run(run, task, context, WORKFLOW, profile)
            pending = asyncio.create_task(operation)
            await entered.wait()
            pending.cancel('original cancellation')
            if case == 'second':
                await cleanup_entered.wait()
                pending.cancel('second cancellation')
                release.set()
            with pytest.raises(asyncio.CancelledError, match='original cancellation'):
                await pending
            if case in {'success', 'starting'}:
                assert trace == ['cancel','cleanup','verify']
                assert not adapter.active
            elif case == 'unknown_ref':
                assert trace == [] and adapter.active

    try:
        asyncio.run(asyncio.wait_for(scenario(),timeout=30))
    finally:
        engine.dispose()
    reopened = create_engine(f'sqlite:///{path}')
    try:
        with Session(reopened) as s:
            run = SqlRunRepository(s).list_by_task(task.id)[0]
            expected = RunState.CANCELLED if case in {'success','starting'} else RunState.ORPHANED
            assert run.state is expected
            assert run.result is None
            assert [e.to_state for e in run.events][-2:] == [RunState.CANCEL_REQUESTED, expected]
            assert 'PRIVATE_CLEANUP_MARKER' not in repr(run)
            for table in ['evidence','artifacts','findings']:
                assert s.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one() == 0
    finally:
        reopened.dispose()


def test_operation_override_does_not_shorten_cleanup(monkeypatch):
    from test_wp24_resource_guards import GuardProbeAdapter, _active_session
    from polynexus_core.runtime import supervisor as module

    adapter = GuardProbeAdapter(cancel_state=RunState.CANCELLED)
    supervisor = module.RunSupervisor(adapter)
    observed = []
    original = supervisor._wait_for_operation
    monkeypatch.setattr(module, '_DEFAULT_OPERATION_TIMEOUT_SECONDS', 0.001)

    async def observe(operation, *, timeout):
        observed.append(timeout)
        return await original(operation, timeout=timeout)

    monkeypatch.setattr(supervisor, '_wait_for_operation', observe)
    execution = asyncio.run(supervisor.cancel(_active_session(adapter)))
    assert execution.run.state is RunState.CANCELLED
    assert observed == [module._DEFAULT_CLEANUP_TIMEOUT_SECONDS] * 3


@pytest.mark.parametrize('failure', ['update', 'commit'])
def test_cancellation_persistence_failure_rolls_back(tmp_path, monkeypatch, failure):
    from polynexus_core.execution_service import ExecutionService
    from polynexus_core.runtime.registry import RuntimeRegistry
    engine = create_engine(f"sqlite:///{tmp_path / 'rollback.db'}")
    Base.metadata.create_all(engine)
    project = Project(name='rollback')
    task = Task(project_id=project.id,title='rollback',workflow_id='review-minimal',
                workflow_version=1,context_package_id='cp')
    run = Run(task_id=task.id,workflow_id=task.workflow_id,workflow_version=1,context_package_id='cp')
    with Session(engine) as session:
        SqlProjectRepository(session).add(project)
        session.flush()
        SqlTaskRepository(session).add(task)
        session.flush()
        SqlRunRepository(session).add(run)
        session.commit()
        service = ExecutionService(session, RuntimeRegistry())
        class CancelledSupervisor:
            async def execute_claimed_run(self, run, *args):
                for state in [RunState.STARTING,RunState.CANCEL_REQUESTED,RunState.ORPHANED]:
                    run.transition(state)
                raise asyncio.CancelledError('caller')
        def fail(*args):
            raise RuntimeError('persistence unavailable')
        monkeypatch.setattr(service._run_repo if failure=='update' else session,
                            'update' if failure=='update' else 'commit', fail)
        with pytest.raises(RuntimeError,match='persistence unavailable'):
            asyncio.run(service._execute_with_cancellation_persistence(
                CancelledSupervisor(),run,task,None,None))
        assert not session.in_transaction()
    with Session(engine) as session:
        saved = SqlRunRepository(session).get(run.id)
        assert saved.state is RunState.CREATED
        assert saved.events == []
    engine.dispose()
