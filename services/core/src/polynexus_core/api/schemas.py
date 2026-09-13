"""Pydantic request/response schemas for Project, Task, Run, ContextPackage API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"] = "INTERNAL"
    name: str = Field(..., min_length=1, description="Project name (non-empty)")
    description: str | None = Field(None, description="Optional project description")

    @field_validator("name")
    @classmethod
    def name_not_whitespace_only(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Project name must not be whitespace-only")
        return v


class ProjectResponse(BaseModel):
    classification: str = "INTERNAL"
    archived: bool = False
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
    classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"] = "INTERNAL"
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
    classification: str = "INTERNAL"
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
    model_config = {"extra":"forbid"}
    generation_revision: int = Field(ge=1)
    expected_control_revision: int = Field(ge=0)
    command_id: str = Field(min_length=1,max_length=128)
    context_package_id: str = Field(..., min_length=1, description="ContextPackage ID to associate with this run")


class RunStart(BaseModel):
    model_config={"extra":"forbid"}
    generation_revision:int=Field(ge=1)
    expected_control_revision:int=Field(ge=0)
    command_id:str=Field(min_length=1,max_length=128)


class RunCancel(RunStart):
    expected_fence:int=Field(ge=0)


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
    generation_binding_status: str = "LEGACY_UNBOUND_UNVERIFIED"
    generation_revision: int | None = None
    generation_parent_run_id: str | None = None
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
    next_cursor: str | None = None
    runs: list[RunResponse]


# ---------------------------------------------------------------------------
# ContextPackage
# ---------------------------------------------------------------------------

class ContextPackageCreate(BaseModel):
    classification: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"] = "INTERNAL"
    version: int = Field(..., ge=1, description="Version number (>= 1)")
    instructions: tuple[str, ...] = Field(default=(), description="Review instructions")
    constraints: tuple[str, ...] = Field(default=(), description="Constraints")
    project_facts: dict[str, str] = Field(default_factory=dict, description="Project facts")
    artifact_refs: tuple[str, ...] = Field(default=(), description="Artifact references")
    prior_decision_refs: tuple[str, ...] = Field(default=(), description="Prior decision references")
    memory_refs: tuple[str, ...] = Field(default=(), description="Memory references")
    source_refs: tuple[str, ...] = Field(default=(), description="Source references")


class ContextPackageResponse(BaseModel):
    classification: str = "INTERNAL"
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


# ---------------------------------------------------------------------------
# Finding / Evidence / Artifact — read-only query responses (WP-09C)
# ---------------------------------------------------------------------------

class FindingResponse(BaseModel):
    id: str
    task_id: str
    run_id: str
    title: str
    description: str
    severity: str
    evidence_refs: tuple[str, ...]
    status: str
    created_at: datetime


class EvidenceResponse(BaseModel):
    id: str
    task_id: str
    run_id: str
    actor_id: str
    source: str
    type: str
    status: str
    artifact_refs: tuple[str, ...]
    metadata: dict[str, str]
    observed_at: datetime


class ArtifactResponse(BaseModel):
    classification: str = "INTERNAL"
    id: str
    project_id: str
    task_id: str | None
    run_id: str | None
    artifact_type: str
    mime_type: str
    source_type: str
    storage_ref: str
    sha256: str
    size: int


# Wrappers — stable JSON, empty returns 200 with null/[]

class RunResultWrapper(BaseModel):
    result: RunResultResponse | None


class FindingsWrapper(BaseModel):
    findings: list[FindingResponse]


class EvidenceWrapper(BaseModel):
    evidence: list[EvidenceResponse]


class ArtifactsWrapper(BaseModel):
    artifacts: list[ArtifactResponse]


class HistoryWrapper(BaseModel):
    next_cursor: str | None = None
    events: list[RunEventResponse]


def encode_cursor(parts: list[str]) -> str:
    import base64, json
    return base64.urlsafe_b64encode(json.dumps(parts,separators=(',',':')).encode()).decode().rstrip('=')


def decode_cursor(value: str, scope: str, length: int) -> list[str]:
    import base64, json
    from fastapi import HTTPException
    try:
        if len(value)>2048: raise ValueError()
        parts=json.loads(base64.b64decode(value+'='*(-len(value)%4),altchars=b'-_',validate=True))
        if not isinstance(parts,list) or len(parts)!=length or not all(isinstance(p,str) for p in parts) or parts[0]!=scope or encode_cursor(parts)!=value: raise ValueError()
        return parts
    except (ValueError,TypeError,UnicodeError):
        raise HTTPException(422,'invalid_cursor') from None


def paginate(items, scope: str, limit: int | None, cursor: str | None):
    from fastapi import HTTPException
    if limit is None and cursor is None: return items,None
    size=limit or 100
    ids=[item.id for item in items]
    start=0;end=len(items)
    if cursor is not None:
        _,last,upper=decode_cursor(cursor,scope,3)
        if last not in ids or upper not in ids: raise HTTPException(422,'invalid_cursor')
        start=ids.index(last)+1;end=ids.index(upper)+1
        if start>end: raise HTTPException(422,'invalid_cursor')
    page=items[start:min(start+size,end)]
    next_cursor=encode_cursor([scope,page[-1].id,ids[end-1]]) if page and start+len(page)<end else None
    return page,next_cursor
