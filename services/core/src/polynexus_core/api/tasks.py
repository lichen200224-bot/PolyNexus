"""Task API endpoints — persistence-backed CRUD via Repository boundary."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from polynexus_core.api.dependencies import AuthLoopback, DbSession
from polynexus_core.api.schemas import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
)
from polynexus_core.domain.enums import WorkMode
from polynexus_core.domain.models import Task
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlProjectRepository,
    SqlTaskRepository,
)

router = APIRouter(tags=["tasks"])


def _task_to_response(t: Task) -> TaskResponse:
    return TaskResponse(
        id=t.id,
        project_id=t.project_id,
        title=t.title,
        workflow_id=t.workflow_id,
        workflow_version=t.workflow_version,
        mode=t.mode.value,
        context_package_id=t.context_package_id,
        created_at=t.created_at,
    )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    project_id: str,
    body: TaskCreate,
    _auth: AuthLoopback,
    db: DbSession,
) -> TaskResponse:
    # Validate parent project exists
    project_repo = SqlProjectRepository(db)
    if project_repo.get(project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Validate context_package_id if provided
    if body.context_package_id:
        cp_repo = SqlContextPackageRepository(db)
        cp = cp_repo.get(body.context_package_id)
        if cp is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"ContextPackage {body.context_package_id} not found",
            )
        if cp.project_id != project_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="ContextPackage does not belong to this project",
            )

    # Parse mode
    mode = WorkMode.REVIEW
    if body.mode:
        try:
            mode = WorkMode(body.mode)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid mode: {body.mode}. Must be one of: DISCUSS, REVIEW, VALIDATE",
            )

    task = Task(
        project_id=project_id,
        title=body.title,
        workflow_id=body.workflow_id,
        workflow_version=body.workflow_version,
        mode=mode,
        context_package_id=body.context_package_id,
    )
    task_repo = SqlTaskRepository(db)
    task_repo.add(task)
    db.commit()
    return _task_to_response(task)


@router.get(
    "/projects/{project_id}/tasks",
    response_model=TaskListResponse,
)
def list_tasks(
    project_id: str,
    _auth: AuthLoopback,
    db: DbSession,
) -> TaskListResponse:
    # Validate parent project exists
    project_repo = SqlProjectRepository(db)
    if project_repo.get(project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    task_repo = SqlTaskRepository(db)
    tasks = task_repo.list_by_project(project_id)
    return TaskListResponse(tasks=[_task_to_response(t) for t in tasks])


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    _auth: AuthLoopback,
    db: DbSession,
) -> TaskResponse:
    task_repo = SqlTaskRepository(db)
    task = task_repo.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return _task_to_response(task)
