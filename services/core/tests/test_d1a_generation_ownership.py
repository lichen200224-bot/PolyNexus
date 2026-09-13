"""D1A-03/04/05: transaction and exact-target facts, not process conformance."""
import json
import subprocess
import sys
from polynexus_core.workspace.ownership import OwnedProcessRegistry
from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine,text
from sqlalchemy.orm import Session
from polynexus_core.domain.models import Project,Task,ContextPackage,Run
from polynexus_core.persistence.repository import SqlProjectRepository,SqlTaskRepository,SqlContextPackageRepository,SqlRunRepository
from polynexus_core.domain.generation import WorkGenerationRef,GenerationConflict
from polynexus_core.persistence.generation import GenerationRepository

@pytest.fixture
def generation_db(tmp_path,monkeypatch):
    monkeypatch.setenv("POLYNEXUS_CONTENT_ROOT",str(tmp_path/"content"))
    db=tmp_path/'generation.db'
    config=Config();config.set_main_option('script_location',str(Path(__file__).parents[1]/'alembic'));config.set_main_option('sqlalchemy.url','sqlite:///'+db.as_posix())
    command.upgrade(config,'head')
    engine=create_engine('sqlite:///'+db.as_posix())
    with Session(engine) as s:
        p=Project(name='synthetic');SqlProjectRepository(s).add(p);s.flush()
        cp=ContextPackage(project_id=p.id,version=1);SqlContextPackageRepository(s).add(cp);s.flush()
        t=Task(project_id=p.id,title='test',workflow_id='review-minimal',workflow_version=1,context_package_id=cp.id);SqlTaskRepository(s).add(t);s.commit()
        prepared=GenerationRepository(s).prepare(task_id=t.id,context_package_id=cp.id,requirements="synthetic requirements",validation="synthetic validation")
        s.commit()
        yield s,t,prepared
    engine.dispose()

def inputs(cp):
    return dict(cp)

def test_begin_replay_restart_and_payload_conflict(generation_db):
    s,t,cp=generation_db;r=GenerationRepository(s)
    kwargs=dict(principal='agent',command_id='begin-1',task_id=t.id,expected_revision=0,inputs=inputs(cp))
    first=r.begin(**kwargs);s.commit()
    assert GenerationRepository(s).begin(**kwargs)==first
    with pytest.raises(GenerationConflict,match='payload_conflict'):
        r.begin(**dict(kwargs,inputs=dict(inputs(cp),input_ref='different')))
    s.rollback()
    assert r.get(WorkGenerationRef(t.id,1))['inputs']==json.dumps(inputs(cp),sort_keys=True,separators=(',',':'))
    with pytest.raises(GenerationConflict,match='revision_conflict'):
        r.begin(**dict(kwargs,command_id='other'))
    s.rollback()
    assert s.execute(text('SELECT count(*) FROM work_generations')).scalar_one()==1

def test_durable_lineage_release_retry_and_late_abort(generation_db):
    s,t,cp=generation_db;r=GenerationRepository(s)
    r.begin(principal='agent',command_id='b',task_id=t.id,expected_revision=0,inputs=inputs(cp));s.commit()
    ref=WorkGenerationRef(t.id,1)
    owners=OwnedProcessRegistry()
    run=Run(task_id=t.id,workflow_id=t.workflow_id,workflow_version=1,context_package_id=cp["context_package_id"],generation_revision=1)
    SqlRunRepository(s).add(run);s.flush()
    assert r.claim(ref,run_id=run.id,lineage='writer-1',expected_control=0)==dict(fence=1,new_claim=True)
    s.commit()
    assert not r.claim(ref,run_id=run.id,lineage='writer-1',expected_control=0)['new_claim']
    with pytest.raises(GenerationConflict,match='lineage_conflict'):
        r.claim(ref,run_id=run.id,lineage='writer-2',expected_control=1)
    s.rollback()
    with pytest.raises(GenerationConflict,match='stop_unverified'):
        r.close(ref,run_id=run.id,fence=1,owned_processes=owners)
    s.execute(text("UPDATE runs SET state='FAILED' WHERE id=:id"),{'id':run.id})
    # Actual bounded controlled leaf process supplies stop evidence.
    child=subprocess.Popen([sys.executable,'-c','pass'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        owners.register_controlled_leaf(ref,run.id,1,child)
        child.wait(timeout=10)
        r.close(ref,run_id=run.id,fence=1,owned_processes=owners);s.commit()
    finally:
        if child.poll() is None:
            child.terminate();child.wait(timeout=10)
    with pytest.raises(GenerationConflict,match='not_startable'):
        r.claim(ref,run_id=run.id,lineage='unrelated',expected_control=2)
    second=r.begin(principal='agent',command_id='retry',task_id=t.id,expected_revision=1,inputs=inputs(cp),predecessor=1);s.commit()
    before=r.get(WorkGenerationRef(t.id,2))
    aborted=r.abort(ref,principal='agent',command_id='abort-old',expected_control=2);s.commit()
    assert aborted['generation_revision']==1 and aborted['work_aborted']
    assert r.get(WorkGenerationRef(t.id,2))==before
    assert second['generation_revision']==2


def test_managed_real_git_selection_preserves_original_source(tmp_path):
    import hashlib,subprocess
    from polynexus_core.workspace.managed import ManagedInputs
    from polynexus_core.storage.content import ContentStore,ContentError
    source=tmp_path/'sources';source.mkdir();repo=source/'selected';repo.mkdir()
    def git(*args):
        result=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+repo.as_posix(),'-C',str(repo),*args],capture_output=True,timeout=30)
        assert result.returncode==0,result.stderr
        return result.stdout
    git('init');git('config','user.name','Synthetic');git('config','user.email','synthetic@example.invalid')
    (repo/'tracked.txt').write_bytes(b'base');(repo/'unselected.txt').write_bytes(b'base untouched');git('add','.');git('commit','-m','synthetic base')
    (repo/'tracked.txt').write_bytes(b'staged');git('add','tracked.txt');(repo/'tracked.txt').write_bytes(b'selected actual dirty bytes')
    (repo/'unselected.txt').write_bytes(b'unselected dirty bytes');(repo/'new.txt').write_bytes(b'selected untracked')
    head=git('rev-parse','HEAD');index=(repo/'.git/index').read_bytes()
    status=git('status','--porcelain=v1','-z','--untracked-files=all')
    source_bytes={p.name:p.read_bytes() for p in repo.iterdir() if p.is_file()}
    store=ContentStore(tmp_path/'content');manager=ManagedInputs(store,source,tmp_path/'managed')
    fact=manager.inspect('selected');assert (repo/'.git/index').read_bytes()==index
    record=manager.capture('selected',fact['baseline_commit'],['tracked.txt','new.txt'])
    destination=manager.materialize(record,'workspace_synthetic1')
    assert (destination/'tracked.txt').read_bytes()==b'selected actual dirty bytes'
    assert (destination/'new.txt').read_bytes()==b'selected untracked'
    assert (destination/'unselected.txt').read_bytes()==b'base untouched'
    assert git('rev-parse','HEAD')==head and (repo/'.git/index').read_bytes()==index
    assert git('status','--porcelain=v1','-z','--untracked-files=all')==status
    assert {p.name:p.read_bytes() for p in repo.iterdir() if p.is_file()}==source_bytes
    assert record['source_index_sha256']==hashlib.sha256(index).hexdigest()
    with pytest.raises(ContentError):manager.capture('selected','0'*40,[])
    with pytest.raises(ContentError):manager.capture('selected',fact['baseline_commit'],['../escape'])


def test_generation_binding_service_reference_execution(generation_db):
    import asyncio
    from polynexus_core.execution_service import ExecutionService
    from polynexus_core.runtime.registry import RuntimeRegistry,build_reference_profile
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
    s,t,prepared=generation_db
    registry=RuntimeRegistry();registry.register(build_reference_profile(),ReferenceRuntimeAdapter)
    service=ExecutionService(s,registry)
    with pytest.raises(GenerationConflict,match='exact_generation_required'):
        asyncio.run(service.execute_task(t.id))
    assert s.execute(text('SELECT count(*) FROM runs')).scalar_one()==0
    r=GenerationRepository(s);r.begin(principal='agent',command_id='begin',task_id=t.id,expected_revision=0,inputs=prepared);s.commit()
    execution=asyncio.run(service.execute_task(t.id,generation_revision=1))
    assert execution.run.state.value=='COMPLETED'
    observed=r.observe(WorkGenerationRef(t.id,1))
    assert observed['closed'] and observed['writer']['released']
    assert execution.run.generation_revision==1
    assert any(e['kind']=='CleanupObserved' for e in observed['events'])
    assert observed['workspace']['git_observation']['state']=='NO_REPOSITORY'
    assert observed['workspace']['ownership']['fence']==observed['writer']['fence']
    with pytest.raises(GenerationConflict,match='not_startable'):
        asyncio.run(service.execute_task(t.id,generation_revision=1))
    assert s.execute(text('SELECT count(*) FROM runs')).scalar_one()==1


def test_real_owned_tree_retry_late_abort_and_registry_loss(generation_db,tmp_path):
    import time,os
    from polynexus_core.workspace.ownership import ControlledJob
    s,t,prepared=generation_db;r=GenerationRepository(s);owners=OwnedProcessRegistry();jobs=[];audit=[]
    r.begin(principal='fixture',command_id='tree-begin',task_id=t.id,expected_revision=0,inputs=prepared);s.commit()
    def launch(revision):
        ref=WorkGenerationRef(t.id,revision)
        run=r.create_run(principal='fixture',command_id='tree-run-'+str(revision),task_id=t.id,revision=revision,context_package_id=prepared['context_package_id'],expected_control=0)
        claim=r.claim(ref,run_id=run.id,lineage='tree:'+run.id,expected_control=0);s.commit()
        ready=tmp_path/('child-'+str(revision)+'.json')
        code="import subprocess,sys,time,json;from pathlib import Path;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(90)']);Path(sys.argv[1]).write_text(json.dumps({'pid':p.pid}));time.sleep(90)"
        job=ControlledJob([sys.executable,'-B','-c',code,str(ready)],tmp_path);jobs.append(job)
        deadline=time.monotonic()+10
        while not ready.exists():
            assert time.monotonic()<deadline,'owned descendant readiness timeout'
            time.sleep(.02)
        job.retain_descendant(json.loads(ready.read_text())['pid'])
        owners.register_controlled_job(ref,run.id,claim['fence'],job)
        assert len(job.facts())==2 and all(not f['stopped'] for f in job.facts())
        audit.append({'generation':revision,'started':job.facts()})
        return ref,run,claim['fence'],job
    try:
        g1,run1,f1,j1=launch(1)
        with pytest.raises(GenerationConflict,match='stop_unverified'):
            r.close(g1,run_id=run1.id,fence=f1,owned_processes=OwnedProcessRegistry())
        with pytest.raises(GenerationConflict,match='owned_handle_unknown'):
            owners.cancel(g1,run1.id,f1+1)
        with pytest.raises(GenerationConflict,match='owned_handle_unknown'):
            owners.cancel(g1,'foreign-run',f1)
        assert not r.observe(g1)['work_aborted']
        owners.cancel(g1,run1.id,f1)
        assert j1.stopped() and all(f['stopped'] and f['ended_filetime']>0 for f in j1.facts())
        audit[0]['ended']=j1.facts()
        s.execute(text("UPDATE runs SET state='CANCELLED' WHERE id=:r"),{'r':run1.id})
        r.close(g1,run_id=run1.id,fence=f1,owned_processes=owners);s.commit()
        r.begin(principal='fixture',command_id='tree-retry',task_id=t.id,expected_revision=1,inputs=prepared,predecessor=1);s.commit()
        g2,run2,f2,j2=launch(2)
        assert f2>f1
        before=r.observe(g2);identity=j2.facts()
        r.abort(g1,principal='fixture',command_id='late-tree-abort',expected_control=r.get(g1)['control_revision']);s.commit()
        owners.cancel(g1,run1.id,f1)
        assert r.observe(g2)==before
        assert j2.facts()==identity and all(not f['stopped'] for f in j2.facts())
        audit[1]['late_abort_survived']=j2.facts()
        lost=OwnedProcessRegistry()
        with pytest.raises(GenerationConflict,match='stop_unverified'):
            r.close(g2,run_id=run2.id,fence=f2,owned_processes=lost)
        assert not r.observe(g2)['work_aborted']
        assert r.claim(g2,run_id=run2.id,lineage='tree:'+run2.id,expected_control=1)['new_claim'] is False
    finally:
        for index,job in enumerate(jobs):
            job.stop(timeout=10)
            if index<len(audit):audit[index]['finally_ended']=job.facts()
            job.dispose()
        (tmp_path/'owned-process-facts.json').write_text(json.dumps(audit,indent=2))
        # The external raw log also retains facts even if fixture ACLs restrict reread.
        print('D1A_OWNED_PROCESS_FACTS='+json.dumps(audit))


def test_durable_public_cursors_survive_restart_and_reject_foreign(generation_db,monkeypatch):
    from fastapi.testclient import TestClient
    from polynexus_core.app import create_app
    import polynexus_core.api.dependencies as dependencies
    from polynexus_core.domain.enums import RunState
    s,t,prepared=generation_db
    monkeypatch.setenv('POLYNEXUS_DATABASE_URL',str(s.bind.url))
    monkeypatch.setattr(dependencies,'_LOOPBACK_TOKEN','cursor-test')
    headers={'X-Loopback-Token':'cursor-test'}
    repo=SqlRunRepository(s);run_ids=[]
    for n in range(3):
        run=Run(task_id=t.id,workflow_id=t.workflow_id,workflow_version=1,context_package_id=prepared['context_package_id'])
        for state in (RunState.STARTING,RunState.RUNNING,RunState.COMPLETED):run.transition(state)
        repo.add(run);s.flush();run_ids.append(run.id)
    generations=GenerationRepository(s);generations.begin(principal='test',command_id='cursor-begin',task_id=t.id,expected_revision=0,inputs=prepared);s.commit()
    with TestClient(create_app(),client=("127.0.0.1",50100)) as client:
        path=f'/api/v1/tasks/{t.id}/runs'
        response=client.get(path,headers=headers);assert response.status_code==200,response.text
        legacy=response.json();assert set(legacy)=={'runs'}
        first=client.get(path,params={'limit':1},headers=headers).json()
        assert len(first['runs'])==1 and first['next_cursor']
        history_path=f'/api/v1/runs/{run_ids[0]}/history'
        all_events=client.get(history_path,headers=headers).json()['events'];assert len(all_events)==3
        history=client.get(history_path,params={'limit':1},headers=headers).json()
        generation_path=f'/api/v1/tasks/{t.id}/generations'
        observed=client.get(generation_path,headers=headers).json()
        assert not observed['unchanged']
        assert client.get(path,params={'limit':1,'cursor':'invalid'},headers=headers).status_code==422
        assert client.get(history_path,params={'limit':1,'cursor':first['next_cursor']},headers=headers).status_code==422
    with TestClient(create_app(),client=("127.0.0.1",50101)) as restarted:
        seen=[first['runs'][0]['id']];cursor=first['next_cursor']
        while cursor:
            response=restarted.get(path,params={'limit':1,'cursor':cursor},headers=headers);assert response.status_code==200
            page=response.json();seen.extend(r['id'] for r in page['runs']);cursor=page['next_cursor']
        assert len(seen)==len(set(seen))==3 and set(seen)==set(run_ids)
        seen_events=[history['events'][0]['id']];cursor=history['next_cursor']
        while cursor:
            page=restarted.get(history_path,params={'limit':1,'cursor':cursor},headers=headers).json()
            seen_events.extend(e['id'] for e in page['events']);cursor=page['next_cursor']
        assert seen_events==[e['id'] for e in all_events]
        same=restarted.get(generation_path,params={'cursor':observed['cursor']},headers=headers).json()
        assert same['unchanged'] and same['cursor']==observed['cursor'] and same['generations']==observed['generations']
        assert restarted.get(generation_path,params={'cursor':first['next_cursor']},headers=headers).status_code==422
        from polynexus_core.api.schemas import encode_cursor
        unknown=encode_cursor(['task-generations:'+t.id,'not-a-durable-event'])
        assert restarted.get(generation_path,params={'cursor':unknown},headers=headers).status_code==422


def test_public_begin_reopen_concurrent_retry_and_invalid_authority(generation_db,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from fastapi.testclient import TestClient
    from polynexus_core.app import create_app
    import polynexus_core.api.dependencies as dependencies
    s,task,prepared=generation_db
    monkeypatch.setenv('POLYNEXUS_DATABASE_URL',str(s.bind.url))
    monkeypatch.setattr(dependencies,'_LOOPBACK_TOKEN','public-concurrency')
    headers={'X-Loopback-Token':'public-concurrency'};path=f'/api/v1/tasks/{task.id}/generations'
    def concurrent(client,bodies):
        barrier=Barrier(2)
        def post(body):barrier.wait(timeout=10);return client.post(path,json=body,headers=headers)
        with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(post,bodies))
    with TestClient(create_app(),client=('127.0.0.1',50110)) as client:
        foreign_project=client.post('/api/v1/projects',json={'name':'foreign refs'},headers=headers).json()['id']
        foreign_context=client.post(f'/api/v1/projects/{foreign_project}/context-packages',json={'version':1},headers=headers).json()['id']
        foreign_task=client.post(f'/api/v1/projects/{foreign_project}/tasks',json={'title':'foreign','workflow_id':'review-minimal','workflow_version':1,'context_package_id':foreign_context},headers=headers).json()['id']
        foreign_inputs=client.post(f'/api/v1/tasks/{foreign_task}/inputs',json={'context_package_id':foreign_context,'requirements':'foreign','validation':'foreign'},headers=headers).json()
        base={'command_id':'base','expected_revision':0,'inputs':prepared}
        malformed=[{},dict(prepared,input_ref='sha256:'+'0'*64),dict(prepared,extra_ref='invented'),foreign_inputs]
        for n,inputs in enumerate(malformed):
            response=client.post(path,json=dict(base,command_id='invalid-'+str(n),inputs=inputs),headers=headers)
            assert response.status_code==409,response.text
        for field,value in [('principal','Human'),('human_decision','ACCEPTED'),('assurance','PASS')]:
            response=client.post(path,json=dict(base,**{field:value}),headers=headers);assert response.status_code==422,response.text
        assert client.get(path,headers=headers).json()['generations']==[]
        responses=concurrent(client,[dict(base,command_id='begin-a'),dict(base,command_id='begin-b')])
        assert sorted(r.status_code for r in responses)==[201,409],[r.text for r in responses]
        receipt=next(r.json() for r in responses if r.status_code==201)
        replay_body=dict(base,command_id=receipt['command_id'])
        assert len(client.get(path,headers=headers).json()['generations'])==1
    with TestClient(create_app(),client=('127.0.0.1',50111)) as reopened:
        replay=reopened.post(path,json=replay_body,headers=headers);assert replay.status_code==201 and replay.json()==receipt
        conflict=reopened.post(path,json=dict(replay_body,expected_revision=1),headers=headers);assert conflict.status_code==409 and conflict.json()['detail']=='command_payload_conflict'
        abort=reopened.post(path+'/1/abort',json={'command_id':'close-one','expected_control':0},headers=headers)
        assert abort.status_code==200 and abort.json()['work_aborted']
        retry={'command_id':'same-retry','expected_revision':1,'predecessor':1,'inputs':prepared}
        responses=concurrent(reopened,[retry,retry])
        assert [r.status_code for r in responses]==[201,201],[r.text for r in responses]
        assert responses[0].json()==responses[1].json() and responses[0].json()['generation_revision']==2
        assert [g['revision'] for g in reopened.get(path,headers=headers).json()['generations']]==[1,2]
        late=reopened.post(path,json=dict(retry,command_id='late-competitor'),headers=headers);assert late.status_code==409
        assert reopened.post(path+'/2/abort',json={'command_id':'close-two','expected_control':0},headers=headers).json()['work_aborted']
        bad_predecessor=reopened.post(path,json=dict(retry,command_id='wrong-predecessor',expected_revision=2),headers=headers);assert bad_predecessor.status_code==409
    with Session(s.bind) as fresh:
        assert fresh.execute(text('SELECT count(*) FROM work_generations WHERE task_id=:t'),{'t':task.id}).scalar_one()==2
        assert set(fresh.execute(text('SELECT DISTINCT principal FROM generation_commands')).scalars())=={'loopback-controller'}
        assert fresh.execute(text('SELECT count(*) FROM runs')).scalar_one()==0


def test_public_legacy_query_new_mutation_and_frozen_authority(generation_db,monkeypatch):
    from fastapi.testclient import TestClient
    from polynexus_core.app import create_app
    from polynexus_core.domain.enums import RunState,WorkMode,ExecutionTarget
    import polynexus_core.api.dependencies as dependencies
    s,task,prepared=generation_db
    monkeypatch.setenv('POLYNEXUS_DATABASE_URL',str(s.bind.url));monkeypatch.setattr(dependencies,'_LOOPBACK_TOKEN','legacy-matrix')
    headers={'X-Loopback-Token':'legacy-matrix'}
    legacy=[]
    for terminal in (False,True):
        run=Run(task_id=task.id,workflow_id=task.workflow_id,workflow_version=1,context_package_id=prepared['context_package_id'])
        if terminal:
            for state in (RunState.STARTING,RunState.RUNNING,RunState.COMPLETED):run.transition(state)
        SqlRunRepository(s).add(run);s.flush();legacy.append(run)
    s.commit()
    with TestClient(create_app(),client=('127.0.0.1',50112)) as client:
        for run in legacy:
            before=client.get(f'/api/v1/runs/{run.id}',headers=headers);assert before.status_code==200
            assert before.json()['generation_binding_status']=='LEGACY_UNBOUND_UNVERIFIED' and before.json()['generation_revision'] is None
            executed=client.post(f'/api/v1/runs/{run.id}/execute',headers=headers)
            assert executed.status_code==(200 if run.state is RunState.COMPLETED else 409)
            assert client.get(f'/api/v1/runs/{run.id}',headers=headers).json()==before.json()
        count=len(client.get(f'/api/v1/tasks/{task.id}/runs',headers=headers).json()['runs'])
        missing=client.post(f'/api/v1/tasks/{task.id}/runs',json={'context_package_id':prepared['context_package_id']},headers=headers)
        assert missing.status_code==422
        assert len(client.get(f'/api/v1/tasks/{task.id}/runs',headers=headers).json()['runs'])==count
        for endpoint in ('human-decisions','assurance','accept'):
            response=client.post(f'/api/v1/tasks/{task.id}/{endpoint}',json={'decision':'ACCEPTED'},headers=headers);assert response.status_code in (404,405)
        assert client.get(f'/api/v1/tasks/{task.id}/generations',headers=headers).json()['generations']==[]
    assert [x.value for x in RunState]==['CREATED','STARTING','RUNNING','CANCEL_REQUESTED','COMPLETED','FAILED','TIMED_OUT','CANCELLED','ORPHANED']
    assert [x.value for x in WorkMode]==['DISCUSS','REVIEW','VALIDATE']
    assert [x.value for x in ExecutionTarget]==['LOCAL']
def test_public_rest_execution_controls_real_job_and_terminal_cancel_is_inert(generation_db,tmp_path,monkeypatch):
    import json,os,subprocess,time
    from pathlib import Path
    from fastapi.testclient import TestClient
    from polynexus_core.app import create_app
    import polynexus_core.api.dependencies as dependencies
    import polynexus_core.execution_service as execution_service_module
    from polynexus_core.domain.enums import AuthOwnership,ExecutionTarget,RunState,TransportKind,UsageVisibility
    from polynexus_core.domain.runtime_binding import RuntimeProfile
    from polynexus_core.persistence.generation import GenerationRepository
    from polynexus_core.runtime.contracts import RuntimeCapabilities,RuntimeResult,RuntimeStatus
    from polynexus_core.runtime.registry import RuntimeRegistry
    from polynexus_core.workspace.ownership import ControlledJob

    assert os.name=='nt'
    s,task,prepared=generation_db
    source_root=tmp_path/'sources';source_root.mkdir()
    work_root=tmp_path/'work'
    monkeypatch.setenv('POLYNEXUS_SOURCE_ROOT',str(source_root))
    monkeypatch.setenv('POLYNEXUS_WORK_ROOT',str(work_root))
    repo=source_root/'clean';repo.mkdir()
    def git(*args):
        result=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+repo.as_posix(),'-C',str(repo),*args],capture_output=True,timeout=30)
        assert result.returncode==0,result.stderr
        return result.stdout
    git('init');git('config','user.name','Synthetic');git('config','user.email','synthetic@example.invalid')
    (repo/'tracked.txt').write_bytes(b'clean source')
    git('add','.');git('commit','-m','clean baseline')
    baseline=git('rev-parse','HEAD').decode().strip()
    prepared=GenerationRepository(s).prepare(task_id=task.id,context_package_id=prepared['context_package_id'],requirements='real controlled job',validation='cleanup and ownership',repository='clean',baseline=baseline,selected=[])
    s.commit()

    instances=[]
    class RealJobAdapter:
        def __init__(self):
            self.runs={}
            self.submit_calls=0
            self.cleanup_calls=0
        def capabilities(self):
            return RuntimeCapabilities(cancel=True,artifacts=True,timeout_cleanup_verified=True,auth_ownership=AuthOwnership.NONE)
        async def health(self): return True
        async def readiness(self): return True
        async def create_run(self,context):
            del context
            number=len(self.runs)+1
            runtime_ref=f'controlled:{number}'
            ready=tmp_path/f'owned-{number}.json'
            child_code='import time;time.sleep(90)'
            launcher=("import json,subprocess,sys,time;from pathlib import Path;"
                      f"child=subprocess.Popen([sys.executable,'-c',{child_code!r}]);"
                      "Path(sys.argv[1]).write_text(json.dumps({'pid':child.pid}));time.sleep(90)")
            job=ControlledJob([sys.executable,'-B','-c',launcher,str(ready)],tmp_path)
            deadline=time.monotonic()+10
            while not ready.exists():
                if time.monotonic()>=deadline:
                    job.stop();job.dispose()
                    raise AssertionError('owned descendant readiness timeout')
                time.sleep(.02)
            job.retain_descendant(json.loads(ready.read_text())['pid'])
            self.runs[runtime_ref]={'job':job,'state':RunState.CREATED,'facts':None,'cleaned':False}
            return runtime_ref
        async def submit(self,runtime_ref,task):
            del task
            record=self.runs[runtime_ref]
            assert record['state'] is RunState.CREATED
            record['state']=RunState.RUNNING
            self.submit_calls+=1
        async def status(self,runtime_ref):
            return RuntimeStatus(state=self.runs[runtime_ref]['state'])
        async def result(self,runtime_ref):
            record=self.runs[runtime_ref]
            assert record['state'] is RunState.RUNNING
            record['state']=RunState.COMPLETED
            return RuntimeResult(summary='controlled job completed')
        async def cancel(self,runtime_ref):
            record=self.runs[runtime_ref]
            if record['state'] in {RunState.CREATED,RunState.STARTING,RunState.RUNNING}:
                record['job'].stop();record['state']=RunState.CANCELLED
        async def resume(self,runtime_ref,checkpoint=None):
            del runtime_ref,checkpoint
            raise NotImplementedError
        async def artifacts(self,runtime_ref):
            self.runs[runtime_ref]
            return ()
        async def cleanup(self,runtime_ref):
            record=self.runs[runtime_ref]
            self.cleanup_calls+=1
            record['job'].stop(timeout=10)
            record['facts']=record['job'].facts()
            record['job'].dispose()
            record['cleaned']=True
            return True
        def version_info(self): return 'controlled-job/1'

    profile=RuntimeProfile(provider_id='polynexus',transport_kind=TransportKind.LOCAL,runtime_id='controlled',adapter_id='builtin.controlled',execution_target=ExecutionTarget.LOCAL,runtime_profile_ref='controlled.local',profile_revision=1,auth_ownership=AuthOwnership.NONE,usage_visibility=UsageVisibility.UNAVAILABLE)
    registry=RuntimeRegistry()
    def factory():
        adapter=RealJobAdapter();instances.append(adapter);return adapter
    registry.register(profile,factory)
    monkeypatch.setattr(execution_service_module,'build_default_registry',lambda:registry)
    monkeypatch.setenv('POLYNEXUS_RUNTIME_PROFILE_REF','controlled.local')
    monkeypatch.setenv('POLYNEXUS_DATABASE_URL',str(s.bind.url))
    monkeypatch.setattr(dependencies,'_LOOPBACK_TOKEN','real-job-test')
    headers={'X-Loopback-Token':'real-job-test'}
    try:
        with TestClient(create_app(),client=('127.0.0.1',50113)) as client:
            generations_path=f'/api/v1/tasks/{task.id}/generations'
            begun=client.post(generations_path,json={'command_id':'real-begin','expected_revision':0,'inputs':prepared},headers=headers)
            assert begun.status_code==201,begun.text
            revision=begun.json()['generation_revision']
            created=client.post(f'/api/v1/tasks/{task.id}/runs',json={'command_id':'real-run','generation_revision':revision,'context_package_id':prepared['context_package_id'],'expected_control_revision':0},headers=headers)
            assert created.status_code==201,created.text
            run_id=created.json()['id']
            started=client.post(f'/api/v1/runs/{run_id}/execute',json={'command_id':'real-start','generation_revision':revision,'expected_control_revision':0},headers=headers)
            assert started.status_code==202,started.text
            run=client.get(f'/api/v1/runs/{run_id}',headers=headers)
            assert run.status_code==200 and run.json()['state']=='COMPLETED',run.text
            observed=client.get(generations_path,headers=headers).json()['generations'][0]
            assert observed['closed'] and observed['writer']['released']
            assert observed['workspace']['git_observation']['state']=='CLEAN'
            assert observed['workspace']['ownership']['state']=='RELEASED'
            assert observed['workspace']['recoverability']['state']=='RECONSTRUCTABLE'
            fence=observed['writer']['fence'];control=observed['control_revision']
            stale=client.post(f'/api/v1/runs/{run_id}/cancel',json={'command_id':'stale-cancel','generation_revision':revision,'expected_control_revision':control,'expected_fence':fence+1},headers=headers)
            assert stale.status_code==409 and stale.json()['detail']=='ownership_fence_conflict',stale.text
            after_stale=client.get(generations_path,headers=headers).json()['generations'][0]
            assert after_stale['control_revision']==control
            assert not any(event['kind']=='RunCancelRequested' for event in after_stale['events'])
            natural=client.post(f'/api/v1/runs/{run_id}/cancel',json={'command_id':'natural-cancel','generation_revision':revision,'expected_control_revision':control,'expected_fence':fence},headers=headers)
            assert natural.status_code==200,natural.text
            assert natural.json()['cancel_requested'] is False and natural.json()['control_revision']==control
            after=client.get(generations_path,headers=headers).json()['generations'][0]
            assert after['control_revision']==control
            assert not any(event['kind']=='RunCancelRequested' for event in after['events'])
            assert client.get(f'/api/v1/runs/{run_id}',headers=headers).json()['state']=='COMPLETED'
        assert len(instances)==1
        adapter=instances[0]
        assert adapter.submit_calls==1 and adapter.cleanup_calls==1
        record=next(iter(adapter.runs.values()))
        assert record['cleaned'] and len(record['facts'])==2
        assert all(fact['stopped'] and fact['ended_filetime']>0 for fact in record['facts'])
    finally:
        for adapter in instances:
            for record in adapter.runs.values():
                if not record['cleaned']:
                    record['job'].stop(timeout=10)
                    record['job'].dispose()
