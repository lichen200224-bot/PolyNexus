"""Run API endpoints — persistence-backed CRUD via Repository boundary.

Run creation only persists a CREATED record; it does NOT start the runtime,
RunSupervisor, or RuntimeAdapter.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from polynexus_core.api.dependencies import AuthLoopback, DbSession
from polynexus_core.api.schemas import (
    RunCreate,
    RunEventResponse,
    RunListResponse,
    RunResponse,
    RunResultResponse,
)
from polynexus_core.domain.models import Run
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlRunRepository,
    SqlTaskRepository,
)

router = APIRouter(tags=["runs"])


def _run_to_response(r: Run) -> RunResponse:
    events = [
        RunEventResponse(
            id=e.id,
            run_id=e.run_id,
            from_state=e.from_state.value,
            to_state=e.to_state.value,
            occurred_at=e.occurred_at,
            reason=e.reason,
        )
        for e in r.events
    ]
    result = None
    if r.result:
        result = RunResultResponse(
            run_id=r.result.run_id,
            status=r.result.status.value,
            summary=r.result.summary,
            finding_ids=r.result.finding_ids,
            evidence_ids=r.result.evidence_ids,
            artifact_ids=r.result.artifact_ids,
        )
    return RunResponse(
        id=r.id,
        task_id=r.task_id,
        workflow_id=r.workflow_id,
        workflow_version=r.workflow_version,
        context_package_id=r.context_package_id,
        execution_target=r.execution_target.value,
        resume_mode=r.resume_mode.value,
        state=r.state.value,
        runtime_ref=r.runtime_ref,
        created_at=r.created_at,
        updated_at=r.updated_at,
        events=events,
        result=result,
    )


@router.post(
    "/tasks/{task_id}/runs",
    response_model=RunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_run(
    task_id: str,
    body: RunCreate,
    _auth: AuthLoopback,
    db: DbSession,
) -> RunResponse:
    # Validate task exists
    task_repo = SqlTaskRepository(db)
    task = task_repo.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    # Validate context package exists and belongs to same project
    cp_repo = SqlContextPackageRepository(db)
    cp = cp_repo.get(body.context_package_id)
    if cp is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"ContextPackage {body.context_package_id} not found",
        )
    if cp.project_id != task.project_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ContextPackage does not belong to the same project as the task",
        )

    # Create Run in CREATED state — no runtime execution
    run = Run(
        task_id=task_id,
        workflow_id=task.workflow_id,
        workflow_version=task.workflow_version,
        context_package_id=body.context_package_id,
    )
    run_repo = SqlRunRepository(db)
    run_repo.add(run)
    db.commit()

    # Reload from DB to ensure persistence and event hydration
    run = run_repo.get(run.id)
    assert run is not None
    return _run_to_response(run)


@router.get(
    "/tasks/{task_id}/runs",
    response_model=RunListResponse,
)
def list_runs(
    task_id: str,
    _auth: AuthLoopback,
    db: DbSession,
) -> RunListResponse:
    # Validate task exists
    task_repo = SqlTaskRepository(db)
    if task_repo.get(task_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    run_repo = SqlRunRepository(db)
    runs = run_repo.list_by_task(task_id)
    return RunListResponse(runs=[_run_to_response(r) for r in runs])


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(
    run_id: str,
    _auth: AuthLoopback,
    db: DbSession,
) -> RunResponse:
    run_repo = SqlRunRepository(db)
    run = run_repo.get(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )
    return _run_to_response(run)
