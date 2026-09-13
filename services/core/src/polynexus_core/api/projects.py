"""Project API endpoints — persistence-backed CRUD via Repository boundary."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from polynexus_core.api.dependencies import AuthLoopback, DbSession
from polynexus_core.api.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
)
from polynexus_core.domain.models import Project
from polynexus_core.persistence.repository import SqlProjectRepository

router = APIRouter(tags=["projects"])


def _project_to_response(p: Project) -> ProjectResponse:
    return ProjectResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        created_at=p.created_at,
        classification=p.classification,
        archived=p.archived,
    )


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    body: ProjectCreate,
    _auth: AuthLoopback,
    db: DbSession,
) -> ProjectResponse:
    repo = SqlProjectRepository(db)
    project = Project(name=body.name, description=body.description, classification=body.classification)
    repo.add(project)
    db.commit()
    return _project_to_response(project)


@router.get("/projects", response_model=ProjectListResponse)
def list_projects(
    _auth: AuthLoopback,
    db: DbSession,
) -> ProjectListResponse:
    repo = SqlProjectRepository(db)
    projects = repo.list_all()
    return ProjectListResponse(projects=[_project_to_response(p) for p in projects])


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    _auth: AuthLoopback,
    db: DbSession,
) -> ProjectResponse:
    repo = SqlProjectRepository(db)
    project = repo.get(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return _project_to_response(project)


@router.post("/projects/{project_id}/archive", response_model=ProjectResponse)
def archive_project(project_id: str, _auth: AuthLoopback, db: DbSession) -> ProjectResponse:
    project = SqlProjectRepository(db).archive(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    db.commit()
    return _project_to_response(project)
