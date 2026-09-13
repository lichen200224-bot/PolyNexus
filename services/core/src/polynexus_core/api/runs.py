"""Run API endpoints — persistence-backed CRUD and execution via Repository boundary.

Run creation only persists a CREATED record; it does NOT start the runtime,
RunSupervisor, or RuntimeAdapter.  The execute command triggers the full
lifecycle on an existing persisted Run.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from polynexus_core.api.dependencies import AuthLoopback, DbSession
from polynexus_core.errors import (
    ClaimConflictError,
    ContractViolationError,
    ResourceNotFoundError,
    RunNotFoundError,
)
from polynexus_core.api.schemas import (
    RunCreate,
    RunStart,
    RunCancel,
    RunEventResponse,
    RunListResponse,
    RunResponse,
    RunResultResponse,
)
from polynexus_core.domain.generation import GenerationConflict
from polynexus_core.storage.content import ContentError
from polynexus_core.persistence.generation import GenerationRepository
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
        generation_binding_status="LEGACY_UNBOUND_UNVERIFIED" if r.generation_revision is None else "EXPLICIT_GENERATION",
        generation_revision=r.generation_revision,
        generation_parent_run_id=r.generation_parent_run_id,
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

    # Authentication identifies the local controller, never a body-provided Human.
    try:
        run=GenerationRepository(db).create_run(principal="loopback-controller",command_id=body.command_id,task_id=task_id,revision=body.generation_revision,context_package_id=body.context_package_id,expected_control=body.expected_control_revision)
        db.commit()
    except (GenerationConflict,ContentError) as error:
        db.rollback()
        raise HTTPException(409,str(error)) from None
    run_repo = SqlRunRepository(db)

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
    limit: int | None = Query(default=None,ge=1,le=200),
    cursor: str | None = Query(default=None,max_length=2048),
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
    from polynexus_core.api.schemas import paginate
    if limit is None and cursor is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(content={"runs":[_run_to_response(r).model_dump(mode="json") for r in runs]})
    runs=sorted(runs,key=lambda r:(r.created_at,r.id))
    page,next_cursor=paginate(runs,"task_runs:"+task_id,limit,cursor)
    return RunListResponse(runs=[_run_to_response(r) for r in page],next_cursor=next_cursor)


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
    body: RunStart | None = None,
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

    # Bound command identity is checked even when replay now observes terminal state.
    if body is not None and run.generation_revision is not None:
        try:
            replay=GenerationRepository(db).start_command(run,principal='loopback-controller',command_id=body.command_id,revision=body.generation_revision,expected_control=body.expected_control_revision)
        except GenerationConflict as error:
            db.rollback();raise HTTPException(409,str(error)) from None
        if replay is not None:
            return JSONResponse(status_code=200 if run.state in _TERMINAL_STATES else 202,content=_run_to_response(run).model_dump(mode='json'))

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

    # Preserve malformed legacy-reference diagnostics without granting launch.
    stored_task=SqlTaskRepository(db).get(run.task_id)
    stored_context=SqlContextPackageRepository(db).get(run.context_package_id)
    if stored_task is None or stored_context is None:
        raise HTTPException(422,'stored_resource_not_found')
    if stored_task.project_id!=stored_context.project_id or run.workflow_id!=stored_task.workflow_id or run.workflow_version!=stored_task.workflow_version:
        raise HTTPException(422,'stored_run_contract_mismatch')
    if body is None or body.generation_revision!=run.generation_revision:
        raise HTTPException(409,'exact_generation_required')
    generations=GenerationRepository(db)
    from polynexus_core.domain.generation import WorkGenerationRef
    ref=WorkGenerationRef(run.task_id,body.generation_revision)
    current=generations.get(ref)
    if current['control_revision']!=body.expected_control_revision:
        raise HTTPException(409,'generation_control_conflict')
    service = ExecutionService(db)
    try:
        generations.start_command(run,principal='loopback-controller',command_id=body.command_id,revision=body.generation_revision,expected_control=body.expected_control_revision,record=True)
        execution = await service.execute_existing_run(run_id)
    except (GenerationConflict,ContentError) as exc:
        db.rollback()
        raise HTTPException(409,str(exc)) from None
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


@router.post('/runs/{run_id}/cancel')
async def cancel_run(run_id:str,body:RunCancel,_auth:AuthLoopback,db:DbSession):
    from polynexus_core.domain.generation import WorkGenerationRef
    from polynexus_core.workspace.ownership import active_operations
    run=SqlRunRepository(db).get(run_id)
    if run is None:raise HTTPException(404,'run_not_found')
    generations=GenerationRepository(db)
    try:
        result,is_new=generations.cancel_run(run,principal='loopback-controller',command_id=body.command_id,revision=body.generation_revision,expected_control=body.expected_control_revision,expected_fence=body.expected_fence)
        db.commit()
    except GenerationConflict as error:
        db.rollback();raise HTTPException(409,str(error)) from None
    if is_new and result['cancel_requested'] and run.state not in _TERMINAL_STATES:
        ref=WorkGenerationRef(run.task_id,run.generation_revision)
        if not active_operations.request_cancel_run(ref,run.id):
            # Restart or an unregistered handle cannot establish cleanup proof.
            generations.mark_unknown(run,'active_operation_handle_unavailable');db.commit()
    return result
