"""D1A-10: real synthetic SQLite upgrade, interrupted upgrade and restore."""
import hashlib
import sqlite3
import tempfile
from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import event
from sqlalchemy.engine import Engine
from polynexus_core.persistence.backup import create_sqlite_backup,restore_sqlite_backup


def config(path):
    assert path.is_absolute()
    c=Config();c.set_main_option('script_location',str(Path(__file__).parents[1]/'alembic'));c.set_main_option('sqlalchemy.url','sqlite:///'+path.as_posix())
    return c


def seed_legacy(path):
    command.upgrade(config(path),'0003')
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO projects(id,name,description,created_at) VALUES('p','legacy','kept','2026-01-01')")
        db.execute("INSERT INTO context_packages(id,project_id,version,instructions,constraints,project_facts,artifact_refs,prior_decision_refs,memory_refs,source_refs,created_at) VALUES('cp','p',1,'[]','[]','{}','[]','[]','[]','[]','2026-01-01')")
        db.execute("INSERT INTO tasks(id,project_id,title,workflow_id,workflow_version,mode,context_package_id,created_at) VALUES('t','p','legacy task','review',1,'REVIEW','cp','2026-01-01')")


def test_upgrade_backup_restore_preserves_legacy(tmp_path,monkeypatch):
    monkeypatch.setattr(tempfile,'tempdir',str(tmp_path))
    db=tmp_path/'legacy.db';backup=tmp_path/'backup.db';restored=tmp_path/'restored.db'
    seed_legacy(db)
    before=hashlib.sha256(db.read_bytes()).hexdigest()
    receipt=create_sqlite_backup(db,backup)
    assert receipt.integrity=='ok'
    command.upgrade(config(db),'head')
    assert ScriptDirectory.from_config(config(db)).get_heads()==['0009']
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT id,name,classification,archived FROM projects').fetchall()==[('p','legacy','INTERNAL',0)]
        assert conn.execute('SELECT id,context_package_id FROM tasks').fetchall()==[('t','cp')]
        assert conn.execute('SELECT count(*) FROM work_generations').fetchone()==(0,)
        assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
    with pytest.raises(RuntimeError,match='not lossless'):
        command.downgrade(config(db),'0003')
    restore_sqlite_backup(backup,restored)
    # SQLite's backup API may normalize file layout; verify restored bytes
    # against the actual backup receipt, plus exact old logical history.
    assert hashlib.sha256(restored.read_bytes()).hexdigest()==receipt.sha256
    with sqlite3.connect(restored) as conn:
        assert conn.execute('SELECT version_num FROM alembic_version').fetchone()==('0003',)
        assert conn.execute('SELECT id,name,description FROM projects').fetchall()==[('p','legacy','kept')]
    assert before==hashlib.sha256(backup.read_bytes()).hexdigest()


def test_interrupted_additive_upgrade_can_restore(tmp_path,monkeypatch):
    monkeypatch.setattr(tempfile,'tempdir',str(tmp_path))
    db=tmp_path/'interrupted.db';backup=tmp_path/'before.db';restored=tmp_path/'restored.db'
    seed_legacy(db);receipt=create_sqlite_backup(db,backup)
    seen=[]
    def interrupt(conn,cursor,statement,parameters,context,executemany):
        if statement.lstrip().startswith('CREATE TABLE work_generations'):
            seen.append(statement)
            raise RuntimeError('synthetic migration interruption')
    event.listen(Engine,'before_cursor_execute',interrupt)
    try:
        with pytest.raises(RuntimeError,match='synthetic migration interruption'):
            command.upgrade(config(db),'head')
    finally:
        event.remove(Engine,'before_cursor_execute',interrupt)
    assert seen
    restore_sqlite_backup(backup,restored)
    assert hashlib.sha256(restored.read_bytes()).hexdigest()==receipt.sha256
    with sqlite3.connect(restored) as conn:
        assert conn.execute('SELECT version_num FROM alembic_version').fetchone()==('0003',)
    command.upgrade(config(restored),'head')


def seed_representative(path):
    import json
    seed_legacy(path)
    content=b'representative immutable legacy artifact'
    blob=path.parent/'legacy-content.bin';blob.write_bytes(content)
    digest=hashlib.sha256(content).hexdigest()
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO runs(id,task_id,workflow_id,workflow_version,context_package_id,execution_target,resume_mode,state,created_at,updated_at,result_artifact_ids) VALUES('r','t','review',1,'cp','LOCAL','NONE','COMPLETED','2026-01-01','2026-01-01','[\"a\"]')")
        db.execute("INSERT INTO run_events(id,run_id,from_state,to_state,occurred_at,event_sequence,sequence_legacy_backfill) VALUES('e','r','CREATED','STARTING','2026-01-01',1,1)")
        db.execute("INSERT INTO artifacts(id,project_id,artifact_type,mime_type,source_type,storage_ref,sha256,size,task_id,run_id) VALUES('a','p','TEXT','text/plain','legacy','legacy-content.bin',?,?,'t','r')",(digest,len(content)))
        db.execute("UPDATE context_packages SET artifact_refs='[\"a\"]' WHERE id='cp'")
    return blob,digest


def logical_snapshot(path,columns=None):
    with sqlite3.connect(path) as db:
        if columns is None:
            tables=[r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name<>'alembic_version'")]
            columns={t:[row[1] for row in db.execute('PRAGMA table_info('+t+')')] for t in tables}
        return columns,{t:db.execute('SELECT '+','.join('"'+c+'"' for c in names)+' FROM '+t+' ORDER BY rowid').fetchall() for t,names in columns.items()}


def test_every_additive_mutation_interrupt_restores_all_legacy_facts(tmp_path,monkeypatch):
    import json
    monkeypatch.setattr(tempfile,'tempdir',str(tmp_path))
    original=tmp_path/'representative.db';blob,digest=seed_representative(original)
    columns,facts=logical_snapshot(original)
    backup=tmp_path/'representative-backup.db';receipt=create_sqlite_backup(original,backup)
    steps=[]
    def capture(conn,cursor,statement,parameters,context,executemany):
        if statement.lstrip().upper().startswith(('CREATE ','ALTER ','UPDATE ALEMBIC_VERSION')):steps.append(statement)
    event.listen(Engine,'before_cursor_execute',capture)
    try:command.upgrade(config(original),'head')
    finally:event.remove(Engine,'before_cursor_execute',capture)
    assert len(steps)>15
    assert logical_snapshot(original,columns)[1]==facts
    with sqlite3.connect(original) as db:
        assert db.execute('SELECT generation_revision,generation_parent_run_id FROM runs').fetchall()==[(None,None)]
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from polynexus_core.persistence.repository import SqlRunRepository
    from polynexus_core.api.runs import _run_to_response
    engine=create_engine('sqlite:///'+original.as_posix())
    with Session(engine) as session:assert _run_to_response(SqlRunRepository(session).get('r')).generation_binding_status=='LEGACY_UNBOUND_UNVERIFIED'
    engine.dispose()
    records=[]
    for step in range(len(steps)):
        damaged=tmp_path/('interrupted-'+str(step)+'.db');restored=tmp_path/('restored-'+str(step)+'.db')
        restore_sqlite_backup(backup,damaged);counter=[0]
        def interrupt(conn,cursor,statement,parameters,context,executemany):
            if statement.lstrip().upper().startswith(('CREATE ','ALTER ','UPDATE ALEMBIC_VERSION')):
                current=counter[0];counter[0]+=1
                if current==step:raise RuntimeError('stepwise interruption')
        event.listen(Engine,'before_cursor_execute',interrupt)
        try:
            with pytest.raises(RuntimeError,match='stepwise interruption'):command.upgrade(config(damaged),'head')
        finally:event.remove(Engine,'before_cursor_execute',interrupt)
        restore_sqlite_backup(backup,restored)
        assert hashlib.sha256(restored.read_bytes()).hexdigest()==receipt.sha256
        assert logical_snapshot(restored,columns)[1]==facts
        assert hashlib.sha256(blob.read_bytes()).hexdigest()==digest
        command.upgrade(config(restored),'head')
        assert logical_snapshot(restored,columns)[1]==facts
        records.append({'step':step,'statement':steps[step].splitlines()[0],'backup_sha256':receipt.sha256,'old_facts_equal':True,'content_sha256':digest,'restored_head':'0009'})
    print('D1A_MIGRATION_STEP_FACTS='+json.dumps(records))


@pytest.mark.parametrize('corruption',['task','context','artifact','duplicate_version','duplicate_content_ref'])
def test_dangling_and_duplicate_audit_before_schema_mutation(tmp_path,corruption):
    db=tmp_path/'invalid.db';seed_representative(db)
    with sqlite3.connect(db) as conn:
        if corruption=='task':conn.execute("UPDATE runs SET task_id='missing' WHERE id='r'")
        elif corruption=='context':conn.execute("UPDATE runs SET context_package_id='missing' WHERE id='r'")
        elif corruption=='artifact':conn.execute("UPDATE context_packages SET artifact_refs='[\"missing\"]'")
        elif corruption=='duplicate_version':conn.execute("INSERT INTO context_packages(id,project_id,version,created_at) VALUES('duplicate','p',1,'2026-01-01')")
        else:conn.execute("UPDATE context_packages SET artifact_refs='[\"a\",\"a\"]'")
    before=hashlib.sha256(db.read_bytes()).hexdigest()
    with pytest.raises(RuntimeError,match='audit failed'):command.upgrade(config(db),'head')
    assert hashlib.sha256(db.read_bytes()).hexdigest()==before
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT version_num FROM alembic_version').fetchone()==('0003',)
        assert 'classification' not in [r[1] for r in conn.execute('PRAGMA table_info(projects)')]
