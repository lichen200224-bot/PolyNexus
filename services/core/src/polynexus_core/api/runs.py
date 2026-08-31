"""Run API endpoints — persistence-backed CRUD and execution via Repository boundary.

Run creation only persists a CREATED record; it does NOT start the runtime,
RunSupervisor, or RuntimeAdapter.  The execute command triggers the full
lifecycle on an existing persisted Run.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from polynexus_core.api.dependencies import AuthLoopback, DbSession
from polynexus_core.errors import (
    ClaimConflictError,
    ContractViolationError,
    ResourceNotFoundError,
    RunNotFoundError,
)
from polynexus_core.api.schemas import (
    RunCreate,
    RunEventResponse,
    RunListResponse,
    RunResponse,
    RunResultResponse,
)
from polynexus_core.domain.enums import RunState
from polynexus_core.domain.models import Run
from polynexus_core.execution_service import ExecutionService
from polynexus_core.runtime.redaction import redact_text
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
            reason=(redact_text(e.reason) if e.reason is not None else None),
        )
        for e in r.events
    ]
    result = None
    if r.result:
        result = RunResultResponse(
            run_id=r.result.run_id,
            status=r.result.status.value,
            summary=redact_text(r.result.summary),
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
        runtime_ref=(redact_text(r.runtime_ref, max_length=1024) if r.runtime_ref is not None else None),
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


# ---------------------------------------------------------------------------
# Execute — POST /runs/{run_id}/execute
# ---------------------------------------------------------------------------

# Terminal states that return 200 (immutable, do not restart)
_TERMINAL_STATES = {
    RunState.COMPLETED,
    RunState.FAILED,
    RunState.TIMED_OUT,
    RunState.CANCELLED,
    RunState.ORPHANED,
}

# Active states that return 202 idempotently (no duplicate runtime)
_ACTIVE_STATES = {RunState.STARTING, RunState.RUNNING}


@router.post(
    "/runs/{run_id}/execute",
    response_model=RunResponse,
)
async def execute_run(
    run_id: str,
    _auth: AuthLoopback,
    db: DbSession,
) -> RunResponse:
    """Execute an existing persisted Run through the full lifecycle.

    Idempotency matrix:
      - CREATED: accept once via CAS claim, return 202
      - STARTING/RUNNING: return 202, no duplicate runtime
      - COMPLETED/FAILED/TIMED_OUT/CANCELLED/ORPHANED: return 200
      - CANCEL_REQUESTED: return 409
    """
    from fastapi.responses import JSONResponse

    run_repo = SqlRunRepository(db)
    run = run_repo.get(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )

    # Lifecycle guard — CANCEL_REQUESTED
    if run.state is RunState.CANCEL_REQUESTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Run {run_id} is in CANCEL_REQUESTED state",
        )

    # Terminal states — return current Run with 200
    if run.state in _TERMINAL_STATES:
        return _run_to_response(run)

    # Active states — return current Run with 202, no duplicate runtime
    if run.state in _ACTIVE_STATES:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=_run_to_response(run).model_dump(mode="json"),
        )

    # CREATED — execute the Run via CAS claim
    assert run.state is RunState.CREATED, f"Unexpected state: {run.state}"

    service = ExecutionService(db)
    try:
        execution = await service.execute_existing_run(run_id)
    except RunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=redact_text(str(exc), fallback="Run not found"),
        )
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=redact_text(str(exc), fallback="Stored resource not found"),
        )
    except ContractViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=redact_text(str(exc), fallback="Run contract violation"),
        )
    except ClaimConflictError as exc:
        # Reload to determine current state for idempotent response
        run = run_repo.get(run_id)
        if run is not None and run.state in _TERMINAL_STATES:
            return _run_to_response(run)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=(
                _run_to_response(run).model_dump(mode="json")
                if run
                else {"detail": redact_text(str(exc), fallback="Run claim conflict")}
            ),
        )

    # Reload from DB to ensure persisted state
    run = run_repo.get(run_id)
    assert run is not None

    # First execution of a CREATED Run returns 202 per contract
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=_run_to_response(run).model_dump(mode="json"),
    )
