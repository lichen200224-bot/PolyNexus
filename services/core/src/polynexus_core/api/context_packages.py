"""ContextPackage API endpoints — persistence-backed create via Repository boundary."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from polynexus_core.api.dependencies import AuthLoopback, DbSession
from polynexus_core.api.schemas import (
    ContextPackageCreate,
    ContextPackageResponse,
)
from polynexus_core.domain.models import ContextPackage
from polynexus_core.persistence.repository import (
    SqlContextPackageRepository,
    SqlProjectRepository,
)

router = APIRouter(tags=["context-packages"])


def _cp_to_response(cp: ContextPackage) -> ContextPackageResponse:
    return ContextPackageResponse(
        id=cp.id,
        project_id=cp.project_id,
        version=cp.version,
        instructions=cp.instructions,
        constraints=cp.constraints,
        project_facts=dict(cp.project_facts),
        artifact_refs=cp.artifact_refs,
        prior_decision_refs=cp.prior_decision_refs,
        memory_refs=cp.memory_refs,
        source_refs=cp.source_refs,
        created_at=cp.created_at,
    )


@router.post(
    "/projects/{project_id}/context-packages",
    response_model=ContextPackageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_context_package(
    project_id: str,
    body: ContextPackageCreate,
    _auth: AuthLoopback,
    db: DbSession,
) -> ContextPackageResponse:
    # Validate project exists
    project_repo = SqlProjectRepository(db)
    if project_repo.get(project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Create ContextPackage domain object (validates version >= 1 in __post_init__)
    cp = ContextPackage(
        project_id=project_id,
        version=body.version,
        instructions=body.instructions,
        constraints=body.constraints,
        project_facts=body.project_facts,
        artifact_refs=body.artifact_refs,
        prior_decision_refs=body.prior_decision_refs,
        memory_refs=body.memory_refs,
        source_refs=body.source_refs,
    )

    # Persist via repository boundary (no direct ORM operations)
    repo = SqlContextPackageRepository(db)
    repo.add(cp)
    db.commit()

    return _cp_to_response(cp)
