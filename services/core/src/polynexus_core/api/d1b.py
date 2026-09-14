"""Strict Core routes for the D1b Candidate/evidence/Human/P0 boundary."""
from __future__ import annotations

import base64
import binascii
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from polynexus_core.api.artifacts import content_store
from polynexus_core.api.dependencies import AuthLoopback, DbSession
from polynexus_core.domain.d1b import (
    Applicability,
    AssuranceMode,
    EvidenceObservation,
    Requiredness,
    VerificationOutcome,
    Validity,
    capture_directory,
    capture_mapping,
)
from polynexus_core.persistence.d1b import (
    D1bPersistenceError,
    D1bRepository,
    HumanProtocolError,
    P0PackageError,
)
from polynexus_core.persistence.generation import GenerationRepository
from polynexus_core.storage.content import ContentError


router = APIRouter(tags=["d1b"])


class StrictBody(BaseModel):
    model_config = {"extra": "forbid", "populate_by_name": True}


class SnapshotBody(StrictBody):
    # Values are base64 of the exact Core-owned bytes.  The domain layer still
    # applies per-file size/path/collision rules after decoding.
    entries: dict[str, str] = Field(default_factory=dict, max_length=10000)
    source_ref: str | None = Field(default=None, max_length=512)


class CreateCandidateBody(StrictBody):
    baseline: SnapshotBody
    result: SnapshotBody
    requirements_snapshot_id: str
    validation_contract_snapshot_id: str
    # These two raw captures are accepted only by the explicit TEST fixture
    # route below; production publication uses persisted snapshot IDs.
    requirements: SnapshotBody | None = None
    validation_contract: SnapshotBody | None = None
    task_id: str | None = None
    generation_revision: int | None = Field(default=None, ge=0)
    run_id: str | None = None
    lineage_ref: str | None = Field(default=None, max_length=128)
    provenance: dict[str, Any] = Field(default_factory=dict)


class EvidenceBody(StrictBody):
    contract_id: str = Field(min_length=1, max_length=256)
    observations: list[dict[str, Any]] = Field(min_length=1, max_length=10000)


class AssuranceBody(StrictBody):
    mode: Literal["FLEXIBLE", "STANDARD", "VERIFIED"]
    target_type: str = Field(default="CANDIDATE", max_length=32)
    target_id: str | None = Field(default=None, max_length=80)
    profile_ref: str | None = Field(default=None, max_length=256)
    profile_revision: int | None = Field(default=None, ge=0)
    reason: str = Field(default="derived_from_current_evidence", min_length=1)


class SnapshotIdCandidateBody(StrictBody):
    baseline_snapshot_id: str
    result_snapshot_id: str
    requirements_snapshot_id: str
    validation_contract_snapshot_id: str
    run_id: str
    lineage_ref: str = Field(min_length=1, max_length=128)
    provenance: dict[str, Any] = Field(default_factory=dict)


class GenerationSnapshotBody(StrictBody):
    run_id: str = Field(min_length=1, max_length=128)
    kind: Literal["baseline", "result", "requirements", "validation"]


class GenerationVerificationBody(StrictBody):
    run_id: str = Field(min_length=1, max_length=128)


class CrossReviewVerificationBody(StrictBody):
    reviewer_run_id: str = Field(min_length=1, max_length=128)


class CrossReviewRunBody(StrictBody):
    target_run_id: str = Field(min_length=1, max_length=128)


class CrossReviewRunResponse(BaseModel):
    run_id: str
    task_id: str
    generation_revision: int
    generation_parent_run_id: str
    runtime_ref: str
    state: str


class WebAuthnResponseBody(StrictBody):
    client_data_json: str = Field(alias="clientDataJSON", min_length=1, max_length=180000)
    attestation_object: str | None = Field(default=None, alias="attestationObject", max_length=1400000)
    authenticator_data: str | None = Field(default=None, alias="authenticatorData", max_length=16000)
    signature: str | None = Field(default=None, max_length=4096)
    user_handle: str | None = Field(default=None, alias="userHandle", max_length=4096)


class WebAuthnCredentialBody(StrictBody):
    id: str = Field(min_length=1, max_length=4096)
    raw_id: str = Field(alias="rawId", min_length=1, max_length=4096)
    type: Literal["public-key"]
    response: WebAuthnResponseBody


class EnrollmentChallengeBody(StrictBody):
    ceremony: Literal["registration", "authentication", "revocation"]
    key_id: str | None = Field(default=None, min_length=1, max_length=80)
    session_id: str | None = Field(default=None, min_length=1, max_length=80)
    csrf_token: str | None = Field(default=None, min_length=1, max_length=4096)


class RegisterCredentialBody(StrictBody):
    challenge_id: str = Field(min_length=1, max_length=80)
    credential: WebAuthnCredentialBody


class RevokeCredentialBody(StrictBody):
    challenge_id: str = Field(min_length=1, max_length=80)
    key_id: str = Field(min_length=1, max_length=80)
    credential: WebAuthnCredentialBody


class PairingBody(StrictBody):
    principal_ref: str | None = Field(default=None, min_length=1, max_length=256)
    enrollment_proof: str | None = Field(default=None, min_length=1, max_length=4096)
    challenge_id: str | None = Field(default=None, min_length=1, max_length=80)
    credential: WebAuthnCredentialBody | None = None
    expires_at: datetime


class SessionBody(StrictBody):
    grant_id: str
    pairing_proof: str | None = Field(default=None, min_length=1, max_length=4096)
    pairing_token: str | None = Field(default=None, min_length=1, max_length=4096)
    audience: str = Field(min_length=1, max_length=64)
    csrf_token: str = Field(min_length=1, max_length=4096)
    expires_at: datetime | None = None


class SessionRevokeBody(StrictBody):
    csrf_token: str = Field(min_length=1, max_length=4096)


class ChallengeBody(StrictBody):
    session_id: str
    candidate_id: str
    action: Literal["Accept", "Reject", "Revoke", "Supersede"]
    replacement_acceptance_id: str | None = Field(default=None, max_length=80)
    policy_revision: int = Field(default=1, ge=0)
    expires_at: datetime | None = None


class DecisionBody(StrictBody):
    session_id: str
    challenge_id: str
    nonce: str = Field(min_length=1, max_length=4096)
    action: Literal["Accept", "Reject", "Revoke", "Supersede"]
    candidate_id: str
    view_digest: str
    csrf_token: str = Field(min_length=1, max_length=4096)
    origin: str = Field(min_length=1, max_length=512)
    command_id: str = Field(min_length=1, max_length=128)
    reason: str | None = Field(default=None, max_length=4096)
    policy_revision: int = Field(default=1, ge=0)
    replacement_acceptance_id: str | None = None


class OpenAcceptedBody(StrictBody):
    target_dir: str = Field(min_length=1, max_length=1024)
    owner_ref: str = Field(min_length=1, max_length=256)


class TakeoverBody(StrictBody):
    owner_ref: str = Field(min_length=1, max_length=256)


class ExportBody(StrictBody):
    package_path: str = Field(min_length=1, max_length=1024)


def _d1b_fixture_only() -> None:
    if (
        os.environ.get("POLYNEXUS_D1B_TEST_MODE") != "1"
        or os.environ.get("POLYNEXUS_ENVIRONMENT") != "TEST"
    ):
        raise HTTPException(status_code=403, detail="d1b_fixture_route_disabled")


def _human_protocol_enabled() -> None:
    """Enable A-LP only through an explicit local-personal deployment flag.

    The fixture switch remains available for deterministic tests.  Production
    local use requires the separate A-LP flag; the ordinary loopback token is
    never treated as a Human principal.
    """
    if (
        os.environ.get("POLYNEXUS_D1B_TEST_MODE") == "1"
        and os.environ.get("POLYNEXUS_ENVIRONMENT") == "TEST"
        and os.environ.get("POLYNEXUS_HUMAN_TEST_MODE") == "1"
    ):
        return
    if (
        os.environ.get("POLYNEXUS_HUMAN_A_LP_ENABLED") == "1"
        and os.environ.get("POLYNEXUS_ENVIRONMENT") == "LOCAL"
    ):
        return
    raise HTTPException(status_code=403, detail="human_protocol_disabled")


def _require_ui_origin(request: Request) -> str:
    origins = request.headers.getlist("origin")
    expected_origin = os.environ.get("POLYNEXUS_UI_ORIGIN", "")
    if len(origins) != 1 or not expected_origin or origins[0] != expected_origin:
        raise HTTPException(status_code=409, detail="origin_rejected")
    return origins[0]


def _require_local_human_origin(request: Request) -> None:
    if os.environ.get("POLYNEXUS_ENVIRONMENT") == "LOCAL":
        _require_ui_origin(request)


def _error(error: Exception, *, code: int = 409) -> HTTPException:
    if isinstance(error, (ContentError, D1bPersistenceError, HumanProtocolError, P0PackageError)):
        return HTTPException(status_code=code, detail=str(error))
    return HTTPException(status_code=422, detail="d1b_request_invalid")


def _decode_snapshot(body: SnapshotBody):
    values: dict[str, bytes] = {}
    for path, encoded in body.entries.items():
        try:
            values[path] = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            raise HTTPException(status_code=422, detail="snapshot_base64_invalid") from None
    return capture_mapping(values, source_ref=body.source_ref)


def _generation_snapshot(
    db,
    *,
    task_id: str,
    generation_revision: int,
    run_id: str,
    kind: str,
):
    """Observe a closed D1a writer and freeze a Core-owned W3 snapshot.

    The request carries only the exact generation/run and logical snapshot
    kind.  Core derives the source from the prepared input or its managed
    workspace; callers cannot provide an arbitrary path or manifest.
    """
    generation = db.execute(
        text(
            "SELECT inputs, aborted, closed, ownership_unknown "
            "FROM work_generations WHERE task_id=:task AND revision=:revision"
        ),
        {"task": task_id, "revision": generation_revision},
    ).mappings().one_or_none()
    if generation is None:
        raise D1bPersistenceError("generation_not_found")
    run = db.execute(
        text(
            "SELECT id, task_id, generation_revision, state "
            "FROM runs WHERE id=:run"
        ),
        {"run": run_id},
    ).mappings().one_or_none()
    if (
        run is None
        or run["task_id"] != task_id
        or run["generation_revision"] != generation_revision
        or run["state"] not in {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}
    ):
        raise D1bPersistenceError("generation_run_scope_invalid")
    claim = db.execute(
        text(
            "SELECT lineage, released FROM generation_writer_claims "
            "WHERE task_id=:task AND revision=:revision AND run_id=:run"
        ),
        {"task": task_id, "revision": generation_revision, "run": run_id},
    ).mappings().one_or_none()
    if claim is None or claim["released"] != 1:
        raise D1bPersistenceError("writer_not_quiescent")
    if generation["aborted"] or generation["ownership_unknown"] or not generation["closed"]:
        raise D1bPersistenceError("generation_not_quiescent")
    try:
        inputs = json.loads(generation["inputs"])
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise D1bPersistenceError("generation_inputs_invalid") from exc
    record = GenerationRepository(db).verify_inputs(task_id, inputs)
    store = content_store()
    source_ref = f"core:generation:{task_id}:{generation_revision}:{run_id}:{kind}"

    def read_entry(entry: dict[str, Any]) -> tuple[bytes, str]:
        blob = entry.get("blob")
        size = entry.get("size")
        path = entry.get("path")
        mode = entry.get("mode", "100644")
        if (
            not isinstance(blob, str)
            or not blob.startswith("sha256:")
            or not isinstance(size, int)
            or not isinstance(path, str)
            or not isinstance(mode, str)
        ):
            raise D1bPersistenceError("generation_snapshot_entry_invalid")
        return store.read(blob.removeprefix("sha256:"), size), mode

    if kind == "result":
        workspace = db.execute(
            text(
                "SELECT workspace_id FROM generation_workspaces "
                "WHERE task_id=:task AND revision=:revision"
            ),
            {"task": task_id, "revision": generation_revision},
        ).scalar_one_or_none()
        repository = record.get("source", {}).get("repository")
        if not repository:
            capture = capture_mapping({}, source_ref=source_ref)
        else:
            work_root_value = os.environ.get("POLYNEXUS_WORK_ROOT")
            if not work_root_value or workspace is None:
                raise D1bPersistenceError("managed_workspace_unavailable")
            work_root = Path(work_root_value)
            if not work_root.is_absolute():
                raise D1bPersistenceError("workspace_root_invalid")
            root = work_root.resolve(strict=False)
            workspace_path = root / workspace
            resolved = workspace_path.resolve(strict=False)
            if workspace_path.is_symlink() or not resolved.is_relative_to(root) or not resolved.is_dir():
                raise D1bPersistenceError("managed_workspace_invalid")
            capture = capture_directory(resolved, source_ref=source_ref)
    elif kind == "baseline":
        entries = record.get("source", {}).get("baseline", {}).get("entries", [])
        if not isinstance(entries, list):
            raise D1bPersistenceError("generation_snapshot_entries_invalid")
        capture = capture_mapping(
            {entry["path"]: read_entry(entry) for entry in entries},
            source_ref=source_ref,
        )
    else:
        key = "requirements" if kind == "requirements" else "validation"
        item = record.get(key)
        if not isinstance(item, dict):
            raise D1bPersistenceError("generation_snapshot_input_invalid")
        try:
            data = store.read(item["hash"], item["size"])
        except (KeyError, TypeError, ContentError) as exc:
            raise D1bPersistenceError("generation_snapshot_input_invalid") from exc
        capture = capture_mapping(
            {"requirements.txt" if kind == "requirements" else "validation.json": (data, "100644")},
            source_ref=source_ref,
        )
    snapshot_id = D1bRepository(db, store).save_snapshot(capture)
    return {
        "snapshot_id": snapshot_id,
        "kind": kind,
        "task_id": task_id,
        "generation_revision": generation_revision,
        "run_id": run_id,
        "lineage_ref": claim["lineage"],
        "source_ref": source_ref,
        "quiescent": capture.quiescent,
    }


def _observation(candidate_id: str, contract_id: str, value: dict[str, Any]) -> EvidenceObservation:
    allowed = {
        "check_id", "evidence_type", "actor_id", "source", "requiredness", "applicability",
        "outcome", "validity", "command", "cwd", "argv", "runner_exit", "child_exit",
        "raw_artifact_ref", "raw_artifact_sha256", "freshness", "provenance", "reason", "observed_at",
    }
    if set(value) - allowed:
        raise HTTPException(status_code=422, detail="evidence_fields_invalid")
    try:
        return EvidenceObservation(
            candidate_id=candidate_id,
            contract_id=contract_id,
            check_id=value["check_id"],
            evidence_type=value["evidence_type"],
            actor_id=value["actor_id"],
            source=value["source"],
            requiredness=Requiredness(value["requiredness"]),
            applicability=Applicability(value["applicability"]),
            outcome=VerificationOutcome(value["outcome"]),
            validity=Validity(value["validity"]),
            command=value.get("command"),
            cwd=value.get("cwd"),
            argv=tuple(value.get("argv", ())),
            runner_exit=value.get("runner_exit"),
            child_exit=value.get("child_exit"),
            raw_artifact_ref=value.get("raw_artifact_ref"),
            raw_artifact_sha256=value.get("raw_artifact_sha256"),
            freshness=value.get("freshness", "CURRENT"),
            provenance=value.get("provenance", {}),
            reason=value.get("reason"),
            observed_at=value.get("observed_at", datetime.now().astimezone()),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail="evidence_observation_invalid") from error


@router.post("/candidates", status_code=status.HTTP_201_CREATED)
def create_candidate(body: CreateCandidateBody, _auth: AuthLoopback, db: DbSession):
    _d1b_fixture_only()
    try:
        repo = D1bRepository(db, content_store())
        if body.requirements is None or body.validation_contract is None:
            raise D1bPersistenceError("test_snapshot_closure_required")
        requirements = _decode_snapshot(body.requirements)
        validation = _decode_snapshot(body.validation_contract)
        if requirements.manifest.snapshot_id != body.requirements_snapshot_id:
            raise D1bPersistenceError("requirements_snapshot_identity_mismatch")
        if validation.manifest.snapshot_id != body.validation_contract_snapshot_id:
            raise D1bPersistenceError("validation_snapshot_identity_mismatch")
        repo.save_snapshot(requirements)
        repo.save_snapshot(validation)
        return repo.publish_candidate(
            baseline=_decode_snapshot(body.baseline),
            result=_decode_snapshot(body.result),
            requirements_snapshot_id=body.requirements_snapshot_id,
            validation_contract_snapshot_id=body.validation_contract_snapshot_id,
            task_id=body.task_id,
            generation_revision=body.generation_revision,
            run_id=body.run_id,
            lineage_ref=body.lineage_ref,
            provenance=body.provenance,
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as error:
        db.rollback()
        raise _error(error) from None
    finally:
        if db.in_transaction():
            db.commit()


@router.post("/tasks/{task_id}/generations/{generation_revision}/candidates", status_code=status.HTTP_201_CREATED)
def create_scoped_candidate(
    task_id: str,
    generation_revision: int,
    body: SnapshotIdCandidateBody,
    _auth: AuthLoopback,
    db: DbSession,
):
    try:
        return D1bRepository(db, content_store()).publish_candidate_from_snapshot_ids(
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=body.run_id,
            baseline_snapshot_id=body.baseline_snapshot_id,
            result_snapshot_id=body.result_snapshot_id,
            requirements_snapshot_id=body.requirements_snapshot_id,
            validation_contract_snapshot_id=body.validation_contract_snapshot_id,
            lineage_ref=body.lineage_ref,
            provenance=body.provenance,
        )
    except Exception as error:
        db.rollback()
        raise _error(error) from None
    finally:
        if db.in_transaction():
            db.commit()


@router.post(
    "/tasks/{task_id}/generations/{generation_revision}/snapshots",
    status_code=status.HTTP_201_CREATED,
)
def capture_generation_snapshot(
    task_id: str,
    generation_revision: int,
    body: GenerationSnapshotBody,
    _auth: AuthLoopback,
    db: DbSession,
):
    try:
        result = _generation_snapshot(
            db,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=body.run_id,
            kind=body.kind,
        )
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.get("/candidates/{candidate_id}/view")
def candidate_view(candidate_id: str, _auth: AuthLoopback, db: DbSession, policy_revision: int = 1):
    try:
        return D1bRepository(db, content_store()).candidate_view(candidate_id, policy_revision=policy_revision)
    except Exception as error:
        raise _error(error, code=404) from None


@router.post("/candidates/{candidate_id}/verifications", status_code=status.HTTP_201_CREATED)
def verify_candidate(candidate_id: str, body: EvidenceBody, _auth: AuthLoopback, db: DbSession):
    _d1b_fixture_only()
    try:
        repo = D1bRepository(db, content_store())
        observations = [_observation(candidate_id, body.contract_id, value) for value in body.observations]
        result = repo.verify_candidate(
            candidate_id=candidate_id,
            contract_id=body.contract_id,
            observations=observations,
            trusted_runner="core-test:http",
        )
        db.commit()
        return result.as_dict()
    except HTTPException:
        db.rollback()
        raise
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post(
    "/tasks/{task_id}/generations/{generation_revision}/candidates/{candidate_id}/verification",
    status_code=status.HTTP_201_CREATED,
)
def verify_candidate_from_generation_run(
    task_id: str,
    generation_revision: int,
    candidate_id: str,
    body: GenerationVerificationBody,
    _auth: AuthLoopback,
    db: DbSession,
):
    try:
        result = D1bRepository(db, content_store()).verify_candidate_from_run(
            candidate_id=candidate_id,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=body.run_id,
        )
        db.commit()
        return result.as_dict()
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post(
    "/tasks/{task_id}/generations/{generation_revision}/candidates/{candidate_id}/cross-review-runs",
    status_code=status.HTTP_201_CREATED,
    response_model=CrossReviewRunResponse,
)
def create_cross_review_run(
    task_id: str,
    generation_revision: int,
    candidate_id: str,
    body: CrossReviewRunBody,
    _auth: AuthLoopback,
    db: DbSession,
):
    """Create the Core-owned reviewer Run used by the cross-review boundary.

    The caller supplies only the target coordinates.  Reviewer identity,
    parent scope, and runtime binding are issued by the D1b repository; the
    returned Run is the only reviewer identity accepted by the consumer route.
    """
    try:
        run = D1bRepository(db, content_store()).create_cross_review_run(
            candidate_id=candidate_id,
            task_id=task_id,
            generation_revision=generation_revision,
            target_run_id=body.target_run_id,
        )
        db.commit()
        return CrossReviewRunResponse(
            run_id=run.id,
            task_id=run.task_id,
            generation_revision=run.generation_revision,
            generation_parent_run_id=run.generation_parent_run_id or "",
            runtime_ref=run.runtime_ref or "",
            state=run.state.value,
        )
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post(
    "/tasks/{task_id}/generations/{generation_revision}/candidates/{candidate_id}/cross-review-verification",
    status_code=status.HTTP_201_CREATED,
)
def verify_candidate_cross_review_from_generation_run(
    task_id: str,
    generation_revision: int,
    candidate_id: str,
    body: CrossReviewVerificationBody,
    _auth: AuthLoopback,
    db: DbSession,
):
    try:
        result = D1bRepository(db, content_store()).verify_candidate_cross_review_from_run(
            candidate_id=candidate_id,
            task_id=task_id,
            generation_revision=generation_revision,
            reviewer_run_id=body.reviewer_run_id,
        )
        db.commit()
        return result.as_dict()
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/candidates/{candidate_id}/assurance", status_code=status.HTTP_201_CREATED)
def append_assurance(candidate_id: str, body: AssuranceBody, _auth: AuthLoopback, db: DbSession):
    try:
        result = D1bRepository(db, content_store()).append_assurance(
            candidate_id=candidate_id,
            mode=AssuranceMode(body.mode),
            target_type=body.target_type,
            target_id=body.target_id,
            profile_ref=body.profile_ref,
            profile_revision=body.profile_revision,
            reason=body.reason,
        )
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/human/enrollment/challenges", status_code=status.HTTP_201_CREATED)
def issue_enrollment_challenge(
    body: EnrollmentChallengeBody,
    request: Request,
    _auth: AuthLoopback,
    db: DbSession,
):
    _human_protocol_enabled()
    _require_ui_origin(request)
    try:
        result = D1bRepository(db, content_store()).issue_enrollment_challenge(**body.model_dump())
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/human/enrollment/credentials", status_code=status.HTTP_201_CREATED)
def register_enrollment_credential(
    body: RegisterCredentialBody,
    request: Request,
    _auth: AuthLoopback,
    db: DbSession,
):
    _human_protocol_enabled()
    _require_ui_origin(request)
    try:
        result = D1bRepository(db, content_store()).register_webauthn_credential(
            challenge_id=body.challenge_id,
            credential=body.credential.model_dump(),
        )
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/human/enrollment/revoke")
def revoke_enrollment_credential(
    body: RevokeCredentialBody,
    request: Request,
    _auth: AuthLoopback,
    db: DbSession,
):
    _human_protocol_enabled()
    _require_ui_origin(request)
    try:
        result = D1bRepository(db, content_store()).revoke_webauthn_key(
            challenge_id=body.challenge_id,
            key_id=body.key_id,
            credential=body.credential.model_dump(),
        )
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/human/pairings", status_code=status.HTTP_201_CREATED)
def create_pairing(body: PairingBody, request: Request, _auth: AuthLoopback, db: DbSession):
    _human_protocol_enabled()
    is_webauthn = body.challenge_id is not None or body.credential is not None
    if is_webauthn:
        _require_ui_origin(request)
    else:
        _d1b_fixture_only()
    try:
        repo = D1bRepository(db, content_store())
        if is_webauthn:
            if body.challenge_id is None or body.credential is None:
                raise HumanProtocolError("webauthn_pairing_fields_required")
            result = repo.create_webauthn_pairing(
                challenge_id=body.challenge_id,
                credential=body.credential.model_dump(),
                expires_at=body.expires_at,
            )
        else:
            if body.principal_ref is None or body.enrollment_proof is None:
                raise HumanProtocolError("fixture_pairing_fields_required")
            result = repo.create_pairing(
                principal_ref=body.principal_ref,
                enrollment_proof=body.enrollment_proof,
                expires_at=body.expires_at,
            )
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/human/sessions", status_code=status.HTTP_201_CREATED)
def create_session(body: SessionBody, request: Request, _auth: AuthLoopback, db: DbSession):
    _human_protocol_enabled()
    _require_local_human_origin(request)
    try:
        if (body.pairing_proof is None) == (body.pairing_token is None):
            raise HumanProtocolError("pairing_credential_required")
        result = D1bRepository(db, content_store()).create_session(
            grant_id=body.grant_id,
            pairing_proof=body.pairing_token or body.pairing_proof,
            audience=body.audience,
            csrf_token=body.csrf_token,
            expires_at=body.expires_at,
        )
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/human/sessions/{session_id}/revoke")
def revoke_human_session(
    session_id: str,
    body: SessionRevokeBody,
    request: Request,
    _auth: AuthLoopback,
    db: DbSession,
):
    _human_protocol_enabled()
    _require_local_human_origin(request)
    try:
        result = D1bRepository(db, content_store()).revoke_session(
            session_id=session_id,
            csrf_token=body.csrf_token,
        )
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/human/decision-challenges", status_code=status.HTTP_201_CREATED)
def decision_challenge(body: ChallengeBody, request: Request, _auth: AuthLoopback, db: DbSession):
    _human_protocol_enabled()
    _require_local_human_origin(request)
    try:
        result = D1bRepository(db, content_store()).issue_challenge(**body.model_dump())
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/human/decisions", status_code=status.HTTP_201_CREATED)
def decision(body: DecisionBody, request: Request, _auth: AuthLoopback, db: DbSession):
    _human_protocol_enabled()
    try:
        origins = request.headers.getlist("origin")
        if len(origins) != 1:
            raise HumanProtocolError("origin_rejected")
        actual_origin = origins[0]
        expected_origin = os.environ.get("POLYNEXUS_UI_ORIGIN", "http://127.0.0.1:5173")
        if actual_origin != body.origin or actual_origin != expected_origin:
            raise HumanProtocolError("origin_rejected")
        payload = body.model_dump()
        payload["origin"] = actual_origin
        payload["expected_origin"] = expected_origin
        result = D1bRepository(db, content_store()).submit_decision(**payload)
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/accepted/{acceptance_id}/open", status_code=status.HTTP_202_ACCEPTED)
def open_accepted(acceptance_id: str, body: OpenAcceptedBody, _auth: AuthLoopback, db: DbSession):
    try:
        result = D1bRepository(db, content_store()).open_accepted_worktree(
            acceptance_id=acceptance_id, target_dir=Path(body.target_dir), owner_ref=body.owner_ref
        )
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/workspaces/{workspace_id}/takeover")
def takeover(workspace_id: str, body: TakeoverBody, _auth: AuthLoopback, db: DbSession):
    try:
        result = D1bRepository(db, content_store()).takeover_workspace(workspace_id, owner_ref=body.owner_ref)
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None


@router.post("/accepted/{acceptance_id}/exports", status_code=status.HTTP_202_ACCEPTED)
def export_accepted(acceptance_id: str, body: ExportBody, _auth: AuthLoopback, db: DbSession):
    try:
        result = D1bRepository(db, content_store()).export_p0(
            acceptance_id=acceptance_id, package_path=Path(body.package_path)
        )
        db.commit()
        return result
    except Exception as error:
        db.rollback()
        raise _error(error) from None
