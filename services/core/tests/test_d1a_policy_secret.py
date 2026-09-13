"""D1A-08 dedicated synthetic OS-store and existing policy truth."""
import json
import pytest
from polynexus_core.security.secret_refs import OsSecretStore,SecretRef,SecretStoreError
from polynexus_core.runtime.routing_policy import evaluate_egress_policy,PolicyDecision,DataClassification


def test_actual_os_secret_roundtrip_and_no_plaintext_storage(tmp_path):
    store=OsSecretStore(tmp_path/'isolated-os-store')
    value=b'D1a-Synthetic-Canary-Only-4fded90'
    ref=store.put(value)
    try:
        assert store.resolve(ref)==value
        assert value not in next(store.root.iterdir()).read_bytes()
        assert value.decode() not in repr(ref)
        assert value.decode() not in json.dumps({'secret_ref':ref.reference})
        with pytest.raises(SecretStoreError) as error:
            store.resolve(SecretRef('secretref:'+'0'*32))
        assert value.decode() not in str(error.value)
    finally:
        store.remove(ref)
    assert list(store.root.iterdir())==[]


@pytest.mark.parametrize('mode',['STANDARD','LOCAL_PREFERRED','LOCAL_ONLY'])
def test_highest_classification_and_local_route(mode):
    result=evaluate_egress_policy(classifications=['PUBLIC','CONFIDENTIAL','INTERNAL'],execution_mode=mode,destination_trust='LOOPBACK',tool_trust='TRUSTED_REGISTERED',local_available=True,side_effect=True)
    assert result.classification is DataClassification.CONFIDENTIAL
    assert result.decision is PolicyDecision.ALLOW


def test_external_local_only_and_no_silent_fallback():
    denied=evaluate_egress_policy(classifications=['PUBLIC'],execution_mode='LOCAL_ONLY',destination_trust='TRUSTED_EXTERNAL',tool_trust='TRUSTED_REGISTERED',local_available=True,side_effect=True)
    assert denied.decision is PolicyDecision.DENY
    fallback=evaluate_egress_policy(classifications=['PUBLIC','CONFIDENTIAL'],execution_mode='LOCAL_PREFERRED',destination_trust='TRUSTED_EXTERNAL',tool_trust='TRUSTED_REGISTERED',local_available=False,side_effect=False)
    assert fallback.classification is DataClassification.CONFIDENTIAL
    assert fallback.decision is PolicyDecision.APPROVAL_REQUIRED
    assert fallback.route=='MANUAL'
    evidence=fallback.as_evidence(task_id='task_policy',run_id='run_policy',generation_revision=1,actor_id='core-policy')
    assert evidence.status.value=='NEED_ACTION'
    assert evidence.status.value not in {'HUMAN_DECISION','HUMAN_APPROVED'}


def test_secret_dispatch_scoped_redaction_and_cleanup(tmp_path,monkeypatch):
    from polynexus_core.security.secret_refs import secret_dispatch_scope,active_secret
    from polynexus_core.runtime.redaction import redact_text,redact_value
    import base64
    store=OsSecretStore(tmp_path/'dispatch-store');monkeypatch.setenv('POLYNEXUS_SECRET_ROOT',str(store.root))
    canary=b'OnlySyntheticCanary9q7c3p8x';ref=store.put(canary)
    try:
        with secret_dispatch_scope(ref.reference):
            assert active_secret()==canary
            ordinary={'event':canary.decode(),'log':base64.b64encode(canary).decode(),'artifact':canary.hex(),'export':canary.decode()[3:14]}
            sanitized=json.dumps(redact_value(ordinary))
            assert canary.decode() not in sanitized and canary.hex() not in sanitized
            assert canary.decode()[3:11] not in sanitized
            with pytest.raises(RuntimeError):
                with secret_dispatch_scope(ref.reference):raise RuntimeError('synthetic failure')
            assert active_secret()==canary
        with pytest.raises(SecretStoreError,match='outside_dispatch'):active_secret()
        assert all(canary not in p.read_bytes() for p in store.root.iterdir())
    finally:store.remove(ref)


def test_secret_ref_adapter_output_never_persists_plaintext(tmp_path,monkeypatch):
    import asyncio
    from sqlalchemy import create_engine,text
    from sqlalchemy.orm import Session
    from d1a_fixtures import migrate_fixture_engine
    from polynexus_core.domain.models import Project,Task,ContextPackage
    from polynexus_core.persistence.repository import SqlProjectRepository,SqlTaskRepository,SqlContextPackageRepository
    from polynexus_core.persistence.generation import GenerationRepository
    from polynexus_core.execution_service import ExecutionService
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
    from polynexus_core.runtime.contracts import RuntimeResult
    from polynexus_core.security.secret_refs import active_secret
    store=OsSecretStore(tmp_path/'os-store');monkeypatch.setenv('POLYNEXUS_SECRET_ROOT',str(store.root));monkeypatch.setenv('POLYNEXUS_CONTENT_ROOT',str(tmp_path/'content'))
    canary=b'UnloggedSyntheticValue9zk84m';ref=store.put(canary)
    db=tmp_path/'secret.db';engine=create_engine('sqlite:///'+db.as_posix());migrate_fixture_engine(engine)
    class Echo(ReferenceRuntimeAdapter):
        async def result(self,runtime_ref):
            await super().result(runtime_ref)
            return RuntimeResult(summary=active_secret().decode())
    try:
        with Session(engine) as session:
            project=Project(name='Synthetic');SqlProjectRepository(session).add(project);session.flush()
            cp=ContextPackage(project_id=project.id,version=1);SqlContextPackageRepository(session).add(cp);session.flush()
            task=Task(project_id=project.id,title='Secret fixture',workflow_id='review-minimal',workflow_version=1,context_package_id=cp.id);SqlTaskRepository(session).add(task);session.commit()
            repo=GenerationRepository(session);inputs=repo.prepare(task_id=task.id,context_package_id=cp.id,requirements='synthetic requirements',validation='synthetic validation',secret_ref=ref.reference)
            repo.begin(principal='fixture',command_id='secret-begin',task_id=task.id,expected_revision=0,inputs=inputs);session.commit()
            from polynexus_core.runtime.registry import RuntimeRegistry,build_reference_profile
            registry=RuntimeRegistry();registry.register(build_reference_profile(),Echo)
            execution=asyncio.run(ExecutionService(session,registry=registry).execute_task(task.id,generation_revision=1))
            assert canary.decode() not in execution.result.summary
            assert '[REDACTED]' in execution.result.summary
            from polynexus_core.persistence.repository import SqlEvidenceRepository
            audits=[e for e in SqlEvidenceRepository(session).list_by_run(execution.run.id) if e.source=='runtime.routing_policy']
            assert len(audits)==1
            assert audits[0].status.value=='PASS'
            assert audits[0].metadata['generation_revision']=='1'
            assert audits[0].metadata['route']=='LOCAL'
            assert audits[0].metadata['tool_trust']=='TRUSTED_REGISTERED'
            assert audits[0].metadata['side_effect']=='True'
            assert canary.decode() not in str(session.execute(text('SELECT record FROM prepared_inputs')).all())
        engine.dispose()
        assert canary not in db.read_bytes()
        assert all(canary not in p.read_bytes() for p in (tmp_path/'content').iterdir())
    finally:
        engine.dispose();store.remove(ref)


def _seed_created_run(tmp_path,monkeypatch,*,secret_ref=None):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from d1a_fixtures import migrate_fixture_engine
    from polynexus_core.domain.models import Project,Task,ContextPackage
    from polynexus_core.persistence.repository import SqlProjectRepository,SqlTaskRepository,SqlContextPackageRepository
    from polynexus_core.persistence.generation import GenerationRepository
    monkeypatch.setenv('POLYNEXUS_CONTENT_ROOT',str(tmp_path/'content'))
    engine=create_engine('sqlite:///'+(tmp_path/'policy.db').as_posix());migrate_fixture_engine(engine)
    with Session(engine) as session:
        project=Project(name='Policy');SqlProjectRepository(session).add(project);session.flush()
        context=ContextPackage(project_id=project.id,version=1);SqlContextPackageRepository(session).add(context);session.flush()
        task=Task(project_id=project.id,title='Policy run',workflow_id='review-minimal',workflow_version=1,context_package_id=context.id);SqlTaskRepository(session).add(task);session.commit()
        generations=GenerationRepository(session)
        inputs=generations.prepare(task_id=task.id,context_package_id=context.id,requirements='policy requirements',validation='policy validation',secret_ref=secret_ref)
        generations.begin(principal='fixture',command_id='begin-policy',task_id=task.id,expected_revision=0,inputs=inputs)
        run=generations.create_run(principal='loopback-controller',command_id='create-policy',task_id=task.id,revision=1,context_package_id=context.id,expected_control=0)
        session.commit()
        return engine,task.id,run.id


def test_untrusted_forged_profile_denial_is_durable_and_replay_does_not_dispatch(tmp_path,monkeypatch):
    import asyncio
    from dataclasses import replace
    from fastapi import HTTPException
    from sqlalchemy.orm import Session
    from polynexus_core.api.schemas import RunStart
    from polynexus_core.api import runs as runs_api
    from polynexus_core.domain.enums import RunState
    from polynexus_core.domain.generation import GenerationConflict,WorkGenerationRef
    from polynexus_core.execution_service import ExecutionService
    from polynexus_core.persistence.generation import GenerationRepository
    from polynexus_core.persistence.repository import SqlEvidenceRepository,SqlRunRepository,SqlRuntimeBindingSnapshotRepository
    from polynexus_core.runtime.registry import RuntimeRegistry,build_reference_profile
    engine,task_id,run_id=_seed_created_run(tmp_path,monkeypatch)
    factory_calls=[]
    registry=RuntimeRegistry();registered=build_reference_profile()
    registry.register(registered,lambda: factory_calls.append('factory'))
    forged=replace(registered,runtime_profile_ref='forged.local')
    registry._resolve_selected_profile=lambda:forged
    with Session(engine) as session:
        run=SqlRunRepository(session).get(run_id)
        GenerationRepository(session).start_command(run,principal='loopback-controller',command_id='start-denied',revision=1,expected_control=0,record=True)
        with pytest.raises(GenerationConflict,match='^predispatch_policy_denied$'):
            asyncio.run(ExecutionService(session,registry=registry).execute_existing_run(run_id))
    with Session(engine) as session:
        run=SqlRunRepository(session).get(run_id)
        assert run.state is RunState.CREATED
        assert SqlRuntimeBindingSnapshotRepository(session).get_by_run(run_id) is None
        assert GenerationRepository(session).observe(WorkGenerationRef(task_id,1))['writer'] is None
        audits=[e for e in SqlEvidenceRepository(session).list_by_run(run_id) if e.source=='runtime.routing_policy']
        assert len(audits)==1 and audits[0].status.value=='FAIL'
        assert audits[0].metadata['decision']=='DENY'
        assert audits[0].metadata['tool_trust']=='UNTRUSTED'
        async def forbidden_dispatch(*_args,**_kwargs):
            raise AssertionError('replay dispatched')
        monkeypatch.setattr(runs_api.ExecutionService,'execute_existing_run',forbidden_dispatch)
        with pytest.raises(HTTPException) as replay_error:
            asyncio.run(runs_api.execute_run(run_id,None,session,RunStart(generation_revision=1,expected_control_revision=0,command_id='start-denied')))
        assert replay_error.value.status_code==409
        assert replay_error.value.detail=='predispatch_policy_denied'
    assert factory_calls==[]
    engine.dispose()


def test_missing_secret_stops_before_adapter_methods_and_keeps_safe_policy_audit(tmp_path,monkeypatch):
    import asyncio
    from sqlalchemy.orm import Session
    from polynexus_core.domain.generation import GenerationConflict
    from polynexus_core.execution_service import ExecutionService
    from polynexus_core.persistence.repository import SqlEvidenceRepository,SqlRunRepository
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
    from polynexus_core.runtime.registry import RuntimeRegistry,build_reference_profile
    store=OsSecretStore(tmp_path/'missing-secret-store');monkeypatch.setenv('POLYNEXUS_SECRET_ROOT',str(store.root))
    ref=store.put(b'MissingSecretCanary7x2p')
    engine,task_id,_run_id=_seed_created_run(tmp_path,monkeypatch,secret_ref=ref.reference)
    store.remove(ref);method_calls=[]
    class CountingAdapter(ReferenceRuntimeAdapter):
        async def create_run(self,context):
            method_calls.append('create_run');return await super().create_run(context)
    registry=RuntimeRegistry();registry.register(build_reference_profile(),CountingAdapter)
    with Session(engine) as session:
        with pytest.raises(GenerationConflict,match='^secret_reference_unavailable$'):
            asyncio.run(ExecutionService(session,registry=registry).execute_task(task_id,generation_revision=1))
        run=SqlRunRepository(session).list_by_task(task_id)[-1]
        audits=[e for e in SqlEvidenceRepository(session).list_by_run(run.id) if e.source=='runtime.routing_policy']
        assert len(audits)==1 and audits[0].status.value=='PASS'
        assert 'MissingSecretCanary7x2p' not in json.dumps(audits[0].metadata)
    assert method_calls==[]
    engine.dispose()


def test_factory_exception_canary_is_not_persisted_in_policy_audit(tmp_path,monkeypatch):
    import asyncio
    from sqlalchemy.orm import Session
    from polynexus_core.domain.runtime_binding import RuntimeBindingError
    from polynexus_core.execution_service import ExecutionService
    from polynexus_core.persistence.repository import SqlEvidenceRepository,SqlRunRepository
    from polynexus_core.runtime.registry import RuntimeRegistry,build_reference_profile
    engine,task_id,_run_id=_seed_created_run(tmp_path,monkeypatch)
    canary='FactoryExceptionCanary6m9q'
    def failing_factory():raise RuntimeError(canary)
    registry=RuntimeRegistry();registry.register(build_reference_profile(),failing_factory)
    with Session(engine) as session:
        with pytest.raises(RuntimeBindingError,match='^Runtime adapter construction failed$'):
            asyncio.run(ExecutionService(session,registry=registry).execute_task(task_id,generation_revision=1))
        run=SqlRunRepository(session).list_by_task(task_id)[-1]
        audits=[e for e in SqlEvidenceRepository(session).list_by_run(run.id) if e.source=='runtime.routing_policy']
        assert len(audits)==1 and audits[0].status.value=='PASS'
        assert canary not in json.dumps(audits[0].metadata)
    engine.dispose()
    assert canary.encode() not in (tmp_path/'policy.db').read_bytes()
