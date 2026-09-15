"""ADR-014 migration and persistence-only ordering contract."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from threading import Barrier

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from polynexus_core.domain.enums import RunState
from polynexus_core.domain.models import RunEvent
from polynexus_core.persistence.repository import SqlRunRepository, SqlRunEventRepository

CORE = Path(__file__).resolve().parents[1]
FACTS = "id,run_id,from_state,to_state,occurred_at,reason"


def config(path):
    cfg = Config(str(CORE / "alembic.ini"))
    cfg.set_main_option("script_location", str(CORE / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    return cfg


def seed(engine):
    with engine.begin() as c:
        c.exec_driver_sql("INSERT INTO projects VALUES ('p','project',NULL,'2026-09-12')")
        c.exec_driver_sql("INSERT INTO tasks VALUES ('t','p','task','review-minimal',1,'REVIEW','cp','2026-09-12')")
        for rid in ["empty", "single", "multi"]:
            c.execute(text("""INSERT INTO runs
                (id,task_id,workflow_id,workflow_version,context_package_id,
                 execution_target,resume_mode,state,created_at,updated_at,
                 result_finding_ids,result_evidence_ids,result_artifact_ids)
                VALUES (:id,'t','review-minimal',1,'cp','LOCAL','NONE','RUNNING',
                 '2026-09-12','2026-09-12','[]','[]','[]')"""), {"id":rid})
        for eid, rid, before, after, reason in [
            ("z", "multi", "CREATED", "STARTING", "unicode: 測試\nline"),
            ("only", "single", "CREATED", "STARTING", None),
            ("m", "multi", "STARTING", "RUNNING", ""),
            ("a", "multi", "RUNNING", "RUNNING", "stage"),
        ]:
            c.execute(text(f"INSERT INTO run_events ({FACTS}) VALUES (:id,:run,:before,:after,:time,:reason)"),
                      dict(id=eid,run=rid,before=before,after=after,time="2026-09-12 00:00:00.123456",reason=reason))

        c.exec_driver_sql("""INSERT INTO run_binding_snapshots
            (run_id,provider_id,transport_kind,runtime_id,adapter_id,execution_target,
             resolved_at,legacy_backfill,snapshot_schema_version,auth_ownership,usage_visibility)
            VALUES ('multi','polynexus','LOCAL','reference','builtin.reference','LOCAL',
                    '2026-09-12',1,1,'NONE','UNAVAILABLE')""")
        c.exec_driver_sql("INSERT INTO context_packages(id,project_id,version,created_at) VALUES('cp','p',1,'2026-01-01')")


def facts(engine):
    with engine.connect() as c:
        return c.exec_driver_sql(f"SELECT rowid,{FACTS} FROM run_events ORDER BY rowid").all()


@pytest.fixture
def migrated(tmp_path):
    path = tmp_path / "migration.db"
    cfg = config(path)
    command.upgrade(cfg, "0002")
    engine = create_engine(f"sqlite:///{path}")
    seed(engine)
    command.upgrade(cfg, "0003")
    yield engine, cfg
    engine.dispose()


def test_upgrade_downgrade_reupgrade_preserves_legacy_facts(tmp_path):
    path = tmp_path / "roundtrip.db"
    cfg = config(path)
    command.upgrade(cfg, "0002")
    engine = create_engine(f"sqlite:///{path}")
    try:
        seed(engine)
        before = facts(engine)
        with engine.connect() as c:
            bindings = c.exec_driver_sql("SELECT * FROM run_binding_snapshots").all()
            runs = c.exec_driver_sql("SELECT * FROM runs ORDER BY id").all()
        for _ in range(2):
            command.upgrade(cfg, "0003")
            assert facts(engine) == before
            with engine.connect() as c:
                assert c.exec_driver_sql("SELECT id,event_sequence,sequence_legacy_backfill FROM run_events ORDER BY run_id,event_sequence").all() == [
                    ("z",1,1),("m",2,1),("a",3,1),("only",1,1)]
                assert c.exec_driver_sql("SELECT id,next_event_sequence FROM runs ORDER BY id").all() == [("empty",0),("multi",3),("single",1)]
                assert c.exec_driver_sql("SELECT * FROM run_binding_snapshots").all() == bindings
            command.downgrade(cfg, "0002")
            assert facts(engine) == before
            assert "event_sequence" not in {x['name'] for x in inspect(engine).get_columns('run_events')}
            with engine.connect() as c:
                assert c.exec_driver_sql("SELECT * FROM runs ORDER BY id").all() == runs
                assert c.exec_driver_sql("SELECT * FROM run_binding_snapshots").all() == bindings
    finally:
        engine.dispose()


@pytest.mark.parametrize("revision, expected", [("0003", "0003"), ("head", "0010")])
def test_fresh_head_and_no_event_counter(tmp_path, revision, expected):
    cfg = config(tmp_path / "fresh.db")
    command.upgrade(cfg,revision)
    engine=create_engine(f"sqlite:///{tmp_path / 'fresh.db'}")
    try:
        with engine.connect() as c:
            assert c.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one() == expected
            assert c.exec_driver_sql("SELECT COUNT(*) FROM run_events").scalar_one() == 0
        indexes=inspect(engine).get_unique_constraints('run_events')
        assert any(x['column_names']==['run_id','event_sequence'] for x in indexes)
    finally:
        engine.dispose()


def event(identity, run_id="multi"):
    return RunEvent(id=identity,run_id=run_id,from_state=RunState.RUNNING,
                    to_state=RunState.RUNNING,occurred_at=datetime(2000,1,1))


def test_update_preserves_counter_and_new_append_continues(migrated):
    engine,cfg=migrated
    command.upgrade(cfg,'head')
    with engine.connect() as connection:
        assert connection.exec_driver_sql('SELECT version_num FROM alembic_version').scalar_one()=='0010'
    with Session(engine) as s:
        repo=SqlRunRepository(s)
        repo.append_event(event("next"))
        run=repo.get("multi")
        repo.update(run)
        repo.update(run)
        s.commit()
        assert s.execute(text("SELECT next_event_sequence FROM runs WHERE id='multi'")).scalar_one()==4
        SqlRunEventRepository(s).add(event("last"))
        s.commit()
        assert s.execute(text("SELECT event_sequence,sequence_legacy_backfill FROM run_events WHERE id='last'")).one()==(5,0)
        assert [e.id for e in repo.get('multi').events]==['z','m','a','next','last']
        assert [e.id for e in repo.list_non_terminal() if e.id=='multi']==['multi']
        assert [e.id for e in next(r for r in repo.list_non_terminal() if r.id=='multi').events]==['z','m','a','next','last']


def test_concurrent_sessions_allocate_distinct_sequences(migrated):
    engine,_=migrated
    barrier=Barrier(4)
    def append(n):
        with Session(engine) as s:
            barrier.wait(timeout=10)
            SqlRunRepository(s).append_event(event(f"concurrent-{n}"))
            sequence=s.execute(text("SELECT event_sequence FROM run_events WHERE id=:id"),{'id':f'concurrent-{n}'}).scalar_one()
            s.commit()
            return sequence
    with ThreadPoolExecutor(max_workers=4) as pool:
        allocated=list(pool.map(append,range(4)))
    assert sorted(allocated)==[4,5,6,7]
    with engine.connect() as c:
        assert c.exec_driver_sql("SELECT next_event_sequence FROM runs WHERE id='multi'").scalar_one()==7


def test_missing_duplicate_and_immutable_sequence_fail_closed(migrated):
    engine,_=migrated
    with Session(engine) as s:
        with pytest.raises(ValueError,match='not found'):
            SqlRunRepository(s).append_event(event('missing','absent'))
        s.rollback()
        with pytest.raises(IntegrityError):
            SqlRunRepository(s).append_event(event('z'))
        s.rollback()
        assert s.execute(text("SELECT next_event_sequence FROM runs WHERE id='multi'")).scalar_one()==3
    for statement in [
        "UPDATE run_events SET event_sequence=20 WHERE id='z'",
        "UPDATE run_events SET sequence_legacy_backfill=0 WHERE id='z'",
        "UPDATE run_events SET run_id='single' WHERE id='z'",
        "INSERT INTO run_events(id,run_id,from_state,to_state,occurred_at,event_sequence) VALUES ('duplicate','multi','RUNNING','RUNNING','2000-01-01',1)",
    ]:
        with engine.connect() as c:
            with pytest.raises(IntegrityError): c.exec_driver_sql(statement)
            c.rollback()


def test_inconsistent_legacy_rollback_preserves_0002(tmp_path):
    path=tmp_path/'invalid.db'
    cfg=config(path)
    command.upgrade(cfg,'0002')
    engine=create_engine(f'sqlite:///{path}')
    try:
        seed(engine)
        with engine.begin() as c:
            c.exec_driver_sql("INSERT INTO run_events VALUES ('orphan','missing','RUNNING','RUNNING','2000-01-01',NULL)")
        before=facts(engine)
        with pytest.raises(RuntimeError,match='inconsistent'): command.upgrade(cfg,'0003')
        assert facts(engine)==before
        assert 'next_event_sequence' not in {x['name'] for x in inspect(engine).get_columns('runs')}
        assert 'run_events_0003_copy' not in inspect(engine).get_table_names()
        with engine.connect() as c:
            assert c.exec_driver_sql('SELECT version_num FROM alembic_version').scalar_one()=='0002'
    finally:
        engine.dispose()


def test_downgrade_preserves_new_events_and_reupgrade_marks_legacy(migrated):
    engine,cfg=migrated
    with Session(engine) as s:
        SqlRunRepository(s).append_event(event('post-0003'))
        s.commit()
    before=facts(engine)
    command.downgrade(cfg,'0002')
    assert facts(engine)==before
    command.upgrade(cfg,'0003')
    assert facts(engine)==before
    with engine.connect() as c:
        assert c.exec_driver_sql("SELECT event_sequence,sequence_legacy_backfill FROM run_events WHERE id='post-0003'").one()==(4,1)
        assert c.exec_driver_sql("SELECT next_event_sequence FROM runs WHERE id='multi'").scalar_one()==4
