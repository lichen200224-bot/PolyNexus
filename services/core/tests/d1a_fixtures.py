"""Explicit generation setup for existing consumer regression fixtures.

These helpers exercise real preparation/Begin; they never patch production
functions, bypass guards, change assertions, or launch runtime work.
"""
from pathlib import Path
from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
from polynexus_core.persistence.generation import GenerationRepository
from polynexus_core.persistence.repository import SqlTaskRepository

@pytest.fixture(autouse=True)
def d1a_content_environment(tmp_path,monkeypatch):
    monkeypatch.setenv('POLYNEXUS_CONTENT_ROOT',str(tmp_path/'d1a-content'))

def migrate_fixture_engine(engine):
    path=Path(engine.url.database)
    assert path.is_absolute() and path.suffix=='.db'
    config=Config();config.set_main_option('script_location',str(Path(__file__).parents[1]/'alembic'))
    config.set_main_option('sqlalchemy.url',str(engine.url));command.upgrade(config,'head')

def prepare_generation(session,task_id,context_id=None):
    session.flush()
    task=SqlTaskRepository(session).get(task_id)
    inputs=GenerationRepository(session).prepare(task_id=task_id,context_package_id=context_id or task.context_package_id,requirements='Retain the existing regression contract and original observable assertions.',validation='Run the original consumer oracle with a fixed synthetic input snapshot.')
    result=GenerationRepository(session).begin(principal='regression-fixture',command_id='fixture-begin-'+task_id,task_id=task_id,expected_revision=0,inputs=inputs)
    session.commit()
    return result['generation_revision']

def prepared_run_body(client,task_id,context_id):
    prepared=client.post(f'/api/v1/tasks/{task_id}/inputs',json={'context_package_id':context_id,'requirements':'Retain the existing API behavior under exact generation binding.','validation':'Exercise the original response, history, scope and execution assertions.'})
    assert prepared.status_code==201,prepared.text
    begin=client.post(f'/api/v1/tasks/{task_id}/generations',json={'command_id':'fixture-begin-'+task_id,'expected_revision':0,'inputs':prepared.json()})
    assert begin.status_code==201,begin.text
    return {'context_package_id':context_id,'generation_revision':begin.json()['generation_revision'],'expected_control_revision':0,'command_id':uuid4().hex}

def start_body():
    return {'generation_revision':1,'expected_control_revision':0,'command_id':uuid4().hex}
