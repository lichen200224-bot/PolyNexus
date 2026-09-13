"""Transactional generation/command/lineage mapping.

Methods participate in the caller's transaction and never launch processes.
The authenticated boundary supplies principal; request bodies cannot select it.
"""
from __future__ import annotations
import hashlib
import json
from sqlalchemy import text
from polynexus_core.domain.generation import WorkGenerationRef, GenerationConflict


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class GenerationRepository:
    def __init__(self, session):
        self.session = session

    def reserve_task_write(self, task_id):
        from polynexus_core.persistence.repository import SqlProjectRepository
        project_id=self.session.execute(text('SELECT project_id FROM tasks WHERE id=:t'),{'t':task_id}).scalar_one_or_none()
        if project_id is None:raise GenerationConflict('task_not_found')
        if not SqlProjectRepository(self.session).reserve_write(project_id):raise GenerationConflict('project_archived')

    def prepare(self, *, task_id, context_package_id, requirements, validation, repository=None, baseline=None, selected=(), execution_mode='STANDARD', secret_ref=None):
        from dataclasses import asdict
        from polynexus_core.persistence.repository import SqlTaskRepository,SqlContextPackageRepository,SqlProjectRepository,SqlArtifactRepository
        from polynexus_core.storage.content import ContentStore,ContentError
        from polynexus_core.workspace.managed import ManagedInputs,canonical,snapshot
        import os
        from pathlib import Path
        self.reserve_task_write(task_id)
        task=SqlTaskRepository(self.session).get(task_id);context=SqlContextPackageRepository(self.session).get(context_package_id)
        if task is None or context is None or context.project_id!=task.project_id:raise GenerationConflict('input_context_scope_mismatch')
        from polynexus_core.runtime.routing_policy import validate_execution_mode
        execution_mode=validate_execution_mode(execution_mode).value
        if not requirements.strip() or not validation.strip():raise GenerationConflict('input_requirements_missing')
        store=ContentStore(Path(os.environ['POLYNEXUS_CONTENT_ROOT']))
        artifacts=SqlArtifactRepository(self.session)
        artifact_records=[]
        for reference in dict.fromkeys((*context.artifact_refs,*context.prior_decision_refs,*context.memory_refs)):
            artifact=artifacts.get(reference)
            if artifact is None or artifact.project_id!=task.project_id:raise GenerationConflict('input_artifact_scope_mismatch')
            store.read_artifact(artifact)
            artifact_records.append(asdict(artifact))
        if secret_ref is not None:
            from polynexus_core.security.secret_refs import SecretRef,OsSecretStore,SecretStoreError
            try:
                secret_root=os.environ.get('POLYNEXUS_SECRET_ROOT')
                if not secret_root:raise SecretStoreError('secret_store_not_configured')
                OsSecretStore(Path(secret_root)).validate(SecretRef(secret_ref))
            except SecretStoreError:raise GenerationConflict('secret_reference_unavailable') from None
        req=store.put(requirements.encode());val=store.put(validation.encode())
        if repository:
            manager=ManagedInputs(store,Path(os.environ['POLYNEXUS_SOURCE_ROOT']),Path(os.environ['POLYNEXUS_WORK_ROOT']))
            source=manager.capture(repository,baseline,list(selected))
        else:
            if selected or baseline:raise GenerationConflict('input_repository_required')
            source={'baseline':snapshot([]),'input':snapshot([]),'repository':None,'baseline_commit':None,'selected':[]}
        project=SqlProjectRepository(self.session).get(task.project_id)
        if project.archived:raise GenerationConflict('project_archived')
        if not set(context.source_refs) <= {e['path'] for e in source['input']['entries']}:raise GenerationConflict('context_source_not_captured')
        from polynexus_core.runtime.routing_policy import highest_classification
        classification=highest_classification(*[project.classification,task.classification,context.classification,*[a['classification'] for a in artifact_records]]).value
        context_record={k:v for k,v in asdict(context).items() if k!='created_at'}
        record={'secret_ref':secret_ref,'task_id':task_id,'context_package_id':context.id,'context_version':context.version,'requirements':{'hash':req[0],'size':req[1]},'validation':{'hash':val[0],'size':val[1]},'source':source,'classification':classification,'execution_mode':execution_mode,'context':context_record,'artifacts':artifact_records}
        raw=canonical(record);identity='sha256:'+hashlib.sha256(raw).hexdigest()
        inputs={'context_package_id':context.id,'requirements_ref':'sha256:'+req[0],'validation_ref':'sha256:'+val[0],'baseline_ref':'sha256:'+hashlib.sha256(canonical(source['baseline'])).hexdigest(),'input_ref':identity}
        self.session.execute(text('INSERT INTO prepared_inputs(id,task_id,record,inputs) VALUES(:id,:t,:r,:i) ON CONFLICT(id) DO NOTHING'),{'id':identity,'t':task_id,'r':raw.decode(),'i':_json(inputs)})
        return inputs

    def verify_inputs(self,task_id,inputs):
        from polynexus_core.storage.content import ContentStore
        from polynexus_core.workspace.managed import canonical
        import os
        from pathlib import Path
        row=self.session.execute(text('SELECT record,inputs FROM prepared_inputs WHERE id=:id AND task_id=:t'),{'id':inputs.get('input_ref'),'t':task_id}).mappings().one_or_none()
        if row is None or json.loads(row['inputs'])!=inputs:raise GenerationConflict('input_not_prepared')
        record=json.loads(row['record'])
        if 'sha256:'+hashlib.sha256(canonical(record)).hexdigest()!=inputs['input_ref']:raise GenerationConflict('input_identity_mismatch')
        store=ContentStore(Path(os.environ['POLYNEXUS_CONTENT_ROOT']))
        for key in ('requirements','validation'):store.read(record[key]['hash'],record[key]['size'])
        for snap in ('baseline','input'):
            for entry in record['source'][snap]['entries']:store.read(entry['blob'][7:],entry['size'])
        from dataclasses import asdict
        from polynexus_core.persistence.repository import SqlContextPackageRepository,SqlArtifactRepository
        context=SqlContextPackageRepository(self.session).get(inputs['context_package_id'])
        if context is None or canonical({k:v for k,v in asdict(context).items() if k!='created_at'})!=canonical(record['context']):raise GenerationConflict('context_identity_changed')
        for saved in record['artifacts']:
            artifact=SqlArtifactRepository(self.session).get(saved['id'])
            if artifact is None or canonical(asdict(artifact))!=canonical(saved):raise GenerationConflict('artifact_identity_changed')
            store.read_artifact(artifact)
        return record

    def validate_run(self, task_id, revision, context_package_id):
        if revision is None:raise GenerationConflict("exact_generation_required")
        ref=WorkGenerationRef(task_id,revision);generation=self.get(ref)
        if generation['aborted'] or generation['closed'] or generation['ownership_unknown']:raise GenerationConflict('generation_not_startable')
        inputs=json.loads(generation['inputs'])
        if inputs['context_package_id']!=context_package_id:raise GenerationConflict('run_generation_context_mismatch')
        self.verify_inputs(task_id,inputs)
        return ref

    def _fact(self,ref,kind,command_id=None,details=None):
        from polynexus_core.domain.models import new_id,utc_now
        row=self.get(ref)
        self.session.execute(text('INSERT INTO generation_events(event_id,task_id,revision,control_revision,kind,command_id,occurred_at,details) VALUES(:id,:t,:r,:c,:k,:cmd,:at,:d)'),{'id':new_id('generation-event'),'t':ref.task_id,'r':ref.generation_revision,'c':row['control_revision'],'k':kind,'cmd':command_id,'at':utc_now().isoformat(),'d':_json(details or {})})

    def get(self, ref: WorkGenerationRef):
        row = self.session.execute(text("SELECT * FROM work_generations WHERE task_id=:task AND revision=:rev"), {"task":ref.task_id,"rev":ref.generation_revision}).mappings().one_or_none()
        if row is None:
            raise GenerationConflict("generation_not_found")
        return dict(row)

    def _replay(self, principal, command_id, payload):
        if not principal or not command_id or len(command_id)>128:
            raise GenerationConflict("command_identity_invalid")
        digest = hashlib.sha256(_json(payload).encode()).hexdigest()
        row = self.session.execute(text("SELECT payload_digest,response FROM generation_commands WHERE principal=:p AND command_id=:c"), {"p":principal,"c":command_id}).mappings().one_or_none()
        if row is not None:
            if row['payload_digest'] != digest:
                raise GenerationConflict("command_payload_conflict")
            return digest,json.loads(row['response'])
        return digest,None

    def _receipt(self, principal, command_id, digest, result):
        self.session.execute(text("INSERT INTO generation_commands(principal,command_id,payload_digest,response) VALUES(:p,:c,:d,:r)"), {"p":principal,"c":command_id,"d":digest,"r":_json(result)})
        return result

    def begin(self, *, principal, command_id, task_id, expected_revision, inputs, predecessor=None):
        payload={"kind":"retry" if predecessor else "begin","task":task_id,"expected":expected_revision,"inputs":inputs,"predecessor":predecessor}
        digest,replay=self._replay(principal,command_id,payload)
        if replay is not None:
            return replay
        self.reserve_task_write(task_id)
        # Another request may have committed the same command while this one
        # waited for the project write reservation. Replay the durable receipt.
        digest,replay=self._replay(principal,command_id,payload)
        if replay is not None:return replay
        required={"context_package_id","requirements_ref","validation_ref","baseline_ref","input_ref"}
        if set(inputs)!=required or any(not isinstance(v,str) or not v.strip() for v in inputs.values()):
            raise GenerationConflict("generation_inputs_incomplete")
        self.verify_inputs(task_id,inputs)
        task=self.session.execute(text("SELECT project_id FROM tasks WHERE id=:id"),{"id":task_id}).scalar_one_or_none()
        context=self.session.execute(text("SELECT project_id FROM context_packages WHERE id=:id"),{"id":inputs['context_package_id']}).scalar_one_or_none()
        if task is None or context != task:
            raise GenerationConflict("generation_context_scope_mismatch")
        current=self.session.execute(text('SELECT revision FROM generation_counters WHERE task_id=:t'),{'t':task_id}).scalar_one_or_none() or 0
        if current!=expected_revision:raise GenerationConflict('task_revision_conflict')
        active=self.session.execute(text('SELECT 1 FROM work_generations WHERE task_id=:t AND (closed=0 OR ownership_unknown=1) LIMIT 1'),{'t':task_id}).scalar_one_or_none()
        if active:raise GenerationConflict('previous_generation_not_safely_released')
        if predecessor is not None:
            if predecessor!=expected_revision:raise GenerationConflict('predecessor_revision_mismatch')
            old=self.get(WorkGenerationRef(task_id,predecessor))
            if not old['closed'] or old['ownership_unknown']:
                raise GenerationConflict("predecessor_not_safely_released")
        # SQLite serializes this conditional write. No max(revision)+1 race.
        self.session.execute(text("INSERT INTO generation_counters(task_id,revision) VALUES(:t,0) ON CONFLICT(task_id) DO NOTHING"),{"t":task_id})
        updated=self.session.execute(text("UPDATE generation_counters SET revision=revision+1 WHERE task_id=:t AND revision=:expected RETURNING revision"),{"t":task_id,"expected":expected_revision}).scalar_one_or_none()
        if updated is None:
            raise GenerationConflict("task_revision_conflict")
        self.session.execute(text("INSERT INTO work_generations(task_id,revision,inputs,predecessor,control_revision,aborted,closed,ownership_unknown) VALUES(:t,:r,:i,:p,0,0,0,0)"),{"t":task_id,"r":updated,"i":_json(inputs),"p":predecessor})
        self._fact(WorkGenerationRef(task_id,updated),"WorkGenerationCreated",command_id,{"predecessor":predecessor})
        return self._receipt(principal,command_id,digest,{"task_id":task_id,"generation_revision":updated,"command_id":command_id,"control_revision":0})

    def claim(self, ref, *, run_id, lineage, expected_control):
        self.reserve_task_write(ref.task_id)
        row=self.get(ref)
        self.verify_inputs(ref.task_id,json.loads(row['inputs']))
        if row['aborted'] or row['closed'] or row['ownership_unknown']:
            raise GenerationConflict("generation_not_startable")
        run=self.session.execute(text("SELECT task_id,context_package_id,generation_revision FROM runs WHERE id=:id"),{"id":run_id}).mappings().one_or_none()
        if run is None or run['generation_revision']!=ref.generation_revision or run['task_id']!=ref.task_id or run['context_package_id']!=json.loads(row['inputs'])['context_package_id']:
            raise GenerationConflict("run_generation_mismatch")
        if not lineage or len(lineage)>128:
            raise GenerationConflict("writer_lineage_invalid")
        previous=self.session.execute(text("SELECT * FROM generation_writer_claims WHERE task_id=:t AND revision=:r"),{"t":ref.task_id,"r":ref.generation_revision}).mappings().one_or_none()
        if previous is not None:
            if previous['lineage']!=lineage or previous['run_id']!=run_id:
                raise GenerationConflict("generation_writer_lineage_conflict")
            # Replay is observation, never a new launch permission.
            return {"fence":previous['fence'],"new_claim":False}
        record=self.verify_inputs(ref.task_id,json.loads(row['inputs']))
        scope=record['source'].get('scope_id','task:'+ref.task_id)
        self.session.execute(text('INSERT INTO workspace_scopes(scope_id,fence,run_id,released) VALUES(:s,0,NULL,1) ON CONFLICT(scope_id) DO NOTHING'),{'s':scope})
        fence=self.session.execute(text('UPDATE workspace_scopes SET fence=fence+1,run_id=:run,released=0 WHERE scope_id=:s AND released=1 RETURNING fence'),{'s':scope,'run':run_id}).scalar_one_or_none()
        if fence is None:raise GenerationConflict('workspace_scope_owned')
        changed=self.session.execute(text("UPDATE work_generations SET control_revision=control_revision+1 WHERE task_id=:t AND revision=:r AND control_revision=:c AND aborted=0 AND closed=0 AND ownership_unknown=0"),{"t":ref.task_id,"r":ref.generation_revision,"c":expected_control}).rowcount
        if changed!=1:
            raise GenerationConflict("generation_control_conflict")
        self.session.execute(text("INSERT INTO generation_writer_claims(task_id,revision,lineage,run_id,fence,released) VALUES(:t,:r,:l,:run,:f,0)"),{"t":ref.task_id,"r":ref.generation_revision,"l":lineage,"run":run_id,"f":fence})
        self._fact(ref,"ExecutionClaimed",details={"run_id":run_id,"fence":fence,"lineage":lineage})
        return {"fence":fence,"new_claim":True}

    def claim_run(self,run):
        self.reserve_task_write(run.task_id)
        ref=self.validate_run(run.task_id,run.generation_revision,run.context_package_id)
        if run.generation_parent_run_id:
            parent=self.session.execute(text('SELECT task_id,generation_revision,state FROM runs WHERE id=:id'),{'id':run.generation_parent_run_id}).mappings().one_or_none()
            claim=self.session.execute(text('SELECT fence FROM generation_writer_claims WHERE task_id=:t AND revision=:r AND run_id=:p AND released=0'),{'t':run.task_id,'r':run.generation_revision,'p':run.generation_parent_run_id}).scalar_one_or_none()
            if parent is None or parent['task_id']!=run.task_id or parent['generation_revision']!=run.generation_revision or parent['state'] not in ('STARTING','RUNNING') or claim is None:raise GenerationConflict('council_generation_parent_mismatch')
            return {'fence':claim,'new_claim':True}
        return self.claim(ref,run_id=run.id,lineage='run:'+run.id,expected_control=self.get(ref)['control_revision'])

    def close(self, ref, *, run_id, fence, owned_processes):
        from polynexus_core.workspace.ownership import OwnedProcessRegistry
        if not isinstance(owned_processes, OwnedProcessRegistry) or not owned_processes.stopped(ref, run_id, fence):
            raise GenerationConflict("writer_stop_unverified")
        # A terminal state alone never establishes ownership release.
        state=self.session.execute(text("SELECT state FROM runs WHERE id=:run"),{"run":run_id}).scalar_one_or_none()
        if state not in {"COMPLETED","FAILED","TIMED_OUT","CANCELLED"}:
            raise GenerationConflict("writer_stop_unverified")
        changed=self.session.execute(text("UPDATE generation_writer_claims SET released=1 WHERE task_id=:t AND revision=:r AND run_id=:run AND fence=:f"),{"t":ref.task_id,"r":ref.generation_revision,"run":run_id,"f":fence}).rowcount
        if changed!=1:
            raise GenerationConflict("ownership_fence_conflict")
        self.session.execute(text("UPDATE work_generations SET closed=1,control_revision=control_revision+1 WHERE task_id=:t AND revision=:r AND ownership_unknown=0"),{"t":ref.task_id,"r":ref.generation_revision})
        self.session.execute(text('UPDATE workspace_scopes SET released=1 WHERE run_id=:run AND fence=:f'),{'run':run_id,'f':fence})
        self.session.execute(text('UPDATE generation_workspaces SET ownership=:o,recoverability=:re WHERE task_id=:t AND revision=:r'),{'o':_json({'state':'RELEASED','run_id':run_id,'fence':fence}),'re':_json({'capture_complete':True,'cleanup':'VERIFIED','state':'RECONSTRUCTABLE'}),'t':ref.task_id,'r':ref.generation_revision})
        self._fact(ref,'OwnershipReleased',details={'run_id':run_id,'fence':fence})
        row=self.get(ref)
        if row['aborted']:self._fact(ref,'WorkAborted',details={'run_id':run_id})

    def abort(self, ref, *, principal, command_id, expected_control):
        payload={"kind":"abort","task":ref.task_id,"revision":ref.generation_revision,"expected_control":expected_control}
        digest,replay=self._replay(principal,command_id,payload)
        if replay is not None:
            return replay
        self.get(ref)
        changed=self.session.execute(text("UPDATE work_generations SET aborted=1,control_revision=control_revision+1 WHERE task_id=:t AND revision=:r AND control_revision=:c"),{"t":ref.task_id,"r":ref.generation_revision,"c":expected_control}).rowcount
        if changed!=1:
            raise GenerationConflict("generation_control_conflict")
        # A generation never claimed has no launched writer to clean up.
        claimed=self.session.execute(text('SELECT 1 FROM generation_writer_claims WHERE task_id=:t AND revision=:r'),{'t':ref.task_id,'r':ref.generation_revision}).scalar_one_or_none()
        if claimed is None:self.session.execute(text('UPDATE work_generations SET closed=1 WHERE task_id=:t AND revision=:r'),{'t':ref.task_id,'r':ref.generation_revision})
        self._fact(ref,'WorkAbortRequested',command_id)
        row=self.get(ref)
        # Requested is distinct from stopped; a caller still must cancel exact
        # owned Run handles and establish cleanup before calling close.
        result={"task_id":ref.task_id,"generation_revision":ref.generation_revision,"command_id":command_id,"control_revision":row['control_revision'],"abort_requested":True,"work_aborted":bool(row['closed'] and not row['ownership_unknown'])}
        return self._receipt(principal,command_id,digest,result)


    def create_run(self, *, principal, command_id, task_id, revision, context_package_id, expected_control):
        from polynexus_core.domain.models import Run
        from polynexus_core.persistence.repository import SqlTaskRepository,SqlRunRepository
        payload={'kind':'create_run','task':task_id,'revision':revision,'context':context_package_id,'control':expected_control}
        digest,replay=self._replay(principal,command_id,payload)
        if replay is not None:return SqlRunRepository(self.session).get(replay['run_id'])
        self.reserve_task_write(task_id)
        ref=self.validate_run(task_id,revision,context_package_id)
        row=self.get(ref)
        if row['control_revision']!=expected_control:raise GenerationConflict('generation_control_conflict')
        task=SqlTaskRepository(self.session).get(task_id)
        run=Run(task_id=task_id,workflow_id=task.workflow_id,workflow_version=task.workflow_version,context_package_id=context_package_id,generation_revision=revision)
        SqlRunRepository(self.session).add(run)
        self._receipt(principal,command_id,digest,{'run_id':run.id})
        self._fact(ref,'RunCreated',command_id,{'run_id':run.id})
        return run

    def observe(self,ref):
        row=self.get(ref);row['inputs']=json.loads(row['inputs'])
        row['writer']=self.session.execute(text('SELECT lineage,run_id,fence,released FROM generation_writer_claims WHERE task_id=:t AND revision=:r'),{'t':ref.task_id,'r':ref.generation_revision}).mappings().one_or_none()
        row['writer']=dict(row['writer']) if row['writer'] else None
        workspace=self.session.execute(text('SELECT workspace_id,identity,git_observation,ownership,recoverability FROM generation_workspaces WHERE task_id=:t AND revision=:r'),{'t':ref.task_id,'r':ref.generation_revision}).mappings().one_or_none()
        row['workspace']={k:(v if k=='workspace_id' else json.loads(v)) for k,v in workspace.items()} if workspace else None
        row['work_aborted']=bool(row['aborted'] and row['closed'] and not row['ownership_unknown'])
        row['events']=[dict(e) for e in self.session.execute(text('SELECT event_id,control_revision,kind,command_id,occurred_at,details FROM generation_events WHERE task_id=:t AND revision=:r ORDER BY control_revision,occurred_at,event_id'),{'t':ref.task_id,'r':ref.generation_revision}).mappings()]
        return row


    def bound_claim(self,run):
        if run.generation_revision is None:raise GenerationConflict('exact_generation_required')
        parent=run.generation_parent_run_id or run.id
        claim=self.session.execute(text('SELECT * FROM generation_writer_claims WHERE task_id=:t AND revision=:r AND run_id=:p'),{'t':run.task_id,'r':run.generation_revision,'p':parent}).mappings().one_or_none()
        if claim is None:raise GenerationConflict('generation_claim_missing')
        return dict(claim)

    def prepare_workspace(self,run):
        import os
        from pathlib import Path
        from polynexus_core.storage.content import ContentStore
        from polynexus_core.workspace.managed import ManagedInputs
        from polynexus_core.domain.models import new_id,utc_now
        ref=WorkGenerationRef(run.task_id,run.generation_revision)
        record=self.verify_inputs(run.task_id,json.loads(self.get(ref)['inputs']))
        claim=self.bound_claim(run)
        existing=self.session.execute(text('SELECT workspace_id FROM generation_workspaces WHERE task_id=:t AND revision=:r'),{'t':run.task_id,'r':run.generation_revision}).scalar_one_or_none()
        if existing:return record,existing
        if run.generation_parent_run_id:raise GenerationConflict('parent_workspace_unavailable')
        identity={'repository':record['source']['repository'],'baseline':self.get(ref)['inputs'],'support_policy':'regular-files-no-filters-v1'}
        workspace_id=new_id('workspace')
        facts={'t':run.task_id,'r':run.generation_revision,'run':run.id,'f':claim['fence'],'w':workspace_id,'i':_json(identity),'g':_json({'state':'NOT_OBSERVED','observed_at':utc_now().isoformat()}),'o':_json({'state':'OWNED','run_id':run.id,'fence':claim['fence']}),'re':_json({'capture_complete':True,'cleanup':'UNCONFIRMED','state':'PREPARING'})}
        self.session.execute(text('INSERT INTO generation_workspaces(task_id,revision,run_id,fence,workspace_id,identity,git_observation,ownership,recoverability) VALUES(:t,:r,:run,:f,:w,:i,:g,:o,:re)'),facts)
        self.session.commit()
        try:
            if record['source']['repository']:
                manager=ManagedInputs(ContentStore(Path(os.environ['POLYNEXUS_CONTENT_ROOT'])),Path(os.environ['POLYNEXUS_SOURCE_ROOT']),Path(os.environ['POLYNEXUS_WORK_ROOT']))
                destination=manager.materialize(record['source'],workspace_id)
                status=manager.git(destination,'status','--porcelain=v1','-z','--untracked-files=all')
                git={'state':'HAS_CHANGES' if status else 'CLEAN','head':record['source']['baseline_commit'],'status_hex':status.hex(),'observed_at':utc_now().isoformat()}
            else:git={'state':'NO_REPOSITORY','observed_at':utc_now().isoformat()}
            self.session.execute(text('UPDATE generation_workspaces SET git_observation=:g,recoverability=:re WHERE task_id=:t AND revision=:r'),{'g':_json(git),'re':_json({'capture_complete':True,'cleanup':'UNCONFIRMED','state':'READY'}),'t':run.task_id,'r':run.generation_revision})
            self.session.commit()
        except Exception:
            self.mark_unknown(run,'workspace_setup_incomplete');self.session.commit();raise GenerationConflict('workspace_setup_incomplete') from None
        return record,workspace_id

    def mark_unknown(self,run,reason):
        ref=WorkGenerationRef(run.task_id,run.generation_revision)
        self.session.execute(text('UPDATE work_generations SET ownership_unknown=1 WHERE task_id=:t AND revision=:r'),{'t':run.task_id,'r':run.generation_revision})
        self.session.execute(text('UPDATE generation_workspaces SET ownership=:o,recoverability=:re WHERE task_id=:t AND revision=:r'),{'o':_json({'state':'UNKNOWN'}),'re':_json({'cleanup':'UNCONFIRMED','state':'RECOVERY_REQUIRED','reason':reason}),'t':run.task_id,'r':run.generation_revision})
        self._fact(ref,'RecoveryRequired',details={'run_id':run.id,'reason':reason})


    def start_command(self, run, *, principal, command_id, revision, expected_control, record=False):
        if revision != run.generation_revision or revision is None:
            raise GenerationConflict('exact_generation_required')
        payload={'kind':'start_run','run':run.id,'task':run.task_id,'revision':revision,'control':expected_control}
        digest,replay=self._replay(principal,command_id,payload)
        if replay is not None:return replay
        if not record:return None
        self.reserve_task_write(run.task_id)
        ref=self.validate_run(run.task_id,revision,run.context_package_id)
        if self.get(ref)['control_revision']!=expected_control:raise GenerationConflict('generation_control_conflict')
        # The caller's existing binding/claim transaction commits this receipt.
        # No separate commit and no restart permission on receipt replay.
        result={'run_id':run.id,'command_id':command_id,'generation_revision':revision,'accepted':True}
        self._fact(ref,'RunStartRequested',command_id,{'run_id':run.id})
        return self._receipt(principal,command_id,digest,result)

    def cancel_run(self, run, *, principal, command_id, revision, expected_control, expected_fence):
        from polynexus_core.domain.enums import RunState
        from polynexus_core.persistence.repository import SqlRunRepository
        if revision != run.generation_revision or revision is None:raise GenerationConflict('exact_generation_required')
        payload={'kind':'cancel_run','run':run.id,'task':run.task_id,'revision':revision,'control':expected_control,'fence':expected_fence}
        digest,replay=self._replay(principal,command_id,payload)
        if replay is not None:return replay,False
        ref=WorkGenerationRef(run.task_id,revision)
        row=self.get(ref)
        if row['control_revision']!=expected_control:raise GenerationConflict('generation_control_conflict')
        claim=self.session.execute(text('SELECT fence FROM generation_writer_claims WHERE task_id=:t AND revision=:r AND run_id=:run'),{'t':run.task_id,'r':revision,'run':run.generation_parent_run_id or run.id}).scalar_one_or_none()
        if expected_fence!=(claim or 0):raise GenerationConflict('ownership_fence_conflict')
        terminal=run.state in {RunState.COMPLETED,RunState.FAILED,RunState.TIMED_OUT,RunState.CANCELLED,RunState.ORPHANED}
        if not terminal:
            changed=self.session.execute(text('UPDATE work_generations SET control_revision=control_revision+1 WHERE task_id=:t AND revision=:r AND control_revision=:c'),{'t':run.task_id,'r':revision,'c':expected_control}).rowcount
            if changed!=1:raise GenerationConflict('generation_control_conflict')
            if run.state is RunState.CREATED:
                run.transition(RunState.CANCEL_REQUESTED,'Cancellation requested before execution')
                run.transition(RunState.CANCELLED,'No runtime was started')
                SqlRunRepository(self.session).update(run)
            self._fact(ref,'RunCancelRequested',command_id,{'run_id':run.id,'fence':expected_fence})
        result={'run_id':run.id,'command_id':command_id,'generation_revision':revision,'cancel_requested':not terminal,'control_revision':self.get(ref)['control_revision']}
        return self._receipt(principal,command_id,digest,result),True
