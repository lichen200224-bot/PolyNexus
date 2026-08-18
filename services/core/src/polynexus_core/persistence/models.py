from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


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

    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False)
    from_state = Column(String(32), nullable=False)
    to_state = Column(String(32), nullable=False)
    occurred_at = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)

    run = relationship("RunRow", backref="events")


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


def _serialize_tuple(value: tuple) -> str:
    return json.dumps(list(value))


def _deserialize_tuple(value: str) -> tuple:
    return tuple(json.loads(value))


def _serialize_dict(value: dict) -> str:
    return json.dumps(value)


def _deserialize_dict(value: str) -> dict:
    return json.loads(value)
