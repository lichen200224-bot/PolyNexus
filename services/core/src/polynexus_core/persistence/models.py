from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from polynexus_core.domain.runtime_binding import RuntimeBindingError


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)


class TaskRow(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    title = Column(String(512), nullable=False)
    workflow_id = Column(String(128), nullable=False)
    workflow_version = Column(Integer, nullable=False)
    mode = Column(String(32), nullable=False)
    context_package_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False)

    project = relationship("ProjectRow", backref="tasks")


class ContextPackageRow(Base):
    __tablename__ = "context_packages"

    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, nullable=False)
    instructions = Column(Text, nullable=False, default="[]")
    constraints = Column(Text, nullable=False, default="[]")
    project_facts = Column(Text, nullable=False, default="{}")
    artifact_refs = Column(Text, nullable=False, default="[]")
    prior_decision_refs = Column(Text, nullable=False, default="[]")
    memory_refs = Column(Text, nullable=False, default="[]")
    source_refs = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, nullable=False)

    project = relationship("ProjectRow", backref="context_packages")


class RunRow(Base):
    __tablename__ = "runs"

    id = Column(String(64), primary_key=True)
    next_event_sequence = Column(Integer, nullable=False, default=0, server_default="0")
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    workflow_id = Column(String(128), nullable=False)
    workflow_version = Column(Integer, nullable=False)
    context_package_id = Column(String(64), nullable=False)
    execution_target = Column(String(32), nullable=False)
    resume_mode = Column(String(32), nullable=False)
    state = Column(String(32), nullable=False)
    runtime_ref = Column(String(256), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    result_status = Column(String(32), nullable=True)
    result_summary = Column(Text, nullable=True)
    result_finding_ids = Column(Text, nullable=False, default="[]")
    result_evidence_ids = Column(Text, nullable=False, default="[]")
    result_artifact_ids = Column(Text, nullable=False, default="[]")

    task = relationship("TaskRow", backref="runs")


class RunEventRow(Base):
    __tablename__ = "run_events"
    __table_args__ = (
        UniqueConstraint("run_id", "event_sequence", name="uq_run_events_sequence"),
        CheckConstraint("event_sequence > 0", name="ck_run_events_sequence_positive"),
    )

    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False)
    event_sequence = Column(Integer, nullable=False)
    sequence_legacy_backfill = Column(Boolean, nullable=False, default=False, server_default="0")
    from_state = Column(String(32), nullable=False)
    to_state = Column(String(32), nullable=False)
    occurred_at = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)

    run = relationship("RunRow", backref="events")


@event.listens_for(RunEventRow.__table__, "after_create")
def _create_event_sequence_guard(target, connection, **kw) -> None:
    from sqlalchemy import text

    connection.execute(text(
        "CREATE TRIGGER trg_run_events_sequence_immutable "
        "BEFORE UPDATE OF run_id, event_sequence, sequence_legacy_backfill ON run_events "
        "WHEN NEW.run_id IS NOT OLD.run_id OR NEW.event_sequence IS NOT OLD.event_sequence "
        "OR NEW.sequence_legacy_backfill IS NOT OLD.sequence_legacy_backfill "
        "BEGIN SELECT RAISE(ABORT, 'Run event ordering metadata is immutable'); END"
    ))


class ArtifactRow(Base):
    __tablename__ = "artifacts"

    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    artifact_type = Column(String(32), nullable=False)
    mime_type = Column(String(128), nullable=False)
    source_type = Column(String(64), nullable=False)
    storage_ref = Column(String(512), nullable=False)
    sha256 = Column(String(64), nullable=False)
    size = Column(Integer, nullable=False, default=0)
    task_id = Column(String(64), nullable=True)
    run_id = Column(String(64), nullable=True)

    project = relationship("ProjectRow", backref="artifacts")


class FindingRow(Base):
    __tablename__ = "findings"

    id = Column(String(64), primary_key=True)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    run_id = Column(String(64), nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(32), nullable=False)
    evidence_refs = Column(Text, nullable=False, default="[]")
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime, nullable=False)

    task = relationship("TaskRow", backref="findings")


class EvidenceRow(Base):
    __tablename__ = "evidence"

    id = Column(String(64), primary_key=True)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    run_id = Column(String(64), nullable=False)
    actor_id = Column(String(64), nullable=False)
    source = Column(String(256), nullable=False)
    type = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)
    artifact_refs = Column(Text, nullable=False, default="[]")
    metadata_json = Column(Text, nullable=False, default="{}")
    observed_at = Column(DateTime, nullable=False)

    task = relationship("TaskRow", backref="evidence")


class RunBindingSnapshotRow(Base):
    """Run-owned immutable RuntimeBindingSnapshot (ADR-011 / PRE-WP14-B).

    - run_id is the primary key AND a foreign key to runs.id (1:1, no cascade).
    - Rows are never updated or deleted through the ORM: both operations are
      rejected fail-closed by the mapper-level listeners below.
    - No raw credential value is ever stored in any column.
    """

    __tablename__ = "run_binding_snapshots"

    run_id = Column(String(64), ForeignKey("runs.id"), primary_key=True)
    provider_id = Column(String(64), nullable=False)
    transport_kind = Column(String(32), nullable=False)
    runtime_id = Column(String(64), nullable=False)
    adapter_id = Column(String(64), nullable=False)
    execution_target = Column(String(32), nullable=False)
    runtime_profile_ref = Column(String(64), nullable=True)
    profile_revision = Column(Integer, nullable=True)
    adapter_version = Column(String(64), nullable=True)
    resolved_at = Column(DateTime, nullable=False)
    legacy_backfill = Column(Boolean, nullable=False, default=False)
    snapshot_schema_version = Column(Integer, nullable=False)
    auth_ownership = Column(String(32), nullable=False)
    secret_ref_id = Column(String(64), nullable=True)
    usage_visibility = Column(String(32), nullable=False)


@event.listens_for(RunBindingSnapshotRow, "before_update")
def _reject_snapshot_row_update(mapper, connection, target) -> None:
    raise RuntimeBindingError(
        "RuntimeBindingSnapshot rows are immutable: ORM update rejected"
    )


@event.listens_for(RunBindingSnapshotRow, "before_delete")
def _reject_snapshot_row_delete(mapper, connection, target) -> None:
    raise RuntimeBindingError(
        "RuntimeBindingSnapshot rows are immutable: ORM delete rejected"
    )


# Database-level guard: SQLite triggers reject UPDATE/DELETE even when they
# bypass the ORM (bulk Query.update()/delete(), raw SQL). This is the
# equivalent-strength transaction guard required by the PRE-WP14-B gate.
_REJECT_UPDATE_TRIGGER = (
    "CREATE TRIGGER IF NOT EXISTS trg_rbs_reject_update "
    "BEFORE UPDATE ON run_binding_snapshots "
    "BEGIN SELECT RAISE(ABORT, "
    "'RuntimeBindingSnapshot rows are immutable'); END"
)
_REJECT_DELETE_TRIGGER = (
    "CREATE TRIGGER IF NOT EXISTS trg_rbs_reject_delete "
    "BEFORE DELETE ON run_binding_snapshots "
    "BEGIN SELECT RAISE(ABORT, "
    "'RuntimeBindingSnapshot rows are immutable'); END"
)

# Run deletion is fail-closed at the database level: a Run owns its binding
# snapshot 1:1 forever, so deleting the Run row (which would orphan or
# require cascading the immutable snapshot) is rejected outright — for ORM
# deletes, bulk ORM deletes, and raw SQL alike — regardless of whether FK
# enforcement is enabled in the connection.
_RUN_DELETE_GUARD_TRIGGER = (
    "CREATE TRIGGER IF NOT EXISTS trg_runs_reject_delete "
    "BEFORE DELETE ON runs "
    "BEGIN SELECT RAISE(ABORT, "
    "'Run rows are protected: run deletion is not permitted'); END"
)


@event.listens_for(RunBindingSnapshotRow.__table__, "after_create")
def _create_snapshot_immutability_triggers(target, connection, **kw) -> None:
    from sqlalchemy import text as _text

    connection.execute(_text(_REJECT_UPDATE_TRIGGER))
    connection.execute(_text(_REJECT_DELETE_TRIGGER))


@event.listens_for(RunRow.__table__, "after_create")
def _create_run_delete_guard_trigger(target, connection, **kw) -> None:
    from sqlalchemy import text as _text

    connection.execute(_text(_RUN_DELETE_GUARD_TRIGGER))


def _serialize_tuple(value: tuple) -> str:
    return json.dumps(list(value))


def _deserialize_tuple(value: str) -> tuple:
    return tuple(json.loads(value))


def _serialize_dict(value: dict) -> str:
    return json.dumps(value)


def _deserialize_dict(value: str) -> dict:
    return json.loads(value)
