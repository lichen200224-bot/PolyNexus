from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping
from uuid import uuid4

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
from polynexus_core.domain.run_lifecycle import assert_transition


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Project:
    name: str
    id: str = field(default_factory=lambda: new_id("project"))
    description: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    classification: str = "INTERNAL"
    archived: bool = False

    def __post_init__(self) -> None:
        if self.classification not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise ValueError("Invalid data classification")
        if not self.name.strip():
            raise ValueError("Project name must not be empty")


@dataclass
class Task:
    project_id: str
    title: str
    workflow_id: str
    workflow_version: int
    id: str = field(default_factory=lambda: new_id("task"))
    mode: WorkMode = WorkMode.REVIEW
    context_package_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)

    classification: str = "INTERNAL"

    def __post_init__(self) -> None:
        if self.classification not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise ValueError("Invalid data classification")
        if not self.title.strip():
            raise ValueError("Task title must not be empty")
        if self.workflow_version < 1:
            raise ValueError("Task workflow_version must be positive")


@dataclass(frozen=True)
class ContextPackage:
    project_id: str
    version: int
    instructions: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    project_facts: Mapping[str, str] = field(default_factory=dict)
    artifact_refs: tuple[str, ...] = ()
    prior_decision_refs: tuple[str, ...] = ()
    memory_refs: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()
    id: str = field(default_factory=lambda: new_id("context"))
    created_at: datetime = field(default_factory=utc_now)

    classification: str = "INTERNAL"

    def __post_init__(self) -> None:
        if self.classification not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise ValueError("Invalid data classification")
        if self.version < 1:
            raise ValueError("ContextPackage version must be positive")
        object.__setattr__(self, "instructions", tuple(self.instructions))
        object.__setattr__(self, "constraints", tuple(self.constraints))
        object.__setattr__(self, "project_facts", dict(self.project_facts))
        object.__setattr__(self, "artifact_refs", tuple(self.artifact_refs))
        object.__setattr__(self, "prior_decision_refs", tuple(self.prior_decision_refs))
        object.__setattr__(self, "memory_refs", tuple(self.memory_refs))
        object.__setattr__(self, "source_refs", tuple(self.source_refs))


@dataclass(frozen=True)
class Artifact:
    project_id: str
    artifact_type: ArtifactType
    mime_type: str
    source_type: str
    storage_ref: str
    sha256: str
    size: int = 0
    task_id: str | None = None
    run_id: str | None = None
    id: str = field(default_factory=lambda: new_id("artifact"))

    classification: str = "INTERNAL"

    def __post_init__(self) -> None:
        if self.classification not in {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}:
            raise ValueError("Invalid data classification")
        if self.size < 0:
            raise ValueError("Artifact size must not be negative")
        if not self.sha256.strip():
            raise ValueError("Artifact sha256 must not be empty")


@dataclass(frozen=True)
class Evidence:
    task_id: str
    run_id: str
    actor_id: str
    source: str
    type: EvidenceType
    status: EvidenceStatus = EvidenceStatus.OBSERVED
    artifact_refs: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: new_id("evidence"))
    observed_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_refs", tuple(self.artifact_refs))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass
class Finding:
    task_id: str
    run_id: str
    title: str
    description: str
    severity: FindingSeverity
    evidence_refs: tuple[str, ...] = ()
    status: FindingStatus = FindingStatus.OPEN
    id: str = field(default_factory=lambda: new_id("finding"))
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Finding title must not be empty")
        object.__setattr__(self, "evidence_refs", tuple(self.evidence_refs))


@dataclass(frozen=True)
class RunEvent:
    run_id: str
    from_state: RunState
    to_state: RunState
    occurred_at: datetime = field(default_factory=utc_now)
    reason: str | None = None
    id: str = field(default_factory=lambda: new_id("run-event"))


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: RunState
    summary: str
    finding_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    artifact_ids: tuple[str, ...] = ()


@dataclass
class Run:
    task_id: str
    workflow_id: str
    workflow_version: int
    context_package_id: str
    id: str = field(default_factory=lambda: new_id("run"))
    execution_target: ExecutionTarget = ExecutionTarget.LOCAL
    resume_mode: ResumeMode = ResumeMode.NONE
    state: RunState = RunState.CREATED
    runtime_ref: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    events: list[RunEvent] = field(default_factory=list)
    result: RunResult | None = None
    generation_revision: int | None = None
    generation_parent_run_id: str | None = None

    def __post_init__(self) -> None:
        if self.workflow_version < 1:
            raise ValueError("Run workflow_version must be positive")

    def transition(self, target: RunState, reason: str | None = None) -> RunEvent:
        assert_transition(self.state, target)
        event = RunEvent(
            run_id=self.id,
            from_state=self.state,
            to_state=target,
            reason=reason,
        )
        self.state = target
        self.updated_at = event.occurred_at
        self.events.append(event)
        return event
