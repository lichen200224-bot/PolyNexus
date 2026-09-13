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
    result=evaluate_egress_policy(classifications=['PUBLIC','CONFIDENTIAL','INTERNAL'],execution_mode=mode,destination_trust='LOOPBACK',local_available=True)
    assert result.classification is DataClassification.CONFIDENTIAL
    assert result.decision is PolicyDecision.ALLOW


def test_external_local_only_and_no_silent_fallback():
    denied=evaluate_egress_policy(classifications=['PUBLIC'],execution_mode='LOCAL_ONLY',destination_trust='TRUSTED_EXTERNAL',local_available=True,side_effect=True)
    assert denied.decision is PolicyDecision.DENY
    fallback=evaluate_egress_policy(classifications=['PUBLIC','CONFIDENTIAL'],execution_mode='LOCAL_PREFERRED',destination_trust='TRUSTED_EXTERNAL',local_available=False)
    assert fallback.classification is DataClassification.CONFIDENTIAL
    assert fallback.decision is PolicyDecision.APPROVAL_REQUIRED
    assert fallback.route=='MANUAL'


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
            assert canary.decode() not in str(session.execute(text('SELECT record FROM prepared_inputs')).all())
        engine.dispose()
        assert canary not in db.read_bytes()
        assert all(canary not in p.read_bytes() for p in (tmp_path/'content').iterdir())
    finally:
        engine.dispose();store.remove(ref)
