"""Authenticated exact-target generation commands and durable observations."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Literal
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy import text
from polynexus_core.api.dependencies import AuthLoopback,DbSession
from polynexus_core.api.artifacts import content_store
from polynexus_core.domain.generation import WorkGenerationRef,GenerationConflict
from polynexus_core.persistence.generation import GenerationRepository
from polynexus_core.storage.content import ContentError
from polynexus_core.workspace.managed import ManagedInputs

router=APIRouter(tags=['generations'])
class StrictBody(BaseModel):model_config={'extra':'forbid'}
class PrepareInput(StrictBody):
    secret_ref:str|None=Field(default=None,pattern=r"^secretref:[0-9a-f]{32}$")
    context_package_id:str=Field(min_length=1)
    requirements:str=Field(min_length=1,max_length=1048576)
    validation:str=Field(min_length=1,max_length=1048576)
    execution_mode:Literal["STANDARD","LOCAL_PREFERRED","LOCAL_ONLY"]="STANDARD"
    repository:str|None=None
    baseline:str|None=None
    selected:list[str]=Field(default_factory=list,max_length=10000)
class BeginWork(StrictBody):
    command_id:str=Field(min_length=1,max_length=128)
    expected_revision:int=Field(ge=0)
    inputs:dict[str,str]
    predecessor:int|None=Field(default=None,ge=1)
class AbortWork(StrictBody):
    command_id:str=Field(min_length=1,max_length=128)
    expected_control:int=Field(ge=0)
class InspectRepository(StrictBody):repository:str=Field(min_length=1,max_length=1024)

def guarded(db,call):
    try:
        value=call();db.commit();return value
    except (GenerationConflict,ContentError) as error:
        db.rollback();raise HTTPException(409,str(error)) from None
    except KeyError:
        db.rollback();raise HTTPException(409,'workspace_not_configured') from None

@router.post('/tasks/{task_id}/inputs',status_code=201)
def prepare_input(task_id:str,body:PrepareInput,_auth:AuthLoopback,db:DbSession):
    return guarded(db,lambda:GenerationRepository(db).prepare(task_id=task_id,**body.model_dump()))

@router.post('/repositories/inspect')
def inspect_repository(body:InspectRepository,_auth:AuthLoopback,db:DbSession):
    return guarded(db,lambda:ManagedInputs(content_store(),Path(os.environ['POLYNEXUS_SOURCE_ROOT']),Path(os.environ['POLYNEXUS_WORK_ROOT'])).inspect(body.repository))

@router.post('/tasks/{task_id}/generations',status_code=201)
def begin_work(task_id:str,body:BeginWork,_auth:AuthLoopback,db:DbSession):
    return guarded(db,lambda:GenerationRepository(db).begin(principal='loopback-controller',task_id=task_id,**body.model_dump()))

@router.get('/tasks/{task_id}/generations')
def list_generations(task_id:str,_auth:AuthLoopback,db:DbSession,cursor:str|None=None):
    revision=db.execute(text('SELECT revision FROM generation_counters WHERE task_id=:t'),{'t':task_id}).scalar_one_or_none() or 0
    refs=db.execute(text('SELECT revision FROM work_generations WHERE task_id=:t ORDER BY revision'),{'t':task_id}).scalars()
    from polynexus_core.api.schemas import encode_cursor,decode_cursor
    scope='task-generations:'+task_id
    event_ids=list(db.execute(text('SELECT event_id FROM generation_events WHERE task_id=:t ORDER BY rowid'),{'t':task_id}).scalars())
    current=encode_cursor([scope,event_ids[-1] if event_ids else ''])
    if cursor is not None:
        _,anchor=decode_cursor(cursor,scope,2)
        if anchor and anchor not in event_ids: raise HTTPException(422,'invalid_cursor')
    return {'task_revision':revision,'cursor':current,'unchanged':cursor==current,'generations':[GenerationRepository(db).observe(WorkGenerationRef(task_id,r)) for r in refs]}

@router.get('/tasks/{task_id}/generations/{revision}')
def get_generation(task_id:str,revision:int,_auth:AuthLoopback,db:DbSession):
    return guarded(db,lambda:GenerationRepository(db).observe(WorkGenerationRef(task_id,revision)))

@router.post('/tasks/{task_id}/generations/{revision}/abort')
async def abort_work(task_id:str,revision:int,body:AbortWork,_auth:AuthLoopback,db:DbSession):
    ref=WorkGenerationRef(task_id,revision)
    result=guarded(db,lambda:GenerationRepository(db).abort(ref,principal='loopback-controller',command_id=body.command_id,expected_control=body.expected_control))
    # Exact owned operation dispatch is integrated with ExecutionService.
    from polynexus_core.workspace.ownership import active_operations
    active_operations.request_cancel_generation(ref)
    return result
