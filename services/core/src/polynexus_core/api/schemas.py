"""Pydantic request/response schemas for Project, Task, Run, ContextPackage API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Project name (non-empty)")
    description: str | None = Field(None, description="Optional project description")

    @field_validator("name")
    @classmethod
    def name_not_whitespace_only(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project name must not be whitespace-only")
        return v


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Task title (non-empty)")
    workflow_id: str = Field(..., min_length=1, description="Workflow definition ID")
    workflow_version: int = Field(..., ge=1, description="Workflow version (>= 1)")
    mode: str | None = Field(None, description="Work mode: DISCUSS, REVIEW, or VALIDATE")
    context_package_id: str | None = Field(None, description="Optional ContextPackage ID")

    @field_validator("title")
    @classmethod
    def title_not_whitespace_only(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Task title must not be whitespace-only")
        return v


class TaskResponse(BaseModel):
    id: str
    project_id: str
    title: str
    workflow_id: str
    workflow_version: int
    mode: str
    context_package_id: str | None
    created_at: datetime


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

class RunCreate(BaseModel):
    context_package_id: str = Field(..., min_length=1, description="ContextPackage ID to associate with this run")


class RunEventResponse(BaseModel):
    id: str
    run_id: str
    from_state: str
    to_state: str
    occurred_at: datetime
    reason: str | None


class RunResultResponse(BaseModel):
    run_id: str
    status: str
    summary: str
    finding_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    artifact_ids: tuple[str, ...]


class RunResponse(BaseModel):
    id: str
    task_id: str
    workflow_id: str
    workflow_version: int
    context_package_id: str
    execution_target: str
    resume_mode: str
    state: str
    runtime_ref: str | None
    created_at: datetime
    updated_at: datetime
    events: list[RunEventResponse]
    result: RunResultResponse | None


class RunListResponse(BaseModel):
    runs: list[RunResponse]


# ---------------------------------------------------------------------------
# ContextPackage
# ---------------------------------------------------------------------------

class ContextPackageCreate(BaseModel):
    version: int = Field(..., ge=1, description="Version number (>= 1)")
    instructions: tuple[str, ...] = Field(default=(), description="Review instructions")
    constraints: tuple[str, ...] = Field(default=(), description="Constraints")
    project_facts: dict[str, str] = Field(default_factory=dict, description="Project facts")
    artifact_refs: tuple[str, ...] = Field(default=(), description="Artifact references")
    prior_decision_refs: tuple[str, ...] = Field(default=(), description="Prior decision references")
    memory_refs: tuple[str, ...] = Field(default=(), description="Memory references")
    source_refs: tuple[str, ...] = Field(default=(), description="Source references")


class ContextPackageResponse(BaseModel):
    id: str
    project_id: str
    version: int
    instructions: tuple[str, ...]
    constraints: tuple[str, ...]
    project_facts: dict[str, str]
    artifact_refs: tuple[str, ...]
    prior_decision_refs: tuple[str, ...]
    memory_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    created_at: datetime
