"""Minimal integration service — executes a Task through RunSupervisor and persists results.

This is a thin orchestration layer that connects:
- Repository layer (persistence) for loading Task/ContextPackage and saving results
- Workflow loader for loading WorkflowDefinition
- RunSupervisor + ReferenceRuntimeAdapter for execution

It does NOT own Domain logic, persistence schema, or runtime adapter internals.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from sqlalchemy.orm import Session

from polynexus_core.domain.models import (
    ContextPackage,
    Finding,
    Evidence,
    Project,
    Task,
    Run,
    RunResult,
)
from polynexus_core.persistence.repository import (
    ArtifactRepository,
    ContextPackageRepository,
    EvidenceRepository,
    FindingRepository,
    ProjectRepository,
    RunRepository,
    RunEventRepository,
    SqlArtifactRepository,
    SqlContextPackageRepository,
    SqlEvidenceRepository,
    SqlFindingRepository,
    SqlProjectRepository,
    SqlRunRepository,
    SqlRunEventRepository,
    SqlTaskRepository,
    TaskRepository,
)
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.supervisor import RunExecution, RunSupervisor
from polynexus_core.workflows.loader import load_workflow_definition
from polynexus_core.workflows.models import WorkflowDefinition


_REPO_ROOT = Path(__file__).resolve().parents[4]
_BUILTIN_WORKFLOWS_DIR = _REPO_ROOT / "workflows" / "builtin"

# Allowlist: only alphanumeric, hyphen, underscore workflow IDs.
# Rejects path separators, dots, and any traversal characters.
_WORKFLOW_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


class ExecutionService:
    """Thin integration layer: load entities, execute via RunSupervisor, persist results."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._project_repo: ProjectRepository = SqlProjectRepository(session)
        self._task_repo: TaskRepository = SqlTaskRepository(session)
        self._cp_repo: ContextPackageRepository = SqlContextPackageRepository(session)
        self._run_repo: RunRepository = SqlRunRepository(session)
        self._finding_repo: FindingRepository = SqlFindingRepository(session)
        self._evidence_repo: EvidenceRepository = SqlEvidenceRepository(session)
        self._artifact_repo: ArtifactRepository = SqlArtifactRepository(session)

    async def execute_task(self, task_id: str) -> RunExecution:
        """Execute a task through RunSupervisor and persist all results.

        Steps:
        1. Load Task and ContextPackage from repositories, validate same project.
        2. Load WorkflowDefinition from builtin YAML, validate task workflow reference.
        3. Execute via RunSupervisor + ReferenceRuntimeAdapter.
        4. Persist Run, RunEvents, RunResult, Finding, Evidence, Artifact through repositories.
        5. Commit and return the RunExecution.

        Raises:
            ValueError: if Task/ContextPackage mismatch, workflow mismatch, or entity not found.
        """
        # 1. Load Task and ContextPackage
        task = self._task_repo.get(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} not found")

        if task.context_package_id is None:
            raise ValueError(f"Task {task_id} has no ContextPackage")

        context = self._cp_repo.get(task.context_package_id)
        if context is None:
            raise ValueError(f"ContextPackage {task.context_package_id} not found")

        if task.project_id != context.project_id:
            raise ValueError("Task and ContextPackage belong to different projects")

        # 2. Load WorkflowDefinition from builtin YAML
        workflow = self._load_workflow(task.workflow_id, task.workflow_version)

        # 3. Execute via RunSupervisor
        adapter = ReferenceRuntimeAdapter()
        supervisor = RunSupervisor(adapter)

        session_data = await supervisor.start(task, context, workflow)
        execution = await supervisor.collect(session_data)

        # 4. Persist all results
        self._persist_execution(execution)

        # 5. Commit
        self._session.commit()

        return execution

    def _load_workflow(self, workflow_id: str, workflow_version: int) -> WorkflowDefinition:
        """Load a workflow from builtin YAML and validate it matches the task reference.

        Security: workflow_id is validated against an allowlist pattern and the resolved
        path must remain within the builtin workflows directory (no traversal).
        """
        workflow_path = self._check_workflow_path_containment(workflow_id)

        if not workflow_path.exists():
            raise ValueError(f"Workflow definition not found: {workflow_id}")

        workflow = load_workflow_definition(workflow_path)

        if workflow.id != workflow_id:
            raise ValueError(f"Workflow id mismatch: expected {workflow_id}, got {workflow.id}")
        if workflow.version != workflow_version:
            raise ValueError(
                f"Workflow version mismatch: expected {workflow_version}, got {workflow.version}"
            )

        return workflow

    @staticmethod
    def _check_workflow_path_containment(workflow_id: str) -> Path:
        """Validate workflow_id format and resolve path containment.

        Returns the resolved workflow path if containment passes.
        Raises ValueError if the workflow_id fails regex validation or path containment.

        This is the production security logic — tests should call this method
        (or _load_workflow) rather than duplicating Path.is_relative_to().
        """
        if not _WORKFLOW_ID_PATTERN.match(workflow_id):
            raise ValueError(
                f"Invalid workflow_id format: {workflow_id!r}. "
                "Workflow IDs must contain only alphanumeric, hyphen, or underscore characters."
            )

        workflow_path = (_BUILTIN_WORKFLOWS_DIR / f"{workflow_id}.yaml").resolve()

        if not workflow_path.is_relative_to(_BUILTIN_WORKFLOWS_DIR.resolve()):
            raise ValueError(
                f"Workflow path traversal rejected: {workflow_id!r} resolves outside builtin directory."
            )

        return workflow_path

    def _persist_execution(self, execution: RunExecution) -> None:
        """Persist Run, RunEvents, RunResult, Finding, Evidence, Artifact through repositories."""
        # Persist the Run (includes state and events)
        self._run_repo.add(execution.run)

        # Persist Finding (ReferenceRuntimeAdapter produces no findings, but persist if present)
        for finding in execution.findings:
            self._finding_repo.add(finding)

        # Persist Evidence (RunSupervisor always produces RUNTIME_EVIDENCE)
        for evidence in execution.evidence:
            self._evidence_repo.add(evidence)

        # Persist Artifact (ReferenceRuntimeAdapter produces none, but persist if present)
        for artifact in execution.artifacts:
            self._artifact_repo.add(artifact)
