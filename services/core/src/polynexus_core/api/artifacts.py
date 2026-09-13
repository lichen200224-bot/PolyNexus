"""Core-owned immutable upload and verified read boundaries."""
from __future__ import annotations
import base64,binascii,os
from pathlib import Path
from typing import Literal
from fastapi import APIRouter,HTTPException,Response
from pydantic import BaseModel,Field
from polynexus_core.api.dependencies import AuthLoopback,DbSession
from polynexus_core.api.run_outputs import _artifact_to_response
from polynexus_core.domain.models import Artifact
from polynexus_core.domain.enums import ArtifactType
from polynexus_core.persistence.repository import SqlArtifactRepository,SqlProjectRepository
from polynexus_core.storage.content import ContentStore,ContentError,MAX_CONTENT_BYTES

router=APIRouter(tags=["artifacts"])

def content_store():
    value=os.environ.get("POLYNEXUS_CONTENT_ROOT")
    if not value:
        raise ContentError("content_store_not_configured")
    return ContentStore(Path(value))

class ArtifactUpload(BaseModel):
    model_config={"extra":"forbid"}
    content_base64:str=Field(max_length=((MAX_CONTENT_BYTES+2)//3)*4)
    mime_type:str=Field(default="application/octet-stream",max_length=128)
    classification:Literal["PUBLIC","INTERNAL","CONFIDENTIAL","RESTRICTED"]="INTERNAL"

@router.post("/projects/{project_id}/artifacts",status_code=201)
def upload_artifact(project_id:str,body:ArtifactUpload,_auth:AuthLoopback,db:DbSession):
    project=SqlProjectRepository(db).get(project_id)
    if project is None:raise HTTPException(404,"project_not_found")
    if project.archived:raise HTTPException(409,"project_archived")
    try:
        data=base64.b64decode(body.content_base64,validate=True)
        digest,size=content_store().put(data)
    except (ContentError,ValueError,binascii.Error) as error:
        raise HTTPException(422,"artifact_content_invalid") from None
    artifact=Artifact(project_id=project_id,artifact_type=ArtifactType.DOCUMENT,mime_type=body.mime_type,source_type="CORE_UPLOAD",storage_ref="core-blob:"+digest,sha256=digest,size=size,classification=body.classification)
    SqlArtifactRepository(db).add(artifact);db.commit()
    return _artifact_to_response(artifact)

@router.get("/projects/{project_id}/artifacts")
def list_artifacts(project_id:str,_auth:AuthLoopback,db:DbSession):
    if SqlProjectRepository(db).get(project_id) is None:raise HTTPException(404,"project_not_found")
    return {"artifacts":[_artifact_to_response(a) for a in SqlArtifactRepository(db).list_by_project(project_id)]}

@router.get("/artifacts/{artifact_id}/content")
def read_artifact(artifact_id:str,_auth:AuthLoopback,db:DbSession):
    artifact=SqlArtifactRepository(db).get(artifact_id)
    if artifact is None:raise HTTPException(404,"artifact_not_found")
    try:data=content_store().read_artifact(artifact)
    except ContentError as error:raise HTTPException(409,str(error)) from None
    # Download only: untrusted HTML/SVG is never executed inside the UI origin.
    return Response(data,media_type="application/octet-stream",headers={"Content-Disposition":"attachment", "X-Content-Type-Options":"nosniff", "Cache-Control":"no-store"})

@router.delete("/artifacts/{artifact_id}")
def retain_artifact(artifact_id:str,_auth:AuthLoopback,db:DbSession):
    if SqlArtifactRepository(db).get(artifact_id) is None:raise HTTPException(404,"artifact_not_found")
    raise HTTPException(409,"artifact_retention_protected")
