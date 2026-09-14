"""ContextPackage API endpoints — persistence-backed create via Repository boundary."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError
from polynexus_core.api.artifacts import content_store
from polynexus_core.storage.content import ContentError
from polynexus_core.persistence.repository import SqlArtifactRepository

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
        classification=cp.classification,
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

    if not project_repo.reserve_write(project_id):
        raise HTTPException(409,"project_archived")

    # D1b execution plans are Core-issued only.  A caller-provided context
    # fact must never be promoted into trusted verification instructions.
    if "d1b_execution_plan_json" in body.project_facts:
        raise HTTPException(422, "reserved_runtime_plan_fact")

    # Artifact identity is Core-owned; raw source locators remain descriptive only.
    for reference in dict.fromkeys((*body.artifact_refs,*body.prior_decision_refs,*body.memory_refs)):
        artifact = SqlArtifactRepository(db).get(reference)
        if artifact is None or artifact.project_id != project_id:
            raise HTTPException(422, "context_artifact_scope_mismatch")
        try:
            content_store().read_artifact(artifact)
        except ContentError as error:
            raise HTTPException(422, str(error)) from None
    # Imported references carry content only, never Human decisions or trusted memory.
    if any(cp.version == body.version for cp in SqlContextPackageRepository(db).list_by_project(project_id)):
        raise HTTPException(409, "context_version_conflict")

    # Create ContextPackage domain object (validates version >= 1 in __post_init__)
    cp = ContextPackage(
        project_id=project_id,
        classification=body.classification,
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
    try:
        repo.add(cp)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "context_version_conflict") from None

    return _cp_to_response(cp)


@router.get("/projects/{project_id}/context-packages")
def list_context_packages(project_id: str, _auth: AuthLoopback, db: DbSession):
    if SqlProjectRepository(db).get(project_id) is None:
        raise HTTPException(404, "project_not_found")
    return {"context_packages": [_cp_to_response(cp) for cp in SqlContextPackageRepository(db).list_by_project(project_id)]}


@router.get("/context-packages/{context_id}", response_model=ContextPackageResponse)
def get_context_package(context_id: str, _auth: AuthLoopback, db: DbSession):
    cp = SqlContextPackageRepository(db).get(context_id)
    if cp is None:
        raise HTTPException(404, "context_not_found")
    return _cp_to_response(cp)
