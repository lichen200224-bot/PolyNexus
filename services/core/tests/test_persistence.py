from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from polynexus_core.domain.enums import (
    ArtifactType,
    EvidenceStatus,
    EvidenceType,
    ExecutionTarget,
    FindingSeverity,
    FindingStatus,
    ResumeMode,
    RunState,
    WorkMode,
)
from polynexus_core.domain.models import (
    Artifact,
    ContextPackage,
    Evidence,
    Finding,
    Project,
    Run,
    RunEvent,
    RunResult,
    Task,
)
from polynexus_core.persistence.database import (
    create_all,
    dispose_engine,
    get_engine,
    init_engine,
)
from polynexus_core.persistence.models import Base
from polynexus_core.persistence.repository import (
    SqlArtifactRepository,
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlFindingRepository,
    SqlProjectRepository,
    SqlRunEventRepository,
    SqlRunRepository,
    SqlTaskRepository,
    _ensure_utc_naive,
)


@pytest.fixture()
def db_session(tmp_path: Path):
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def fresh_db(tmp_path: Path):
    db_path = tmp_path / "fresh.db"
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    session = Session()
    yield session, db_path, url, engine
    session.close()
    engine.dispose()


def _make_project(name: str = "Test Project") -> Project:
    return Project(name=name, description="A test project")


def _make_task(project_id: str, title: str = "Test Task") -> Task:
    return Task(
        project_id=project_id,
        title=title,
        workflow_id="review-minimal",
        workflow_version=1,
        mode=WorkMode.REVIEW,
    )


def _make_context_package(project_id: str) -> ContextPackage:
    return ContextPackage(
        project_id=project_id,
        version=1,
        instructions=("Review the code for security issues.",),
        constraints=("Do not modify source files.",),
        project_facts={"language": "python", "framework": "fastapi"},
        artifact_refs=("art_abc123",),
    )


def _make_run(task: Task, cp: ContextPackage) -> Run:
    return Run(
        task_id=task.id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=cp.id,
    )


def _make_artifact(project_id: str) -> Artifact:
    return Artifact(
        project_id=project_id,
        artifact_type=ArtifactType.CODE_DIFF,
        mime_type="text/plain",
        source_type="filesystem",
        storage_ref="/tmp/diff.txt",
        sha256="abc123def456",
        size=1024,
    )


def _make_finding(task_id: str, run_id: str) -> Finding:
    return Finding(
        task_id=task_id,
        run_id=run_id,
        title="SQL Injection Risk",
        description="Found potential SQL injection in query builder.",
        severity=FindingSeverity.HIGH,
        status=FindingStatus.OPEN,
    )


def _make_evidence(task_id: str, run_id: str) -> Evidence:
    return Evidence(
        task_id=task_id,
        run_id=run_id,
        actor_id="reference-adapter",
        source="test runner",
        type=EvidenceType.RUNTIME_EVIDENCE,
        status=EvidenceStatus.PASS,
        metadata={"tool": "pytest", "version": "9.0"},
    )


class TestProjectRoundTrip:
    def test_add_and_get(self, db_session):
        repo = SqlProjectRepository(db_session)
        project = _make_project("My Project")
        repo.add(project)
        db_session.commit()

        loaded = repo.get(project.id)
        assert loaded is not None
        assert loaded.id == project.id
        assert loaded.name == "My Project"
        assert loaded.description == "A test project"

    def test_list_all(self, db_session):
        repo = SqlProjectRepository(db_session)
        repo.add(_make_project("P1"))
        repo.add(_make_project("P2"))
        db_session.commit()

        all_projects = repo.list_all()
        assert len(all_projects) == 2
        names = {p.name for p in all_projects}
        assert names == {"P1", "P2"}

    def test_delete(self, db_session):
        repo = SqlProjectRepository(db_session)
        project = _make_project()
        repo.add(project)
        db_session.commit()

        assert repo.delete(project.id) is True
        db_session.commit()
        assert repo.get(project.id) is None

    def test_delete_nonexistent(self, db_session):
        repo = SqlProjectRepository(db_session)
        assert repo.delete("nonexistent") is False


class TestTaskRoundTrip:
    def test_add_and_get(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        loaded = SqlTaskRepository(db_session).get(task.id)
        assert loaded is not None
        assert loaded.id == task.id
        assert loaded.project_id == project.id
        assert loaded.title == "Test Task"
        assert loaded.workflow_id == "review-minimal"
        assert loaded.workflow_version == 1
        assert loaded.mode == WorkMode.REVIEW

    def test_list_by_project(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        t1 = _make_task(project.id, "Task 1")
        t2 = _make_task(project.id, "Task 2")
        repo = SqlTaskRepository(db_session)
        repo.add(t1)
        repo.add(t2)
        db_session.commit()

        tasks = repo.list_by_project(project.id)
        assert len(tasks) == 2


class TestRunRoundTrip:
    def test_add_get_lifecycle(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        repo = SqlRunRepository(db_session)
        repo.add(run)
        db_session.commit()

        loaded = repo.get(run.id)
        assert loaded is not None
        assert loaded.state == RunState.CREATED
        assert loaded.execution_target == ExecutionTarget.LOCAL
        assert loaded.resume_mode == ResumeMode.NONE

    def test_lifecycle_transition_persisted(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        run.transition(RunState.RUNNING)

        repo = SqlRunRepository(db_session)
        repo.add(run)
        db_session.commit()

        loaded = repo.get(run.id)
        assert loaded is not None
        assert loaded.state == RunState.RUNNING
        assert len(loaded.events) == 2
        assert loaded.events[0].from_state == RunState.CREATED
        assert loaded.events[0].to_state == RunState.STARTING
        assert loaded.events[1].from_state == RunState.STARTING
        assert loaded.events[1].to_state == RunState.RUNNING

    def test_run_with_result_persisted(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        run.transition(RunState.RUNNING)
        run.result = RunResult(
            run_id=run.id,
            status=RunState.COMPLETED,
            summary="All checks passed.",
            finding_ids=("finding_1",),
            evidence_ids=("evidence_1",),
        )
        run.state = RunState.COMPLETED

        repo = SqlRunRepository(db_session)
        repo.add(run)
        db_session.commit()

        loaded = repo.get(run.id)
        assert loaded is not None
        assert loaded.state == RunState.COMPLETED
        assert loaded.result is not None
        assert loaded.result.summary == "All checks passed."
        assert loaded.result.finding_ids == ("finding_1",)
        assert loaded.result.evidence_ids == ("evidence_1",)

    def test_update_run(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        repo = SqlRunRepository(db_session)
        repo.add(run)
        db_session.commit()

        run.transition(RunState.STARTING)
        repo.update(run)
        db_session.commit()

        loaded = repo.get(run.id)
        assert loaded is not None
        assert loaded.state == RunState.STARTING

    def test_list_by_task(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        r1 = _make_run(task, cp)
        r2 = _make_run(task, cp)
        repo = SqlRunRepository(db_session)
        repo.add(r1)
        repo.add(r2)
        db_session.commit()

        runs = repo.list_by_task(task.id)
        assert len(runs) == 2


class TestArtifactRoundTrip:
    def test_add_and_get(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        artifact = _make_artifact(project.id)
        repo = SqlArtifactRepository(db_session)
        repo.add(artifact)
        db_session.commit()

        loaded = repo.get(artifact.id)
        assert loaded is not None
        assert loaded.id == artifact.id
        assert loaded.artifact_type == ArtifactType.CODE_DIFF
        assert loaded.sha256 == "abc123def456"
        assert loaded.size == 1024
        assert loaded.storage_ref == "/tmp/diff.txt"

    def test_list_by_project(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        a1 = _make_artifact(project.id)
        a2 = _make_artifact(project.id)
        repo = SqlArtifactRepository(db_session)
        repo.add(a1)
        repo.add(a2)
        db_session.commit()

        artifacts = repo.list_by_project(project.id)
        assert len(artifacts) == 2


class TestContextPackageRoundTrip:
    def test_add_and_get(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        cp = _make_context_package(project.id)
        repo = SqlContextPackageRepository(db_session)
        repo.add(cp)
        db_session.commit()

        loaded = repo.get(cp.id)
        assert loaded is not None
        assert loaded.id == cp.id
        assert loaded.version == 1
        assert loaded.instructions == ("Review the code for security issues.",)
        assert loaded.constraints == ("Do not modify source files.",)
        assert loaded.project_facts == {"language": "python", "framework": "fastapi"}
        assert loaded.artifact_refs == ("art_abc123",)

    def test_empty_tuples(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        cp = ContextPackage(
            project_id=project.id,
            version=1,
        )
        repo = SqlContextPackageRepository(db_session)
        repo.add(cp)
        db_session.commit()

        loaded = repo.get(cp.id)
        assert loaded is not None
        assert loaded.instructions == ()
        assert loaded.constraints == ()
        assert loaded.project_facts == {}
        assert loaded.artifact_refs == ()


class TestFindingRoundTrip:
    def test_add_and_get(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        finding = _make_finding(task.id, run.id)
        repo = SqlFindingRepository(db_session)
        repo.add(finding)
        db_session.commit()

        loaded = repo.get(finding.id)
        assert loaded is not None
        assert loaded.title == "SQL Injection Risk"
        assert loaded.severity == FindingSeverity.HIGH
        assert loaded.status == FindingStatus.OPEN

    def test_list_by_task(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        f1 = _make_finding(task.id, run.id)
        f2 = _make_finding(task.id, run.id)
        repo = SqlFindingRepository(db_session)
        repo.add(f1)
        repo.add(f2)
        db_session.commit()

        findings = repo.list_by_task(task.id)
        assert len(findings) == 2


class TestEvidenceRoundTrip:
    def test_add_and_get(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        evidence = _make_evidence(task.id, run.id)
        repo = SqlEvidenceRepository(db_session)
        repo.add(evidence)
        db_session.commit()

        loaded = repo.get(evidence.id)
        assert loaded is not None
        assert loaded.type == EvidenceType.RUNTIME_EVIDENCE
        assert loaded.status == EvidenceStatus.PASS
        assert loaded.metadata == {"tool": "pytest", "version": "9.0"}

    def test_list_by_task(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        e1 = _make_evidence(task.id, run.id)
        e2 = _make_evidence(task.id, run.id)
        repo = SqlEvidenceRepository(db_session)
        repo.add(e1)
        repo.add(e2)
        db_session.commit()

        evidence = repo.list_by_task(task.id)
        assert len(evidence) == 2


class TestMigrationFromEmpty:
    def test_create_all_and_verify_tables(self, tmp_path):
        db_path = tmp_path / "migration_test.db"
        url = f"sqlite:///{db_path}"
        engine = create_engine(url, connect_args={"check_same_thread": False}, future=True)

        Base.metadata.create_all(engine)

        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        expected = {
            "projects",
            "tasks",
            "context_packages",
            "runs",
            "run_events",
            "artifacts",
            "findings",
            "evidence",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"
        engine.dispose()

    def test_fresh_db_full_lifecycle(self, fresh_db):
        session, db_path, url, engine = fresh_db

        project = _make_project("Fresh Project")
        SqlProjectRepository(session).add(project)
        session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(session).add(task)
        session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        run.transition(RunState.RUNNING)
        SqlRunRepository(session).add(run)
        session.commit()

        artifact = _make_artifact(project.id)
        SqlArtifactRepository(session).add(artifact)
        session.commit()

        finding = _make_finding(task.id, run.id)
        SqlFindingRepository(session).add(finding)
        session.commit()

        evidence = _make_evidence(task.id, run.id)
        SqlEvidenceRepository(session).add(evidence)
        session.commit()

        assert SqlProjectRepository(session).get(project.id) is not None
        assert SqlTaskRepository(session).get(task.id) is not None
        assert SqlRunRepository(session).get(run.id) is not None
        assert SqlArtifactRepository(session).get(artifact.id) is not None
        assert SqlFindingRepository(session).get(finding.id) is not None
        assert SqlEvidenceRepository(session).get(evidence.id) is not None


class TestReopenDatabaseReloadHistory:
    def test_reopen_and_reload(self, tmp_path):
        db_path = tmp_path / "reopen_test.db"
        url = f"sqlite:///{db_path}"

        engine1 = create_engine(url, connect_args={"check_same_thread": False}, future=True)
        Base.metadata.create_all(engine1)
        Session1 = sessionmaker(bind=engine1, expire_on_commit=False, future=True)
        s1 = Session1()

        project = _make_project("Persist Project")
        SqlProjectRepository(s1).add(project)
        s1.commit()

        task = _make_task(project.id)
        SqlTaskRepository(s1).add(task)
        s1.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(s1).add(cp)
        s1.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        run.transition(RunState.RUNNING)
        run.result = RunResult(
            run_id=run.id,
            status=RunState.COMPLETED,
            summary="Done.",
        )
        run.state = RunState.COMPLETED
        SqlRunRepository(s1).add(run)
        s1.commit()

        s1.close()
        engine1.dispose()

        engine2 = create_engine(url, connect_args={"check_same_thread": False}, future=True)
        Session2 = sessionmaker(bind=engine2, expire_on_commit=False, future=True)
        s2 = Session2()

        loaded_project = SqlProjectRepository(s2).get(project.id)
        assert loaded_project is not None
        assert loaded_project.name == "Persist Project"

        loaded_task = SqlTaskRepository(s2).get(task.id)
        assert loaded_task is not None
        assert loaded_task.project_id == project.id

        loaded_cp = SqlContextPackageRepository(s2).get(cp.id)
        assert loaded_cp is not None
        assert loaded_cp.version == 1

        loaded_run = SqlRunRepository(s2).get(run.id)
        assert loaded_run is not None
        assert loaded_run.state == RunState.COMPLETED
        assert loaded_run.result is not None
        assert loaded_run.result.summary == "Done."
        assert len(loaded_run.events) == 2

        s2.close()
        engine2.dispose()


# ---------------------------------------------------------------------------
# FVS02-AC-002: RunEvent repository boundary + list-based history reload
# ---------------------------------------------------------------------------

class TestRunEventRepository:
    def test_add_and_list_by_run(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        run.transition(RunState.RUNNING)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        repo = SqlRunEventRepository(db_session)
        events = repo.list_by_run(run.id)
        assert len(events) == 2
        assert events[0].from_state == RunState.CREATED
        assert events[0].to_state == RunState.STARTING
        assert events[1].from_state == RunState.STARTING
        assert events[1].to_state == RunState.RUNNING

    def test_add_standalone_event(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        event = RunEvent(
            run_id=run.id,
            from_state=RunState.CREATED,
            to_state=RunState.STARTING,
            reason="manual trigger",
        )
        SqlRunEventRepository(db_session).add(event)
        db_session.commit()

        loaded = SqlRunEventRepository(db_session).list_by_run(run.id)
        assert len(loaded) == 1
        assert loaded[0].reason == "manual trigger"

    def test_list_by_run_empty(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        events = SqlRunEventRepository(db_session).list_by_run(run.id)
        assert len(events) == 0


class TestListBasedHistoryReload:
    def test_list_by_task_hydrates_events(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        run.transition(RunState.RUNNING)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        runs = SqlRunRepository(db_session).list_by_task(task.id)
        assert len(runs) == 1
        assert len(runs[0].events) == 2
        assert runs[0].events[0].to_state == RunState.STARTING
        assert runs[0].events[1].to_state == RunState.RUNNING

    def test_list_by_task_multiple_runs_with_events(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        r1 = _make_run(task, cp)
        r1.transition(RunState.STARTING)
        SqlRunRepository(db_session).add(r1)

        r2 = _make_run(task, cp)
        r2.transition(RunState.STARTING)
        r2.transition(RunState.RUNNING)
        SqlRunRepository(db_session).add(r2)
        db_session.commit()

        runs = SqlRunRepository(db_session).list_by_task(task.id)
        assert len(runs) == 2
        assert len(runs[0].events) == 1
        assert len(runs[1].events) == 2

    def test_list_by_task_reopen_reload_events(self, tmp_path):
        db_path = tmp_path / "reopen_events.db"
        url = f"sqlite:///{db_path}"

        engine1 = create_engine(url, connect_args={"check_same_thread": False}, future=True)
        Base.metadata.create_all(engine1)
        Session1 = sessionmaker(bind=engine1, expire_on_commit=False, future=True)
        s1 = Session1()

        project = _make_project()
        SqlProjectRepository(s1).add(project)
        s1.commit()

        task = _make_task(project.id)
        SqlTaskRepository(s1).add(task)
        s1.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(s1).add(cp)
        s1.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        run.transition(RunState.RUNNING)
        SqlRunRepository(s1).add(run)
        s1.commit()

        s1.close()
        engine1.dispose()

        engine2 = create_engine(url, connect_args={"check_same_thread": False}, future=True)
        Session2 = sessionmaker(bind=engine2, expire_on_commit=False, future=True)
        s2 = Session2()

        runs = SqlRunRepository(s2).list_by_task(task.id)
        assert len(runs) == 1
        assert len(runs[0].events) == 2
        assert runs[0].events[0].to_state == RunState.STARTING
        assert runs[0].events[1].to_state == RunState.RUNNING

        s2.close()
        engine2.dispose()


# ---------------------------------------------------------------------------
# FVS02-AC-003: Timestamp round-trip preservation
# ---------------------------------------------------------------------------

class TestTimestampRoundTrip:
    def test_ensure_utc_naive_strips_tz(self):
        aware = datetime(2026, 8, 18, 12, 0, 0, tzinfo=timezone.utc)
        naive = _ensure_utc_naive(aware)
        assert naive.tzinfo is None
        assert naive.year == 2026
        assert naive.month == 8
        assert naive.day == 18
        assert naive.hour == 12

    def test_ensure_utc_naive_preserves_naive(self):
        naive = datetime(2026, 8, 18, 12, 0, 0)
        result = _ensure_utc_naive(naive)
        assert result is naive

    def test_project_created_at_roundtrip(self, db_session):
        repo = SqlProjectRepository(db_session)
        project = _make_project("Timestamp Test")
        repo.add(project)
        db_session.commit()

        loaded = repo.get(project.id)
        assert loaded is not None
        assert loaded.created_at.tzinfo is None
        assert loaded.created_at.year == project.created_at.year
        assert loaded.created_at.month == project.created_at.month
        assert loaded.created_at.day == project.created_at.day
        assert loaded.created_at.hour == project.created_at.hour
        assert loaded.created_at.minute == project.created_at.minute

    def test_task_created_at_roundtrip(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        loaded = SqlTaskRepository(db_session).get(task.id)
        assert loaded is not None
        assert loaded.created_at.tzinfo is None
        assert loaded.created_at.year == task.created_at.year

    def test_run_timestamps_roundtrip(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        loaded = SqlRunRepository(db_session).get(run.id)
        assert loaded is not None
        assert loaded.created_at.tzinfo is None
        assert loaded.updated_at.tzinfo is None
        assert loaded.created_at.year == run.created_at.year

    def test_event_occurred_at_roundtrip(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        loaded = SqlRunRepository(db_session).get(run.id)
        assert loaded is not None
        for event in loaded.events:
            assert event.occurred_at.tzinfo is None

    def test_finding_created_at_roundtrip(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        finding = _make_finding(task.id, run.id)
        SqlFindingRepository(db_session).add(finding)
        db_session.commit()

        loaded = SqlFindingRepository(db_session).get(finding.id)
        assert loaded is not None
        assert loaded.created_at.tzinfo is None

    def test_evidence_observed_at_roundtrip(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(db_session).add(task)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        run = _make_run(task, cp)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        evidence = _make_evidence(task.id, run.id)
        SqlEvidenceRepository(db_session).add(evidence)
        db_session.commit()

        loaded = SqlEvidenceRepository(db_session).get(evidence.id)
        assert loaded is not None
        assert loaded.observed_at.tzinfo is None

    def test_context_package_created_at_roundtrip(self, db_session):
        project = _make_project()
        SqlProjectRepository(db_session).add(project)
        db_session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(db_session).add(cp)
        db_session.commit()

        loaded = SqlContextPackageRepository(db_session).get(cp.id)
        assert loaded is not None
        assert loaded.created_at.tzinfo is None


# ---------------------------------------------------------------------------
# FVS02-AC-004: Alembic lifecycle tests
# ---------------------------------------------------------------------------

class TestAlembicLifecycle:
    def test_upgrade_downgrade_reupgrade_reload(self, tmp_path):
        """Full Alembic lifecycle: upgrade head -> verify -> downgrade base -> verify -> upgrade head -> reload history."""
        from alembic.config import Config
        from alembic import command as alembic_cmd
        from sqlalchemy import inspect as sa_inspect

        db_path = tmp_path / "alembic_lifecycle.db"
        alembic_ini = tmp_path / "alembic.ini"
        alembic_dir = Path(__file__).parent.parent / "alembic"

        alembic_ini.write_text(
            "[alembic]\n"
            f"script_location = {alembic_dir}\n"
            "prepend_sys_path = .\n"
            f"sqlalchemy.url = sqlite:///{db_path}\n"
            "\n"
            "[loggers]\n"
            "keys = root,sqlalchemy,alembic\n"
            "\n"
            "[handlers]\n"
            "keys = console\n"
            "\n"
            "[formatters]\n"
            "keys = generic\n"
            "\n"
            "[logger_root]\n"
            "level = WARN\n"
            "handlers = console\n"
            "\n"
            "[logger_sqlalchemy]\n"
            "level = WARN\n"
            "handlers =\n"
            "qualname = sqlalchemy.engine\n"
            "\n"
            "[logger_alembic]\n"
            "level = INFO\n"
            "handlers =\n"
            "qualname = alembic\n"
            "\n"
            "[handler_console]\n"
            "class = StreamHandler\n"
            "args = (sys.stderr,)\n"
            "level = NOTSET\n"
            "formatter = generic\n"
            "\n"
            "[formatter_generic]\n"
            "format = %(levelname)-5.5s [%(name)s] %(message)s\n"
            "datefmt = %H:%M:%S\n"
        )

        config = Config(str(alembic_ini))

        # --- Phase 1: upgrade historical 0003 on empty db ---
        alembic_cmd.upgrade(config, "0003")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        inspector = sa_inspect(engine)
        tables = set(inspector.get_table_names())
        expected = {
            "projects", "tasks", "context_packages", "runs",
            "run_events", "artifacts", "findings", "evidence",
            "alembic_version",
        }
        assert expected.issubset(tables), f"Missing after upgrade: {expected - tables}"
        engine.dispose()

        # --- Phase 2: downgrade base ---
        alembic_cmd.downgrade(config, "base")

        engine2 = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        inspector2 = sa_inspect(engine2)
        tables_after_down = set(inspector2.get_table_names())
        assert tables_after_down <= {"alembic_version"}, f"Tables remain after downgrade: {tables_after_down}"
        engine2.dispose()

        # --- Phase 3: re-upgrade head ---
        alembic_cmd.upgrade(config, "head")

        engine3 = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        inspector3 = sa_inspect(engine3)
        tables_reup = set(inspector3.get_table_names())
        assert expected.issubset(tables_reup), f"Missing after re-upgrade: {expected - tables_reup}"
        engine3.dispose()

        # --- Phase 4: reopen and reload persisted history ---
        Session = sessionmaker(
            bind=create_engine(
                f"sqlite:///{db_path}",
                connect_args={"check_same_thread": False},
                future=True,
            ),
            expire_on_commit=False,
            future=True,
        )
        session = Session()

        project = _make_project("Alembic Lifecycle Test")
        SqlProjectRepository(session).add(project)
        session.commit()

        task = _make_task(project.id)
        SqlTaskRepository(session).add(task)
        session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        run = _make_run(task, cp)
        run.transition(RunState.STARTING)
        run.transition(RunState.RUNNING)
        SqlRunRepository(session).add(run)
        session.commit()

        # Verify reload
        loaded_project = SqlProjectRepository(session).get(project.id)
        assert loaded_project is not None
        assert loaded_project.name == "Alembic Lifecycle Test"

        loaded_run = SqlRunRepository(session).get(run.id)
        assert loaded_run is not None
        assert loaded_run.state == RunState.RUNNING
        assert len(loaded_run.events) == 2

        # Verify list-based reload
        runs = SqlRunRepository(session).list_by_task(task.id)
        assert len(runs) == 1
        assert len(runs[0].events) == 2

        session.close()
        engine_final = session.get_bind()
        engine_final.dispose()


class TestRunBindingSnapshotPersistence:
    """PRE-WP14-B: Run-owned immutable RuntimeBindingSnapshot persistence."""

    def _snapshot(self, run_id: str):
        from datetime import datetime, timezone

        from polynexus_core.domain.runtime_binding import legacy_backfill_snapshot

        return legacy_backfill_snapshot(
            run_id, ExecutionTarget.LOCAL, datetime(2026, 8, 25, tzinfo=timezone.utc)
        )

    def test_snapshot_round_trip_and_reload(self, db_session) -> None:
        from polynexus_core.persistence.repository import (
            SqlRuntimeBindingSnapshotRepository,
        )

        repo = SqlRuntimeBindingSnapshotRepository(db_session)
        snapshot = self._snapshot("run-rt-1")
        repo.insert_once(snapshot)
        db_session.commit()

        loaded = repo.get_by_run("run-rt-1")
        assert loaded == snapshot
        assert loaded.snapshot_schema_version == snapshot.snapshot_schema_version
        assert loaded.legacy_backfill is True

    def test_snapshot_duplicate_insert_rejected(self, db_session) -> None:
        from polynexus_core.domain.runtime_binding import RuntimeBindingError
        from polynexus_core.persistence.repository import (
            SqlRuntimeBindingSnapshotRepository,
        )

        repo = SqlRuntimeBindingSnapshotRepository(db_session)
        repo.insert_once(self._snapshot("run-dup-p"))
        with pytest.raises(RuntimeBindingError, match="already bound"):
            repo.insert_once(self._snapshot("run-dup-p"))

    def test_snapshot_repository_update_delete_rejected(self, db_session) -> None:
        from polynexus_core.domain.runtime_binding import RuntimeBindingError
        from polynexus_core.persistence.repository import (
            SqlRuntimeBindingSnapshotRepository,
        )

        repo = SqlRuntimeBindingSnapshotRepository(db_session)
        snapshot = self._snapshot("run-rej-p")
        repo.insert_once(snapshot)

        with pytest.raises(RuntimeBindingError, match="update is rejected"):
            repo.update(snapshot)
        with pytest.raises(RuntimeBindingError, match="delete is rejected"):
            repo.delete(snapshot.run_id)

    def test_snapshot_unknown_schema_version_fails_closed(self, db_session) -> None:
        from sqlalchemy import text as sa_text

        from polynexus_core.domain.runtime_binding import RuntimeBindingError
        from polynexus_core.persistence.repository import (
            SqlRuntimeBindingSnapshotRepository,
        )

        db_session.execute(
            sa_text(
                """
                INSERT INTO run_binding_snapshots (
                    run_id, provider_id, transport_kind, runtime_id, adapter_id,
                    execution_target, runtime_profile_ref, profile_revision,
                    adapter_version, resolved_at, legacy_backfill,
                    snapshot_schema_version, auth_ownership, secret_ref_id,
                    usage_visibility
                ) VALUES (
                    'run-badver-p', 'polynexus', 'LOCAL', 'reference',
                    'builtin.reference', 'LOCAL', NULL, NULL, NULL,
                    '2026-08-25 00:00:00.000000', 1, 99, 'NONE', NULL,
                    'UNAVAILABLE'
                )
                """
            )
        )
        db_session.commit()
        repo = SqlRuntimeBindingSnapshotRepository(db_session)
        with pytest.raises(RuntimeBindingError, match="snapshot_schema_version"):
            repo.get_by_run("run-badver-p")

    def test_run_update_does_not_mutate_persisted_snapshot(self, db_session) -> None:
        from polynexus_core.persistence.repository import (
            SqlRuntimeBindingSnapshotRepository,
        )

        project = _make_project("Snapshot Run Update")
        cp = _make_context_package(project.id)
        task = _make_task(project.id)
        task.context_package_id = cp.id
        run = _make_run(task, cp)
        SqlProjectRepository(db_session).add(project)
        SqlContextPackageRepository(db_session).add(cp)
        SqlTaskRepository(db_session).add(task)
        SqlRunRepository(db_session).add(run)
        db_session.commit()

        binding_repo = SqlRuntimeBindingSnapshotRepository(db_session)
        snapshot = self._snapshot(run.id)
        binding_repo.insert_once(snapshot)
        db_session.commit()

        # Legal lifecycle: CAS claim (CREATED→STARTING) then STARTING→RUNNING.
        assert SqlRunRepository(db_session).claim_for_execution(run.id) is True
        stored_run = SqlRunRepository(db_session).get(run.id)
        assert stored_run is not None
        stored_run.transition(RunState.RUNNING)
        SqlRunRepository(db_session).update(stored_run)
        db_session.commit()

        reloaded = binding_repo.get_by_run(run.id)
        assert reloaded == snapshot
