"""Run output query endpoints — read-only, run-scoped, via Repository boundary."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from polynexus_core.api.dependencies import AuthLoopback, DbSession
from polynexus_core.api.schemas import (
    ArtifactResponse,
    ArtifactsWrapper,
    EvidenceResponse,
    EvidenceWrapper,
    FindingResponse,
    FindingsWrapper,
    HistoryWrapper,
    RunEventResponse,
    RunResultResponse,
    RunResultWrapper,
)
from polynexus_core.persistence.repository import (
    SqlArtifactRepository,
    SqlEvidenceRepository,
    SqlFindingRepository,
    SqlRunEventRepository,
    SqlRunRepository,
    SqlTaskRepository,
)

router = APIRouter(tags=["run-outputs"])


def _load_run_and_task(db, run_id: str):
    run_repo = SqlRunRepository(db)
    run = run_repo.get(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found")
    task_repo = SqlTaskRepository(db)
    task = task_repo.get(run.task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Stored Task {run.task_id} not found")
    return run, task


def _finding_to_response(f) -> FindingResponse:
    return FindingResponse(
        id=f.id, task_id=f.task_id, run_id=f.run_id, title=f.title,
        description=f.description, severity=f.severity.value,
        evidence_refs=f.evidence_refs, status=f.status.value, created_at=f.created_at,
    )


def _evidence_to_response(ev) -> EvidenceResponse:
    return EvidenceResponse(
        id=ev.id, task_id=ev.task_id, run_id=ev.run_id, actor_id=ev.actor_id,
        source=ev.source, type=ev.type.value, status=ev.status.value,
        artifact_refs=ev.artifact_refs, metadata=dict(ev.metadata), observed_at=ev.observed_at,
    )


def _artifact_to_response(a) -> ArtifactResponse:
    return ArtifactResponse(
        id=a.id, project_id=a.project_id, task_id=a.task_id, run_id=a.run_id,
        artifact_type=a.artifact_type.value, mime_type=a.mime_type,
        source_type=a.source_type, storage_ref=a.storage_ref, sha256=a.sha256, size=a.size,
    )


def _event_to_response(e) -> RunEventResponse:
    return RunEventResponse(
        id=e.id, run_id=e.run_id, from_state=e.from_state.value, to_state=e.to_state.value,
        occurred_at=e.occurred_at, reason=e.reason,
    )


@router.get("/runs/{run_id}/result", response_model=RunResultWrapper)
def get_run_result(run_id: str, _auth: AuthLoopback, db: DbSession) -> RunResultWrapper:
    run, task = _load_run_and_task(db, run_id)
    if run.result is None:
        return RunResultWrapper(result=None)
    # Validate every referenced ID resolves and satisfies ownership
    finding_repo = SqlFindingRepository(db)
    evidence_repo = SqlEvidenceRepository(db)
    artifact_repo = SqlArtifactRepository(db)
    for fid in run.result.finding_ids:
        f = finding_repo.get(fid)
        if f is None or f.run_id != run.id or f.task_id != run.task_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid Finding reference {fid}")
    for eid in run.result.evidence_ids:
        ev = evidence_repo.get(eid)
        if ev is None or ev.run_id != run.id or ev.task_id != run.task_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid Evidence reference {eid}")
    for aid in run.result.artifact_ids:
        a = artifact_repo.get(aid)
        if a is None or a.run_id != run.id or a.task_id != run.task_id or a.project_id != task.project_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid Artifact reference {aid}")
    result = RunResultResponse(
        run_id=run.result.run_id, status=run.result.status.value, summary=run.result.summary,
        finding_ids=run.result.finding_ids, evidence_ids=run.result.evidence_ids, artifact_ids=run.result.artifact_ids,
    )
    return RunResultWrapper(result=result)


@router.get("/runs/{run_id}/findings", response_model=FindingsWrapper)
def get_run_findings(run_id: str, _auth: AuthLoopback, db: DbSession) -> FindingsWrapper:
    run, _ = _load_run_and_task(db, run_id)
    repo = SqlFindingRepository(db)
    findings = repo.list_by_run(run_id)
    for f in findings:
        if f.run_id != run.id or f.task_id != run.task_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Cross-owned Finding {f.id}")
    return FindingsWrapper(findings=[_finding_to_response(f) for f in findings])


@router.get("/runs/{run_id}/evidence", response_model=EvidenceWrapper)
def get_run_evidence(run_id: str, _auth: AuthLoopback, db: DbSession) -> EvidenceWrapper:
    run, _ = _load_run_and_task(db, run_id)
    repo = SqlEvidenceRepository(db)
    evidence = repo.list_by_run(run_id)
    for ev in evidence:
        if ev.run_id != run.id or ev.task_id != run.task_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Cross-owned Evidence {ev.id}")
    return EvidenceWrapper(evidence=[_evidence_to_response(ev) for ev in evidence])


@router.get("/runs/{run_id}/artifacts", response_model=ArtifactsWrapper)
def get_run_artifacts(run_id: str, _auth: AuthLoopback, db: DbSession) -> ArtifactsWrapper:
    run, task = _load_run_and_task(db, run_id)
    repo = SqlArtifactRepository(db)
    artifacts = repo.list_by_run(run_id)
    for a in artifacts:
        if a.run_id != run.id or a.task_id != run.task_id or a.project_id != task.project_id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Cross-owned Artifact {a.id}")
    return ArtifactsWrapper(artifacts=[_artifact_to_response(a) for a in artifacts])


@router.get("/runs/{run_id}/history", response_model=HistoryWrapper)
def get_run_history(run_id: str, _auth: AuthLoopback, db: DbSession) -> HistoryWrapper:
    run, _ = _load_run_and_task(db, run_id)
    repo = SqlRunEventRepository(db)
    events = repo.list_by_run(run_id)
    for e in events:
        if e.run_id != run.id:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Cross-owned event {e.id}")
    return HistoryWrapper(events=[_event_to_response(e) for e in events])
