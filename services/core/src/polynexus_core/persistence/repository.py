from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import text, update as sa_update
from sqlalchemy.orm import Session

from polynexus_core.domain.enums import (
    ArtifactType,
    AuthOwnership,
    EvidenceStatus,
    EvidenceType,
    ExecutionTarget,
    FindingSeverity,
    FindingStatus,
    ResumeMode,
    RunState,
    TransportKind,
    UsageVisibility,
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
from polynexus_core.domain.runtime_binding import (
    SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS,
    RuntimeBindingError,
    RuntimeBindingSnapshot,
)
from polynexus_core.domain.run_lifecycle import TERMINAL_STATES
from polynexus_core.persistence.models import (
    ArtifactRow,
    Base,
    ContextPackageRow,
    EvidenceRow,
    FindingRow,
    ProjectRow,
    RunBindingSnapshotRow,
    RunEventRow,
    RunRow,
    TaskRow,
    _deserialize_dict,
    _deserialize_tuple,
    _serialize_dict,
    _serialize_tuple,
)


def _ensure_utc_naive(dt: datetime) -> datetime:
    """Normalize a timezone-aware UTC datetime to naive UTC for SQLite storage.

    Contract: Domain timestamps are always timezone-aware UTC.
    SQLite DateTime columns store naive datetimes.
    At the repository write boundary, strip timezone info (assumed UTC).
    At read, SQLite returns naive UTC values directly.
    """
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


# ---------------------------------------------------------------------------
# Domain → ORM conversion helpers
# ---------------------------------------------------------------------------

def _project_to_row(p: Project) -> ProjectRow:
    return ProjectRow(id=p.id, name=p.name, description=p.description, created_at=_ensure_utc_naive(p.created_at), classification=p.classification, archived=p.archived)


def _row_to_project(r: ProjectRow) -> Project:
    return Project(id=r.id, name=r.name, description=r.description, created_at=r.created_at, classification=r.classification, archived=r.archived)


def _task_to_row(t: Task) -> TaskRow:
    return TaskRow(
        id=t.id,
        classification=t.classification,
        project_id=t.project_id,
        title=t.title,
        workflow_id=t.workflow_id,
        workflow_version=t.workflow_version,
        mode=t.mode.value,
        context_package_id=t.context_package_id,
        created_at=_ensure_utc_naive(t.created_at),
    )


def _row_to_task(r: TaskRow) -> Task:
    return Task(
        id=r.id,
        classification=r.classification,
        project_id=r.project_id,
        title=r.title,
        workflow_id=r.workflow_id,
        workflow_version=r.workflow_version,
        mode=WorkMode(r.mode),
        context_package_id=r.context_package_id,
        created_at=r.created_at,
    )


def _cp_to_row(cp: ContextPackage) -> ContextPackageRow:
    return ContextPackageRow(
        id=cp.id,
        classification=cp.classification,
        project_id=cp.project_id,
        version=cp.version,
        instructions=_serialize_tuple(cp.instructions),
        constraints=_serialize_tuple(cp.constraints),
        project_facts=_serialize_dict(dict(cp.project_facts)),
        artifact_refs=_serialize_tuple(cp.artifact_refs),
        prior_decision_refs=_serialize_tuple(cp.prior_decision_refs),
        memory_refs=_serialize_tuple(cp.memory_refs),
        source_refs=_serialize_tuple(cp.source_refs),
        created_at=_ensure_utc_naive(cp.created_at),
    )


def _row_to_cp(r: ContextPackageRow) -> ContextPackage:
    return ContextPackage(
        id=r.id,
        classification=r.classification,
        project_id=r.project_id,
        version=r.version,
        instructions=_deserialize_tuple(r.instructions),
        constraints=_deserialize_tuple(r.constraints),
        project_facts=_deserialize_dict(r.project_facts),
        artifact_refs=_deserialize_tuple(r.artifact_refs),
        prior_decision_refs=_deserialize_tuple(r.prior_decision_refs),
        memory_refs=_deserialize_tuple(r.memory_refs),
        source_refs=_deserialize_tuple(r.source_refs),
        created_at=r.created_at,
    )


def _run_to_row(run: Run) -> RunRow:
    result_status = run.result.status.value if run.result else None
    result_summary = run.result.summary if run.result else None
    result_finding_ids = _serialize_tuple(run.result.finding_ids) if run.result else "[]"
    result_evidence_ids = _serialize_tuple(run.result.evidence_ids) if run.result else "[]"
    result_artifact_ids = _serialize_tuple(run.result.artifact_ids) if run.result else "[]"
    return RunRow(
        id=run.id,
        generation_revision=run.generation_revision,
        generation_parent_run_id=run.generation_parent_run_id,
        task_id=run.task_id,
        workflow_id=run.workflow_id,
        workflow_version=run.workflow_version,
        context_package_id=run.context_package_id,
        execution_target=run.execution_target.value,
        resume_mode=run.resume_mode.value,
        state=run.state.value,
        runtime_ref=run.runtime_ref,
        created_at=_ensure_utc_naive(run.created_at),
        updated_at=_ensure_utc_naive(run.updated_at),
        result_status=result_status,
        result_summary=result_summary,
        result_finding_ids=result_finding_ids,
        result_evidence_ids=result_evidence_ids,
        result_artifact_ids=result_artifact_ids,
    )


def _row_to_run(r: RunRow) -> Run:
    result = None
    if r.result_status:
        result = RunResult(
            run_id=r.id,
            status=RunState(r.result_status),
            summary=r.result_summary or "",
            finding_ids=_deserialize_tuple(r.result_finding_ids),
            evidence_ids=_deserialize_tuple(r.result_evidence_ids),
            artifact_ids=_deserialize_tuple(r.result_artifact_ids),
        )
    run = Run(
        id=r.id,
        generation_revision=r.generation_revision,
        generation_parent_run_id=r.generation_parent_run_id,
        task_id=r.task_id,
        workflow_id=r.workflow_id,
        workflow_version=r.workflow_version,
        context_package_id=r.context_package_id,
        execution_target=ExecutionTarget(r.execution_target),
        resume_mode=ResumeMode(r.resume_mode),
        state=RunState(r.state),
        runtime_ref=r.runtime_ref,
        created_at=r.created_at,
        updated_at=r.updated_at,
        result=result,
    )
    return run


def _event_to_row(e: RunEvent) -> RunEventRow:
    return RunEventRow(
        id=e.id,
        run_id=e.run_id,
        from_state=e.from_state.value,
        to_state=e.to_state.value,
        occurred_at=_ensure_utc_naive(e.occurred_at),
        reason=e.reason,
    )


def _row_to_event(r: RunEventRow) -> RunEvent:
    return RunEvent(
        id=r.id,
        run_id=r.run_id,
        from_state=RunState(r.from_state),
        to_state=RunState(r.to_state),
        occurred_at=r.occurred_at,
        reason=r.reason,
    )


def _append_events(session: Session, events: Sequence[RunEvent]) -> None:
    """Allocate per-Run ordinals atomically in the caller's transaction."""
    grouped: dict[str, list[RunEvent]] = {}
    for event in events:
        grouped.setdefault(event.run_id, []).append(event)
    for run_id, batch in grouped.items():
        high = session.execute(
            sa_update(RunRow)
            .where(RunRow.id == run_id)
            .values(next_event_sequence=RunRow.next_event_sequence + len(batch))
            .returning(RunRow.next_event_sequence)
        ).scalar_one_or_none()
        if high is None:
            raise ValueError(f"Run {run_id} not found for event append")
        for sequence, event in enumerate(batch, high - len(batch) + 1):
            row = _event_to_row(event)
            row.event_sequence = sequence
            row.sequence_legacy_backfill = False
            session.add(row)


def _artifact_to_row(a: Artifact) -> ArtifactRow:
    return ArtifactRow(
        id=a.id,
        classification=a.classification,
        project_id=a.project_id,
        artifact_type=a.artifact_type.value,
        mime_type=a.mime_type,
        source_type=a.source_type,
        storage_ref=a.storage_ref,
        sha256=a.sha256,
        size=a.size,
        task_id=a.task_id,
        run_id=a.run_id,
    )


def _row_to_artifact(r: ArtifactRow) -> Artifact:
    return Artifact(
        id=r.id,
        classification=r.classification,
        project_id=r.project_id,
        artifact_type=ArtifactType(r.artifact_type),
        mime_type=r.mime_type,
        source_type=r.source_type,
        storage_ref=r.storage_ref,
        sha256=r.sha256,
        size=r.size,
        task_id=r.task_id,
        run_id=r.run_id,
    )


def _finding_to_row(f: Finding) -> FindingRow:
    return FindingRow(
        id=f.id,
        task_id=f.task_id,
        run_id=f.run_id,
        title=f.title,
        description=f.description,
        severity=f.severity.value,
        evidence_refs=_serialize_tuple(f.evidence_refs),
        status=f.status.value,
        created_at=_ensure_utc_naive(f.created_at),
    )


def _row_to_finding(r: FindingRow) -> Finding:
    return Finding(
        id=r.id,
        task_id=r.task_id,
        run_id=r.run_id,
        title=r.title,
        description=r.description,
        severity=FindingSeverity(r.severity),
        evidence_refs=_deserialize_tuple(r.evidence_refs),
        status=FindingStatus(r.status),
        created_at=r.created_at,
    )


def _evidence_to_row(e: Evidence) -> EvidenceRow:
    return EvidenceRow(
        id=e.id,
        task_id=e.task_id,
        run_id=e.run_id,
        actor_id=e.actor_id,
        source=e.source,
        type=e.type.value,
        status=e.status.value,
        artifact_refs=_serialize_tuple(e.artifact_refs),
        metadata_json=_serialize_dict(dict(e.metadata)),
        observed_at=_ensure_utc_naive(e.observed_at),
    )


def _row_to_evidence(r: EvidenceRow) -> Evidence:
    return Evidence(
        id=r.id,
        task_id=r.task_id,
        run_id=r.run_id,
        actor_id=r.actor_id,
        source=r.source,
        type=EvidenceType(r.type),
        status=EvidenceStatus(r.status),
        artifact_refs=_deserialize_tuple(r.artifact_refs),
        metadata=_deserialize_dict(r.metadata_json),
        observed_at=r.observed_at,
    )


def _snapshot_to_row(s: RuntimeBindingSnapshot) -> RunBindingSnapshotRow:
    return RunBindingSnapshotRow(
        run_id=s.run_id,
        provider_id=s.provider_id,
        transport_kind=s.transport_kind.value,
        runtime_id=s.runtime_id,
        adapter_id=s.adapter_id,
        execution_target=s.execution_target.value,
        runtime_profile_ref=s.runtime_profile_ref,
        profile_revision=s.profile_revision,
        adapter_version=s.adapter_version,
        resolved_at=_ensure_utc_naive(s.resolved_at),
        legacy_backfill=s.legacy_backfill,
        snapshot_schema_version=s.snapshot_schema_version,
        auth_ownership=s.auth_ownership.value,
        secret_ref_id=s.secret_ref_id,
        usage_visibility=s.usage_visibility.value,
    )


def _row_to_snapshot(r: RunBindingSnapshotRow) -> RuntimeBindingSnapshot:
    # Unknown snapshot_schema_version raises RuntimeBindingError here —
    # reload of an unsupported version fails closed instead of guessing.
    return RuntimeBindingSnapshot(
        run_id=r.run_id,
        provider_id=r.provider_id,
        transport_kind=TransportKind(r.transport_kind),
        runtime_id=r.runtime_id,
        adapter_id=r.adapter_id,
        execution_target=ExecutionTarget(r.execution_target),
        runtime_profile_ref=r.runtime_profile_ref,
        profile_revision=r.profile_revision,
        adapter_version=r.adapter_version,
        resolved_at=r.resolved_at.replace(tzinfo=timezone.utc),
        legacy_backfill=bool(r.legacy_backfill),
        snapshot_schema_version=r.snapshot_schema_version,
        auth_ownership=AuthOwnership(r.auth_ownership),
        secret_ref_id=r.secret_ref_id,
        usage_visibility=UsageVisibility(r.usage_visibility),
    )


# ---------------------------------------------------------------------------
# Repository Interfaces (ABC)
# ---------------------------------------------------------------------------

class ProjectRepository(ABC):
    @abstractmethod
    def add(self, project: Project) -> None: ...

    @abstractmethod
    def get(self, project_id: str) -> Project | None: ...

    @abstractmethod
    def list_all(self) -> Sequence[Project]: ...

    @abstractmethod
    def delete(self, project_id: str) -> bool: ...


class TaskRepository(ABC):
    @abstractmethod
    def add(self, task: Task) -> None: ...

    @abstractmethod
    def get(self, task_id: str) -> Task | None: ...

    @abstractmethod
    def list_by_project(self, project_id: str) -> Sequence[Task]: ...


class ContextPackageRepository(ABC):
    @abstractmethod
    def add(self, cp: ContextPackage) -> None: ...

    @abstractmethod
    def get(self, cp_id: str) -> ContextPackage | None: ...


class RunRepository(ABC):
    @abstractmethod
    def add(self, run: Run) -> None: ...

    @abstractmethod
    def get(self, run_id: str) -> Run | None: ...

    @abstractmethod
    def list_by_task(self, task_id: str) -> Sequence[Run]: ...

    @abstractmethod
    def list_non_terminal(self) -> Sequence[Run]:
        """List durable Runs that require startup reconciliation."""

    @abstractmethod
    def update(self, run: Run) -> None: ...

    @abstractmethod
    def claim_for_execution(self, run_id: str) -> bool:
        """Atomically claim a Run for execution using CAS.

        Executes: UPDATE runs SET state = 'STARTING' WHERE id = :run_id AND state = 'CREATED'
        Returns True if the claim succeeded (1 row updated), False if another caller
        already claimed the Run or the Run is not in CREATED state.

        This is a one-winner mechanism — two sessions calling simultaneously will
        produce at most one successful claim.
        """

    @abstractmethod
    def append_event(self, event: RunEvent) -> None:
        """Append a single RunEvent to the database (used for claim event persistence)."""


class RunEventRepository(ABC):
    @abstractmethod
    def add(self, event: RunEvent) -> None: ...

    @abstractmethod
    def list_by_run(self, run_id: str) -> Sequence[RunEvent]: ...


class RuntimeBindingSnapshotRepository(ABC):
    """Minimal immutable snapshot contract (ADR-011 / PRE-WP14-B).

    insert-once semantics: a second insert for the same Run fails closed,
    update and delete are always rejected, and Run lifecycle updates can
    never overwrite a persisted binding.
    """

    @abstractmethod
    def insert_once(self, snapshot: RuntimeBindingSnapshot) -> None:
        """Insert the snapshot; raise RuntimeBindingError if the Run is already bound."""

    @abstractmethod
    def get_by_run(self, run_id: str) -> RuntimeBindingSnapshot | None:
        """Reload the snapshot for a Run; unknown schema versions fail closed."""

    @abstractmethod
    def exists_for_run(self, run_id: str) -> bool: ...

    @abstractmethod
    def update(self, snapshot: RuntimeBindingSnapshot) -> None:
        """Always rejected — snapshots are immutable."""

    @abstractmethod
    def delete(self, run_id: str) -> None:
        """Always rejected — snapshots are immutable."""


class ArtifactRepository(ABC):
    @abstractmethod
    def add(self, artifact: Artifact) -> None: ...

    @abstractmethod
    def get(self, artifact_id: str) -> Artifact | None: ...

    @abstractmethod
    def list_by_project(self, project_id: str) -> Sequence[Artifact]: ...

    @abstractmethod
    def list_by_run(self, run_id: str) -> Sequence[Artifact]: ...


class FindingRepository(ABC):
    @abstractmethod
    def add(self, finding: Finding) -> None: ...

    @abstractmethod
    def get(self, finding_id: str) -> Finding | None: ...

    @abstractmethod
    def list_by_task(self, task_id: str) -> Sequence[Finding]: ...

    @abstractmethod
    def list_by_run(self, run_id: str) -> Sequence[Finding]: ...


class EvidenceRepository(ABC):
    @abstractmethod
    def add(self, evidence: Evidence) -> None: ...

    @abstractmethod
    def get(self, evidence_id: str) -> Evidence | None: ...

    @abstractmethod
    def list_by_task(self, task_id: str) -> Sequence[Evidence]: ...

    @abstractmethod
    def list_by_run(self, run_id: str) -> Sequence[Evidence]: ...

    @abstractmethod
    def list_all(self) -> Sequence[Evidence]: ...

    @abstractmethod
    def update(self, evidence: Evidence) -> None: ...


# ---------------------------------------------------------------------------
# SQLite Implementations
# ---------------------------------------------------------------------------

class SqlProjectRepository(ProjectRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, project: Project) -> None:
        self._s.add(_project_to_row(project))

    def get(self, project_id: str) -> Project | None:
        r = self._s.get(ProjectRow, project_id)
        return _row_to_project(r) if r else None

    def list_all(self) -> Sequence[Project]:
        rows = self._s.query(ProjectRow).all()
        return [_row_to_project(r) for r in rows]

    def reserve_write(self, project_id: str) -> bool:
        """Serialize new work against archive in the caller's transaction."""
        return self._s.execute(text("UPDATE projects SET archived=archived WHERE id=:id AND archived=0"),{"id":project_id}).rowcount == 1

    def archive(self, project_id: str) -> Project | None:
        row = self._s.get(ProjectRow, project_id)
        if row is None:
            return None
        row.archived = True
        self._s.flush()
        return _row_to_project(row)

    def delete(self, project_id: str) -> bool:
        r = self._s.get(ProjectRow, project_id)
        if r is None:
            return False
        self._s.delete(r)
        return True


class SqlTaskRepository(TaskRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, task: Task) -> None:
        self._s.add(_task_to_row(task))

    def get(self, task_id: str) -> Task | None:
        r = self._s.get(TaskRow, task_id)
        return _row_to_task(r) if r else None

    def list_by_project(self, project_id: str) -> Sequence[Task]:
        rows = self._s.query(TaskRow).filter_by(project_id=project_id).all()
        return [_row_to_task(r) for r in rows]


class SqlContextPackageRepository(ContextPackageRepository):
    def list_by_project(self, project_id):
        rows = self._s.query(ContextPackageRow).filter_by(project_id=project_id).order_by(ContextPackageRow.version, ContextPackageRow.id).all()
        return [_row_to_cp(row) for row in rows]

    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, cp: ContextPackage) -> None:
        self._s.add(_cp_to_row(cp))

    def get(self, cp_id: str) -> ContextPackage | None:
        r = self._s.get(ContextPackageRow, cp_id)
        return _row_to_cp(r) if r else None


class SqlRunRepository(RunRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, run: Run) -> None:
        self._s.add(_run_to_row(run))
        self._s.flush()
        _append_events(self._s, run.events)

    def get(self, run_id: str) -> Run | None:
        r = self._s.get(RunRow, run_id)
        if r is None:
            return None
        run = _row_to_run(r)
        event_rows = (
            self._s.query(RunEventRow)
            .filter_by(run_id=run_id)
            .order_by(RunEventRow.run_id, RunEventRow.event_sequence)
            .all()
        )
        run.events = [_row_to_event(er) for er in event_rows]
        return run

    def list_by_task(self, task_id: str) -> Sequence[Run]:
        rows = (
            self._s.query(RunRow)
            .filter_by(task_id=task_id)
            .order_by(RunRow.created_at)
            .all()
        )
        runs = []
        for r in rows:
            run = _row_to_run(r)
            event_rows = (
                self._s.query(RunEventRow)
                .filter_by(run_id=r.id)
                .order_by(RunEventRow.run_id, RunEventRow.event_sequence)
                .all()
            )
            run.events = [_row_to_event(er) for er in event_rows]
            runs.append(run)
        return runs

    def list_non_terminal(self) -> Sequence[Run]:
        """Load all non-terminal Runs in deterministic creation order."""
        terminal_values = [state.value for state in TERMINAL_STATES]
        rows = (
            self._s.query(RunRow)
            .filter(RunRow.state.notin_(terminal_values))
            .order_by(RunRow.created_at, RunRow.id)
            .all()
        )
        runs = []
        for r in rows:
            run = _row_to_run(r)
            event_rows = (
                self._s.query(RunEventRow)
                .filter_by(run_id=r.id)
                .order_by(RunEventRow.run_id, RunEventRow.event_sequence)
                .all()
            )
            run.events = [_row_to_event(er) for er in event_rows]
            runs.append(run)
        return runs

    def update(self, run: Run) -> None:
        existing = self._s.get(RunRow, run.id)
        if existing is None:
            raise ValueError(f"Run {run.id} not found")
        updated = _run_to_row(run)
        for col in RunRow.__table__.columns:
            if col.name == "next_event_sequence":
                continue
            setattr(existing, col.name, getattr(updated, col.name))
        existing_events = (
            self._s.query(RunEventRow).filter_by(run_id=run.id).all()
        )
        existing_event_ids = {e.id for e in existing_events}
        _append_events(self._s, [event for event in run.events if event.id not in existing_event_ids])

    def claim_for_execution(self, run_id: str) -> bool:
        """Atomically claim a Run for execution using CAS.

        Executes: UPDATE runs SET state = 'STARTING' WHERE id = :run_id AND state = 'CREATED'
        Returns True if the claim succeeded (1 row updated), False if another caller
        already claimed the Run or the Run is not in CREATED state.

        This is a one-winner mechanism — two sessions calling simultaneously will
        produce at most one successful claim.
        """
        from sqlalchemy import text, update as sa_update

        stmt = (
            sa_update(RunRow)
            .where(RunRow.id == run_id, RunRow.state == RunState.CREATED.value)
            .values(state=RunState.STARTING.value)
        )
        result = self._s.execute(stmt)
        self._s.flush()
        return result.rowcount == 1

    def append_event(self, event: RunEvent) -> None:
        """Append a single RunEvent to the database."""
        _append_events(self._s, [event])
        self._s.flush()


class SqlRunEventRepository(RunEventRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, event: RunEvent) -> None:
        _append_events(self._s, [event])

    def list_by_run(self, run_id: str) -> Sequence[RunEvent]:
        rows = (
            self._s.query(RunEventRow)
            .filter_by(run_id=run_id)
            .order_by(RunEventRow.run_id, RunEventRow.event_sequence)
            .all()
        )
        return [_row_to_event(r) for r in rows]


class SqlRuntimeBindingSnapshotRepository(RuntimeBindingSnapshotRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def insert_once(self, snapshot: RuntimeBindingSnapshot) -> None:
        if self.exists_for_run(snapshot.run_id):
            raise RuntimeBindingError(
                f"Run {snapshot.run_id} is already bound; rebinding is rejected"
            )
        self._s.add(_snapshot_to_row(snapshot))
        self._s.flush()

    def get_by_run(self, run_id: str) -> RuntimeBindingSnapshot | None:
        r = self._s.get(RunBindingSnapshotRow, run_id)
        if r is None:
            return None
        # Unknown snapshot_schema_version raises RuntimeBindingError (fail closed).
        return _row_to_snapshot(r)

    def exists_for_run(self, run_id: str) -> bool:
        return self._s.get(RunBindingSnapshotRow, run_id) is not None

    def update(self, snapshot: RuntimeBindingSnapshot) -> None:
        raise RuntimeBindingError(
            "RuntimeBindingSnapshot update is rejected (snapshots are immutable)"
        )

    def delete(self, run_id: str) -> None:
        raise RuntimeBindingError(
            "RuntimeBindingSnapshot delete is rejected (snapshots are immutable)"
        )


class SqlArtifactRepository(ArtifactRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, artifact: Artifact) -> None:
        self._s.add(_artifact_to_row(artifact))

    def get(self, artifact_id: str) -> Artifact | None:
        r = self._s.get(ArtifactRow, artifact_id)
        return _row_to_artifact(r) if r else None

    def list_by_project(self, project_id: str) -> Sequence[Artifact]:
        rows = self._s.query(ArtifactRow).filter_by(project_id=project_id).all()
        return [_row_to_artifact(r) for r in rows]

    def list_by_run(self, run_id: str) -> Sequence[Artifact]:
        rows = (
            self._s.query(ArtifactRow)
            .filter_by(run_id=run_id)
            .order_by(ArtifactRow.id)
            .all()
        )
        return [_row_to_artifact(r) for r in rows]


class SqlFindingRepository(FindingRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, finding: Finding) -> None:
        self._s.add(_finding_to_row(finding))

    def get(self, finding_id: str) -> Finding | None:
        r = self._s.get(FindingRow, finding_id)
        return _row_to_finding(r) if r else None

    def list_by_task(self, task_id: str) -> Sequence[Finding]:
        rows = self._s.query(FindingRow).filter_by(task_id=task_id).all()
        return [_row_to_finding(r) for r in rows]

    def list_by_run(self, run_id: str) -> Sequence[Finding]:
        rows = (
            self._s.query(FindingRow)
            .filter_by(run_id=run_id)
            .order_by(FindingRow.created_at, FindingRow.id)
            .all()
        )
        return [_row_to_finding(r) for r in rows]


class SqlEvidenceRepository(EvidenceRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, evidence: Evidence) -> None:
        self._s.add(_evidence_to_row(evidence))

    def get(self, evidence_id: str) -> Evidence | None:
        r = self._s.get(EvidenceRow, evidence_id)
        return _row_to_evidence(r) if r else None

    def list_by_task(self, task_id: str) -> Sequence[Evidence]:
        rows = self._s.query(EvidenceRow).filter_by(task_id=task_id).all()
        return [_row_to_evidence(r) for r in rows]

    def list_by_run(self, run_id: str) -> Sequence[Evidence]:
        rows = (
            self._s.query(EvidenceRow)
            .filter_by(run_id=run_id)
            .order_by(EvidenceRow.observed_at, EvidenceRow.id)
            .all()
        )
        return [_row_to_evidence(r) for r in rows]

    def list_all(self) -> Sequence[Evidence]:
        rows = self._s.query(EvidenceRow).order_by(
            EvidenceRow.observed_at, EvidenceRow.id
        ).all()
        return [_row_to_evidence(r) for r in rows]

    def update(self, evidence: Evidence) -> None:
        existing = self._s.get(EvidenceRow, evidence.id)
        if existing is None:
            raise ValueError(f"Evidence {evidence.id} not found")
        updated = _evidence_to_row(evidence)
        for col in EvidenceRow.__table__.columns:
            setattr(existing, col.name, getattr(updated, col.name))
