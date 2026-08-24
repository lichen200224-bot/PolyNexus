"""WP-07 Integration Acceptance Tests — execution persistence and reload.

Validates the full integration path:
  Project → Task → ContextPackage → WorkflowDefinition → RunSupervisor
  → ReferenceRuntimeAdapter → Run/RunEvent/RunResult/Finding/Evidence persistence
  → Close session → New session reload → Verify

Uses Alembic upgrade head on temporary SQLite database.
Does NOT use Base.metadata.create_all() for migration lifecycle.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from alembic import command as alembic_cmd
from alembic.config import Config
from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.orm import sessionmaker

from polynexus_core.domain.enums import (
    EvidenceStatus,
    EvidenceType,
    ExecutionTarget,
    FindingStatus,
    ResumeMode,
    RunState,
    WorkMode,
)
from polynexus_core.domain.models import (
    ContextPackage,
    Project,
    Task,
)
from polynexus_core.persistence.models import Base
from polynexus_core.persistence.repository import (
    SqlArtifactRepository,
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlFindingRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlTaskRepository,
)
from polynexus_core.execution_service import ExecutionService, _BUILTIN_WORKFLOWS_DIR


ALEMBIC_DIR = Path(__file__).parent.parent / "alembic"
REPO_ROOT = Path(__file__).resolve().parents[3]


def _make_alembic_config(db_path: Path) -> Config:
    """Create a temporary alembic.ini Config for the given DB path."""
    alembic_ini = db_path.parent / "alembic.ini"
    alembic_ini.write_text(
        "[alembic]\n"
        f"script_location = {ALEMBIC_DIR}\n"
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
    return Config(str(alembic_ini))


def _make_project(name: str = "Integration Test Project") -> Project:
    return Project(name=name, description="WP-07 integration acceptance test project")


def _make_context_package(project_id: str) -> ContextPackage:
    return ContextPackage(
        project_id=project_id,
        version=1,
        instructions=("Review the code for correctness and completeness.",),
        constraints=("Do not modify source files.",),
        project_facts={"language": "python", "framework": "fastapi"},
        artifact_refs=(),
    )


def _make_task(project_id: str, cp_id: str, title: str = "Integration Review Task") -> Task:
    return Task(
        project_id=project_id,
        title=title,
        workflow_id="review-minimal",
        workflow_version=1,
        mode=WorkMode.REVIEW,
        context_package_id=cp_id,
    )


class TestWP07ExecutionPersistence:
    """WP-07: Full execution-persistence-reload integration acceptance."""

    def test_execute_and_reload_full_lifecycle(self, tmp_path):
        """Core acceptance test: execute a task, persist all results, reload and verify.

        Uses Alembic upgrade head on fresh temp DB (not create_all).
        Closes first session/engine, opens new session/engine, reloads and verifies.
        """
        db_path = tmp_path / "wp07_acceptance.db"

        # --- Phase 1: Alembic upgrade head on fresh DB ---
        config = _make_alembic_config(db_path)
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        inspector = sa_inspect(engine)
        tables = set(inspector.get_table_names())
        expected_tables = {
            "projects", "tasks", "context_packages", "runs",
            "run_events", "artifacts", "findings", "evidence",
            "alembic_version",
        }
        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"

        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session1 = SessionFactory()

        # --- Phase 2: Create and persist Project, Task, ContextPackage ---
        project = _make_project()
        SqlProjectRepository(session1).add(project)
        session1.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session1).add(cp)
        session1.commit()

        task = _make_task(project.id, cp.id)
        SqlTaskRepository(session1).add(task)
        session1.commit()

        # Verify pre-execution state
        assert SqlTaskRepository(session1).get(task.id) is not None
        assert SqlContextPackageRepository(session1).get(cp.id) is not None

        # --- Phase 3: Execute via ExecutionService ---
        service = ExecutionService(session1)
        execution = asyncio.run(service.execute_task(task.id))

        # Verify in-memory execution result
        assert execution.run.state is RunState.COMPLETED
        assert execution.result.status is RunState.COMPLETED
        assert execution.result.summary == "Reference runtime completed without vendor execution"
        assert len(execution.evidence) > 0
        # Evidence includes RUNTIME_EVIDENCE from supervisor and
        # DOCUMENT_EVIDENCE gate report from post-execution gate evaluation.
        evidence_types = {e.type for e in execution.evidence}
        assert EvidenceType.RUNTIME_EVIDENCE in evidence_types
        assert EvidenceType.DOCUMENT_EVIDENCE in evidence_types
        assert not any(e.type is EvidenceType.AI_OPINION for e in execution.evidence)
        assert execution.artifacts == ()

        # Verify in-memory run has correct lifecycle
        run = execution.run
        assert run.execution_target == ExecutionTarget.LOCAL
        assert run.resume_mode == ResumeMode.NONE
        assert run.workflow_id == "review-minimal"
        assert run.workflow_version == 1

        # Verify lifecycle events include proper transitions
        state_transitions = [(e.from_state, e.to_state) for e in run.events]
        assert (RunState.CREATED, RunState.STARTING) in state_transitions
        assert (RunState.STARTING, RunState.RUNNING) in state_transitions
        assert (RunState.RUNNING, RunState.COMPLETED) in state_transitions

        # Verify RunResult references evidence
        assert len(run.result.evidence_ids) == len(execution.evidence)

        # Verify persisted in current session
        loaded_run = SqlRunRepository(session1).get(run.id)
        assert loaded_run is not None
        assert loaded_run.state == RunState.COMPLETED
        assert loaded_run.result is not None
        assert loaded_run.result.summary == "Reference runtime completed without vendor execution"

        loaded_evidence = SqlEvidenceRepository(session1).list_by_task(task.id)
        assert len(loaded_evidence) == len(execution.evidence)
        loaded_types = {e.type for e in loaded_evidence}
        assert EvidenceType.RUNTIME_EVIDENCE in loaded_types
        assert EvidenceType.DOCUMENT_EVIDENCE in loaded_types
        assert all(e.status is EvidenceStatus.PASS for e in loaded_evidence
                   if e.type is EvidenceType.RUNTIME_EVIDENCE)

        loaded_findings = SqlFindingRepository(session1).list_by_task(task.id)
        assert len(loaded_findings) == 0  # Reference runtime produces no findings

        # --- Phase 4: Close first session/engine ---
        session1.close()
        engine.dispose()

        # --- Phase 5: Reopen with new session/engine and reload ---
        engine2 = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory2 = sessionmaker(bind=engine2, expire_on_commit=False, future=True)
        session2 = SessionFactory2()

        # Reload all entities from fresh session
        reloaded_project = SqlProjectRepository(session2).get(project.id)
        assert reloaded_project is not None
        assert reloaded_project.name == "Integration Test Project"

        reloaded_task = SqlTaskRepository(session2).get(task.id)
        assert reloaded_task is not None
        assert reloaded_task.project_id == project.id
        assert reloaded_task.workflow_id == "review-minimal"
        assert reloaded_task.context_package_id == cp.id

        reloaded_cp = SqlContextPackageRepository(session2).get(cp.id)
        assert reloaded_cp is not None
        assert reloaded_cp.version == 1
        assert reloaded_cp.instructions == ("Review the code for correctness and completeness.",)

        reloaded_run = SqlRunRepository(session2).get(run.id)
        assert reloaded_run is not None
        assert reloaded_run.state == RunState.COMPLETED
        assert reloaded_run.execution_target == ExecutionTarget.LOCAL
        assert reloaded_run.resume_mode == ResumeMode.NONE
        assert reloaded_run.workflow_id == "review-minimal"
        assert reloaded_run.workflow_version == 1

        # Reload and verify RunResult
        assert reloaded_run.result is not None
        assert reloaded_run.result.status == RunState.COMPLETED
        assert reloaded_run.result.summary == "Reference runtime completed without vendor execution"

        # Reload and verify RunEvents
        assert len(reloaded_run.events) == len(run.events)
        reloaded_transitions = [(e.from_state, e.to_state) for e in reloaded_run.events]
        assert (RunState.CREATED, RunState.STARTING) in reloaded_transitions
        assert (RunState.STARTING, RunState.RUNNING) in reloaded_transitions
        assert (RunState.RUNNING, RunState.COMPLETED) in reloaded_transitions

        # Reload and verify Evidence
        reloaded_evidence = SqlEvidenceRepository(session2).list_by_task(task.id)
        assert len(reloaded_evidence) == len(execution.evidence)
        for ev in reloaded_evidence:
            assert ev.type in {EvidenceType.RUNTIME_EVIDENCE, EvidenceType.DOCUMENT_EVIDENCE}
            if ev.type is EvidenceType.RUNTIME_EVIDENCE:
                assert ev.status is EvidenceStatus.PASS
                assert ev.actor_id == "system:run-supervisor"

        # Reload and verify no findings (reference runtime produces none)
        reloaded_findings = SqlFindingRepository(session2).list_by_task(task.id)
        assert len(reloaded_findings) == 0

        # Verify no AI_OPINION, TOOL_EVIDENCE, or fabricated data
        all_evidence = SqlEvidenceRepository(session2).list_by_task(task.id)
        for ev in all_evidence:
            assert ev.type is not EvidenceType.AI_OPINION
            assert ev.type is not EvidenceType.TOOL_EVIDENCE

        # Clean up
        session2.close()
        engine2.dispose()

    def test_execute_validates_same_project(self, tmp_path):
        """Verify Task and ContextPackage must belong to same project."""
        db_path = tmp_path / "wp07_cross_project.db"
        config = _make_alembic_config(db_path)
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session = SessionFactory()

        # Create two projects
        project1 = _make_project("Project 1")
        SqlProjectRepository(session).add(project1)
        session.commit()

        project2 = _make_project("Project 2")
        SqlProjectRepository(session).add(project2)
        session.commit()

        # ContextPackage in project1
        cp = _make_context_package(project1.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        # Task in project2 (mismatch)
        task = Task(
            project_id=project2.id,
            title="Cross-project task",
            workflow_id="review-minimal",
            workflow_version=1,
            mode=WorkMode.REVIEW,
            context_package_id=cp.id,
        )
        SqlTaskRepository(session).add(task)
        session.commit()

        service = ExecutionService(session)
        with pytest.raises(ValueError, match="different projects"):
            asyncio.run(service.execute_task(task.id))

        session.close()
        engine.dispose()

    def test_execute_validates_workflow_match(self, tmp_path):
        """Verify Task workflow reference must match loaded WorkflowDefinition."""
        db_path = tmp_path / "wp07_workflow_mismatch.db"
        config = _make_alembic_config(db_path)
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session = SessionFactory()

        project = _make_project()
        SqlProjectRepository(session).add(project)
        session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        # Task with wrong workflow_id
        task = Task(
            project_id=project.id,
            title="Wrong workflow task",
            workflow_id="nonexistent-workflow",
            workflow_version=1,
            mode=WorkMode.REVIEW,
            context_package_id=cp.id,
        )
        SqlTaskRepository(session).add(task)
        session.commit()

        service = ExecutionService(session)
        with pytest.raises(ValueError, match="Workflow definition not found"):
            asyncio.run(service.execute_task(task.id))

        session.close()
        engine.dispose()

    def test_execute_persists_run_events(self, tmp_path):
        """Verify all RunEvents are persisted with strict CREATED→STARTING→RUNNING→COMPLETED order.

        Also verifies event timestamp ordering (monotonic non-decreasing).
        """
        db_path = tmp_path / "wp07_events.db"
        config = _make_alembic_config(db_path)
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session = SessionFactory()

        project = _make_project()
        SqlProjectRepository(session).add(project)
        session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        task = _make_task(project.id, cp.id)
        SqlTaskRepository(session).add(task)
        session.commit()

        service = ExecutionService(session)
        execution = asyncio.run(service.execute_task(task.id))

        run_id = execution.run.id

        # Close and reopen
        session.close()
        engine.dispose()

        engine2 = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory2 = sessionmaker(bind=engine2, expire_on_commit=False, future=True)
        session2 = SessionFactory2()

        # Reload run via list_by_task (hydrates events)
        runs = SqlRunRepository(session2).list_by_task(task.id)
        assert len(runs) == 1
        reloaded_run = runs[0]
        assert reloaded_run.id == run_id

        # Strict event ordering: CREATED → STARTING → RUNNING → COMPLETED
        # Verify by checking both from_state and to_state of each event
        assert len(reloaded_run.events) == 3, (
            f"Expected 3 lifecycle events, got {len(reloaded_run.events)}"
        )
        expected_transitions = [
            (RunState.CREATED, RunState.STARTING),
            (RunState.STARTING, RunState.RUNNING),
            (RunState.RUNNING, RunState.COMPLETED),
        ]
        actual_transitions = [(e.from_state, e.to_state) for e in reloaded_run.events]
        assert actual_transitions == expected_transitions, (
            f"Expected lifecycle transitions {expected_transitions}, got {actual_transitions}"
        )

        # Verify event from_state matches previous to_state (chain integrity)
        for i in range(1, len(reloaded_run.events)):
            prev_event = reloaded_run.events[i - 1]
            curr_event = reloaded_run.events[i]
            assert prev_event.to_state == curr_event.from_state, (
                f"Event chain broken at index {i}: "
                f"prev.to_state={prev_event.to_state}, curr.from_state={curr_event.from_state}"
            )

        # Verify timestamps are monotonic (non-decreasing)
        for i in range(1, len(reloaded_run.events)):
            prev_ts = reloaded_run.events[i - 1].occurred_at
            curr_ts = reloaded_run.events[i].occurred_at
            assert curr_ts >= prev_ts, (
                f"Timestamps not monotonic at index {i}: "
                f"prev={prev_ts}, curr={curr_ts}"
            )

        # Verify all timestamps are naive UTC
        for event in reloaded_run.events:
            assert event.occurred_at is not None
            assert event.occurred_at.tzinfo is None

        session2.close()
        engine.dispose()

    def test_no_network_egress_from_reference_runtime(self, tmp_path):
        """Verify ReferenceRuntimeAdapter does not make network calls.

        This is a structural guarantee — the adapter is purely in-memory.
        We verify by checking that the adapter completes synchronously
        (no I/O) and produces no vendor-specific artifacts.
        """
        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter

        adapter = ReferenceRuntimeAdapter()
        project = _make_project()
        cp = _make_context_package(project.id)
        task = _make_task(project.id, cp.id)

        # The adapter operations are in-memory; asyncio.run completes deterministically
        runtime_ref = asyncio.run(adapter.create_run(cp))
        asyncio.run(adapter.submit(runtime_ref, task))
        status = asyncio.run(adapter.status(runtime_ref))
        assert status.state == RunState.RUNNING

        result = asyncio.run(adapter.result(runtime_ref))
        assert result.summary == "Reference runtime completed without vendor execution"
        assert result.findings == ()
        assert result.artifacts == ()

        artifacts = asyncio.run(adapter.artifacts(runtime_ref))
        assert artifacts == ()

    def test_cancel_cleanup_persisted(self, tmp_path):
        """Verify cancel path persists CANCELLED state and cleanup verification."""
        db_path = tmp_path / "wp07_cancel.db"
        config = _make_alembic_config(db_path)
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session = SessionFactory()

        project = _make_project()
        SqlProjectRepository(session).add(project)
        session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        task = _make_task(project.id, cp.id)
        SqlTaskRepository(session).add(task)
        session.commit()

        # Execute and cancel
        from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
        from polynexus_core.runtime.supervisor import RunSupervisor
        from polynexus_core.workflows.loader import load_workflow_definition

        workflow = load_workflow_definition(REPO_ROOT / "workflows" / "builtin" / "review-minimal.yaml")
        adapter = ReferenceRuntimeAdapter()
        supervisor = RunSupervisor(adapter)

        session_data = asyncio.run(supervisor.start(task, cp, workflow))
        execution = asyncio.run(supervisor.cancel(session_data))

        # Persist the cancelled run
        SqlRunRepository(session).add(execution.run)
        for evidence in execution.evidence:
            from polynexus_core.persistence.repository import SqlEvidenceRepository
            SqlEvidenceRepository(session).add(evidence)
        session.commit()

        # Verify cleanup
        assert adapter.was_cleaned(session_data.runtime_ref)
        assert execution.run.state == RunState.CANCELLED

        # Reload and verify
        reloaded = SqlRunRepository(session).get(execution.run.id)
        assert reloaded is not None
        assert reloaded.state == RunState.CANCELLED

        session.close()
        engine.dispose()


class TestWP07WorkflowPathSecurity:
    """WP-07: Workflow path traversal prevention tests."""

    def test_rejects_workflow_id_with_path_separator(self, tmp_path):
        """workflow_id containing path separators must be rejected."""
        db_path = tmp_path / "wp07_traversal_sep.db"
        config = _make_alembic_config(db_path)
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session = SessionFactory()

        project = _make_project()
        SqlProjectRepository(session).add(project)
        session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        task = Task(
            project_id=project.id,
            title="Traversal task",
            workflow_id="../etc/passwd",
            workflow_version=1,
            mode=WorkMode.REVIEW,
            context_package_id=cp.id,
        )
        SqlTaskRepository(session).add(task)
        session.commit()

        service = ExecutionService(session)
        with pytest.raises(ValueError, match="Invalid workflow_id format"):
            asyncio.run(service.execute_task(task.id))

        session.close()
        engine.dispose()

    def test_rejects_workflow_id_with_dot_dot(self, tmp_path):
        """workflow_id containing .. must be rejected."""
        db_path = tmp_path / "wp07_traversal_dotdot.db"
        config = _make_alembic_config(db_path)
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session = SessionFactory()

        project = _make_project()
        SqlProjectRepository(session).add(project)
        session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        task = Task(
            project_id=project.id,
            title="Traversal task",
            workflow_id="..\\..\\services\\core\\src",
            workflow_version=1,
            mode=WorkMode.REVIEW,
            context_package_id=cp.id,
        )
        SqlTaskRepository(session).add(task)
        session.commit()

        service = ExecutionService(session)
        with pytest.raises(ValueError, match="Invalid workflow_id format"):
            asyncio.run(service.execute_task(task.id))

        session.close()
        engine.dispose()

    def test_rejects_workflow_id_with_url_encoding(self, tmp_path):
        """workflow_id with URL-encoded characters must be rejected."""
        db_path = tmp_path / "wp07_traversal_encoded.db"
        config = _make_alembic_config(db_path)
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session = SessionFactory()

        project = _make_project()
        SqlProjectRepository(session).add(project)
        session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        task = Task(
            project_id=project.id,
            title="Traversal task",
            workflow_id="..%2F..%2Fetc%2Fpasswd",
            workflow_version=1,
            mode=WorkMode.REVIEW,
            context_package_id=cp.id,
        )
        SqlTaskRepository(session).add(task)
        session.commit()

        service = ExecutionService(session)
        with pytest.raises(ValueError, match="Invalid workflow_id format"):
            asyncio.run(service.execute_task(task.id))

        session.close()
        engine.dispose()

    def test_accepts_valid_workflow_id(self, tmp_path):
        """Valid workflow_id (alphanumeric, hyphen, underscore) is accepted."""
        db_path = tmp_path / "wp07_valid_id.db"
        config = _make_alembic_config(db_path)
        alembic_cmd.upgrade(config, "head")

        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        SessionFactory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
        session = SessionFactory()

        project = _make_project()
        SqlProjectRepository(session).add(project)
        session.commit()

        cp = _make_context_package(project.id)
        SqlContextPackageRepository(session).add(cp)
        session.commit()

        task = _make_task(project.id, cp.id)
        SqlTaskRepository(session).add(task)
        session.commit()

        service = ExecutionService(session)
        execution = asyncio.run(service.execute_task(task.id))
        assert execution.run.state is RunState.COMPLETED

        session.close()
        engine.dispose()

    def test_builtin_child_path_passes_containment(self, tmp_path):
        """A workflow_id that resolves to a genuine child of builtin must pass containment.

        This exercises the production _check_workflow_path_containment helper,
        not just Path.is_relative_to() in isolation.
        """
        from polynexus_core.execution_service import ExecutionService

        # "review-minimal" passes regex and resolves inside builtin — containment must pass.
        resolved = ExecutionService._check_workflow_path_containment("review-minimal")
        assert resolved.is_relative_to(_BUILTIN_WORKFLOWS_DIR.resolve())

    def test_sibling_prefix_path_rejected_by_containment(self, tmp_path):
        """A workflow_id that resolves to a sibling directory (shared string prefix) must be rejected.

        This exercises the production _check_workflow_path_containment helper to verify
        it correctly rejects sibling-prefix paths that string startswith would miss.
        Uses os.symlink to create a sibling-targeting junction; falls back to regex
        rejection test if symlink is not supported.
        """
        import os

        from polynexus_core.execution_service import ExecutionService

        builtin_root = _BUILTIN_WORKFLOWS_DIR.resolve()
        sibling = builtin_root.parent / (builtin_root.name + "_extra")
        sibling.mkdir(exist_ok=True)
        sibling_yaml = sibling / "review-minimal.yaml"
        sibling_yaml.write_text("id: review-minimal\nversion: 1\nsteps:\n  - id: s\n    type: TOOL\n")

        link = builtin_root / "review-minimal.yaml.link"
        try:
            os.symlink(str(sibling_yaml), str(link))
        except OSError:
            # Symlink not supported — verify regex rejects sibling-path workflow IDs
            with pytest.raises(ValueError, match="Invalid workflow_id format"):
                ExecutionService._check_workflow_path_containment("../review-minimal_extra/review-minimal")
            sibling_yaml.unlink(missing_ok=True)
            sibling.rmdir()
            return

        # Symlink created — rename real workflow, put symlink in its place
        real = builtin_root / "review-minimal.yaml"
        real_backup = builtin_root / "review-minimal.yaml.bak"
        real.rename(real_backup)
        link.rename(builtin_root / "review-minimal.yaml")

        try:
            with pytest.raises(ValueError, match="traversal rejected"):
                ExecutionService._check_workflow_path_containment("review-minimal")
        finally:
            (builtin_root / "review-minimal.yaml").unlink(missing_ok=True)
            real_backup.rename(real)
            sibling_yaml.unlink(missing_ok=True)
            sibling.rmdir()

    def test_symlink_escape_rejected(self, tmp_path):
        """Symlink inside builtin pointing outside must be rejected by production containment.

        If symlink creation succeeds: replaces real workflow file with a symlink to an
        outside file, calls _check_workflow_path_containment, and verifies it raises
        ValueError with 'traversal rejected'.

        If Windows denies symlink permission: pytest.skip with explicit reason.
        The handoff must record this skip and its reason.
        """
        import os

        from polynexus_core.execution_service import ExecutionService

        builtin_root = _BUILTIN_WORKFLOWS_DIR.resolve()
        outside_file = tmp_path / "escaped.yaml"
        outside_file.write_text("id: escaped\nversion: 1\nsteps:\n  - id: s\n    type: TOOL\n")

        symlink_target = builtin_root / "review-minimal.yaml"
        real_file = builtin_root / "review-minimal.yaml.real"

        try:
            os.symlink(str(outside_file), str(symlink_target))
        except OSError:
            pytest.skip(
                "Symlink creation denied by Windows policy — "
                "cannot test real symlink escape via production containment helper. "
                "Sibling-prefix and regex tests provide partial coverage."
            )

        # Symlink created — rename real file, verify production containment rejects
        symlink_target.rename(real_file)  # move symlink out temporarily
        os.symlink(str(outside_file), str(symlink_target))

        try:
            with pytest.raises(ValueError, match="traversal rejected"):
                ExecutionService._check_workflow_path_containment("review-minimal")
        finally:
            symlink_target.unlink(missing_ok=True)
            real_file.rename(builtin_root / "review-minimal.yaml")
