"""D1A-01 / PN-001: archive is durable and preserves related history."""
from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from polynexus_core.domain.models import Project, Task
from polynexus_core.persistence.repository import SqlProjectRepository, SqlTaskRepository


def test_archive_reopen_retains_task_and_classification(tmp_path):
    database = tmp_path / "project.db"
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    config.set_main_option("sqlalchemy.url", "sqlite:///" + database.as_posix())
    command.upgrade(config, "head")
    engine = create_engine("sqlite:///" + database.as_posix())
    with Session(engine) as session:
        project = Project(name="Synthetic", classification="CONFIDENTIAL")
        projects = SqlProjectRepository(session)
        projects.add(project)
        session.flush()
        task = Task(project_id=project.id, title="Preserve history", workflow_id="review", workflow_version=1)
        SqlTaskRepository(session).add(task)
        session.commit()
        assert projects.archive(project.id).archived
        assert projects.archive(project.id).archived
        assert projects.archive("foreign") is None
        session.commit()
    engine.dispose()
    engine = create_engine("sqlite:///" + database.as_posix())
    with Session(engine) as session:
        reopened = SqlProjectRepository(session).get(project.id)
        assert reopened.archived and reopened.classification == "CONFIDENTIAL"
        assert SqlTaskRepository(session).get(task.id).project_id == project.id
        assert session.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "0004"
    engine.dispose()


def test_unknown_classification_rejected():
    with pytest.raises(ValueError, match="classification"):
        Project(name="Synthetic", classification="UNKNOWN")


# D1A-02 / PN-010/011: real file-backed identity and retention.
def test_core_content_survives_source_edit_and_rejects_fake_locator(tmp_path):
    from dataclasses import replace
    from polynexus_core.storage.content import ContentStore, ContentError
    from polynexus_core.domain.models import Artifact
    from polynexus_core.domain.enums import ArtifactType
    source = tmp_path / "selected.txt"
    source.write_bytes(b"original content")
    store = ContentStore(tmp_path / "core-content")
    digest, size = store.put(source.read_bytes())
    artifact = Artifact(project_id="p", artifact_type=next(iter(ArtifactType)), mime_type="text/plain", source_type="test", storage_ref="core-blob:" + digest, sha256=digest, size=size)
    source.write_bytes(b"changed source")
    assert store.read_artifact(artifact) == b"original content"
    with pytest.raises(ContentError, match="locator"):
        store.read_artifact(replace(artifact, storage_ref=str(source)))
    with pytest.raises(ContentError, match="retention"):
        store.delete(digest)
    assert store.read_artifact(artifact) == b"original content"
    (store.root / digest).write_bytes(b"tampered")
    with pytest.raises(ContentError, match="identity"):
        store.read_artifact(artifact)


def test_content_missing_traversal_size_and_collision_fail_closed(tmp_path):
    from polynexus_core.storage.content import ContentStore, ContentError
    store = ContentStore(tmp_path / "content")
    for digest, size in [("../escape", 0), ("a" * 64, 0), ("a" * 64, -1)]:
        with pytest.raises(ContentError):
            store.read(digest, size)
    digest, size = store.put(b"correct")
    (store.root / digest).write_bytes(b"corrupt")
    with pytest.raises(ContentError, match="identity"):
        store.put(b"correct")


@pytest.fixture()
def content_api(tmp_path,monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker
    from polynexus_core.api.dependencies import require_loopback
    from polynexus_core.persistence.database import get_session
    from polynexus_core.api.artifacts import router as artifacts
    from polynexus_core.api.context_packages import router as contexts
    from polynexus_core.api.projects import router as projects
    database=tmp_path/'api.db';config=Config()
    config.set_main_option('script_location',str(Path(__file__).parents[1]/'alembic'))
    config.set_main_option('sqlalchemy.url','sqlite:///'+database.as_posix());command.upgrade(config,'head')
    engine=create_engine('sqlite:///'+database.as_posix(),connect_args={'check_same_thread':False})
    factory=sessionmaker(engine)
    def sessions():
        with factory() as s:yield s
    app=FastAPI();app.dependency_overrides[get_session]=sessions;app.dependency_overrides[require_loopback]=lambda:None
    for router in (artifacts,contexts,projects):app.include_router(router,prefix='/api/v1')
    monkeypatch.setenv('POLYNEXUS_CONTENT_ROOT',str(tmp_path/'content'))
    with TestClient(app) as client:yield client,factory,tmp_path/'content'
    engine.dispose()


def test_context_artifact_closure_versions_and_retention(content_api):
    import base64,hashlib
    from sqlalchemy.exc import IntegrityError
    client,factory,root=content_api
    p=client.post('/api/v1/projects',json={'name':'one'}).json()['id']
    foreign=client.post('/api/v1/projects',json={'name':'other'}).json()['id']
    payload=b'Immutable content, including Unicode: '+chr(0x6e2c).encode()
    response=client.post(f'/api/v1/projects/{p}/artifacts',json={'content_base64':base64.b64encode(payload).decode(),'classification':'RESTRICTED'})
    assert response.status_code==201,response.text
    artifact=response.json();assert artifact['sha256']==hashlib.sha256(payload).hexdigest() and artifact['classification']=='RESTRICTED'
    downloaded=client.get(f"/api/v1/artifacts/{artifact['id']}/content")
    assert downloaded.content==payload and downloaded.headers['content-disposition']=='attachment'
    body={'version':1,'artifact_refs':[artifact['id']],'classification':'CONFIDENTIAL'}
    assert client.post(f'/api/v1/projects/{foreign}/context-packages',json=body).status_code==422
    assert client.post(f'/api/v1/projects/{p}/context-packages',json={'version':1,'artifact_refs':['missing']}).status_code==422
    cp=client.post(f'/api/v1/projects/{p}/context-packages',json=body)
    assert cp.status_code==201,cp.text
    assert client.post(f'/api/v1/projects/{p}/context-packages',json=body).status_code==409
    body['version']=2;cp2=client.post(f'/api/v1/projects/{p}/context-packages',json=body)
    assert cp2.status_code==201 and cp2.json()['id']!=cp.json()['id']
    assert len(client.get(f'/api/v1/projects/{p}/context-packages').json()['context_packages'])==2
    with factory() as s:
        with pytest.raises(IntegrityError,match='immutable'):
            s.execute(text('UPDATE context_packages SET version=99 WHERE id=:id'),{'id':cp.json()['id']})
        s.rollback()
        with pytest.raises(IntegrityError,match='retained'):
            s.execute(text('DELETE FROM artifacts WHERE id=:id'),{'id':artifact['id']})
        s.rollback()
    assert client.delete(f"/api/v1/artifacts/{artifact['id']}").status_code==409
    assert client.post(f'/api/v1/projects/{p}/archive').status_code==200
    assert client.get(f"/api/v1/artifacts/{artifact['id']}/content").content==payload
    (root/artifact['sha256']).write_bytes(b'tampered')
    assert client.get(f"/api/v1/artifacts/{artifact['id']}/content").status_code==409
