"""Durable D1b Candidate, evidence, Human decision and P0 boundaries.

The repository is deliberately the only place where D1b domain identities are
joined to SQL rows or Core-owned bytes.  Callers may provide metadata for
publication, but they cannot provide an identity-bearing change list, a Human
principal, an assurance status, or an accepted result.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import stat
import zipfile
import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from polynexus_core.domain.d1b import (
    Applicability,
    AssuranceMode,
    AssuranceStatus,
    Candidate,
    CanonicalizationError,
    ChangeSet,
    EvidenceObservation,
    EvidenceBindingError,
    Publication,
    Requiredness,
    SnapshotCapture,
    SnapshotEntry,
    SnapshotManifest,
    parse_validation_contract,
    VerificationOutcome,
    VerificationResult,
    Validity,
    canonical_json,
    changeset_from_json,
    derive_assurance_status,
    derive_changeset,
    evaluate_verification,
    manifest_from_json,
    sha256_id,
    validate_digest,
    validate_relative_path,
)
from polynexus_core.persistence.models import (
    AcceptedResultRow,
    ArtifactRow,
    AssuranceAssessmentRow,
    CandidatePublicationRow,
    CandidateRow,
    ChangeSetRow,
    ContentSnapshotRow,
    ContentSnapshotObservationRow,
    EvidenceRow,
    EvidenceSetRow,
    HumanChallengeRow,
    HumanDecisionEventRow,
    HumanEnrollmentChallengeRow,
    HumanPairingGrantRow,
    HumanSessionRow,
    HumanTrustKeyRow,
    ManagedWorktreeRow,
    P0PackageRow,
    RunRow,
    TaskRow,
    VerificationRecordRow,
)
from polynexus_core.storage.content import ContentError, ContentStore
from polynexus_core.runtime.d1b_producer import (
    D1bExecutionPlan,
    build_d1b_execution_plan,
    produce_d1b_runtime_evidence,
)
from polynexus_core.security.a_lp import (
    ALPVerificationError,
    b64u_decode,
    b64u_encode,
    challenge_digest,
    credential_fingerprint,
    load_config,
    verify_assertion,
    verify_registration,
)


class D1bPersistenceError(ValueError):
    """Bounded fail-closed persistence or protocol rejection."""


class HumanProtocolError(D1bPersistenceError):
    pass


class P0PackageError(D1bPersistenceError):
    pass


CURRENT_POLICY_REVISION = 1
D11_TRUST_SCOPE = "local-personal"
D11_AUTH_METHOD = "d11-a-lp-session"
HUMAN_ENROLLMENT_ASSERTION_FORMAT = "pn-d11-a-lp-enrollment-v1"
HUMAN_WEBAUTHN_ASSERTION_FORMAT = "pn-d11-a-lp-webauthn-v2"
HUMAN_WEBAUTHN_AUTH_METHOD = "d11-a-lp-webauthn"
HUMAN_TEST_AUTH_METHOD = "d11-a-lp-test-fixture"
HUMAN_KEY_ACTIVE = "ACTIVE"
HUMAN_KEY_RETIRING = "RETIRING"
HUMAN_KEY_REVOKED = "REVOKED"
HUMAN_KEY_COMPROMISED = "COMPROMISED"
_ACCEPTED_AUTH_METHODS = frozenset({
    D11_AUTH_METHOD,
    HUMAN_WEBAUTHN_AUTH_METHOD,
    HUMAN_TEST_AUTH_METHOD,
})
P0_RECEIPT_FORMAT = "pn.p0-receipt.v1"

_ED25519_Q = 2**255 - 19
_ED25519_L = 2**252 + 27742317777372353535851937790883648493
_ED25519_D = (-121665 * pow(121666, _ED25519_Q - 2, _ED25519_Q)) % _ED25519_Q
_ED25519_I = pow(2, (_ED25519_Q - 1) // 4, _ED25519_Q)
_ED25519_BY = (4 * pow(5, _ED25519_Q - 2, _ED25519_Q)) % _ED25519_Q


def _ed25519_xrecover(y: int) -> int:
    xx = ((y * y - 1) * pow(_ED25519_D * y * y + 1, _ED25519_Q - 2, _ED25519_Q)) % _ED25519_Q
    x = pow(xx, (_ED25519_Q + 3) // 8, _ED25519_Q)
    if (x * x - xx) % _ED25519_Q != 0:
        x = (x * _ED25519_I) % _ED25519_Q
    if x & 1:
        x = _ED25519_Q - x
    return x


def _ed25519_base() -> tuple[int, int]:
    return _ed25519_xrecover(_ED25519_BY), _ED25519_BY


def _ed25519_add(first: tuple[int, int], second: tuple[int, int]) -> tuple[int, int]:
    x1, y1 = first
    x2, y2 = second
    product = (_ED25519_D * x1 * x2 * y1 * y2) % _ED25519_Q
    x3 = ((x1 * y2 + y1 * x2) * pow(1 + product, _ED25519_Q - 2, _ED25519_Q)) % _ED25519_Q
    y3 = ((y1 * y2 + x1 * x2) * pow(1 - product, _ED25519_Q - 2, _ED25519_Q)) % _ED25519_Q
    return x3, y3


def _ed25519_scalarmult(point: tuple[int, int], scalar: int) -> tuple[int, int]:
    result = (0, 1)
    addend = point
    while scalar:
        if scalar & 1:
            result = _ed25519_add(result, addend)
        addend = _ed25519_add(addend, addend)
        scalar >>= 1
    return result


def _ed25519_encode(point: tuple[int, int]) -> bytes:
    x, y = point
    value = y | ((x & 1) << 255)
    return value.to_bytes(32, "little")


def _ed25519_decode(value: bytes) -> tuple[int, int]:
    if len(value) != 32:
        raise ValueError("ed25519_point_length")
    encoded = int.from_bytes(value, "little")
    sign = encoded >> 255
    y = encoded & ((1 << 255) - 1)
    if y >= _ED25519_Q:
        raise ValueError("ed25519_point_invalid")
    x = _ed25519_xrecover(y)
    if (x * x - (y * y - 1) * pow(_ED25519_D * y * y + 1, _ED25519_Q - 2, _ED25519_Q)) % _ED25519_Q != 0:
        raise ValueError("ed25519_point_invalid")
    if (x & 1) != sign:
        x = _ED25519_Q - x
    return x, y


def _ed25519_public_key(seed: bytes) -> bytes:
    if len(seed) != 32:
        raise ValueError("ed25519_private_key_invalid")
    digest = hashlib.sha512(seed).digest()
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    return _ed25519_encode(_ed25519_scalarmult(_ed25519_base(), scalar))


def _ed25519_sign(seed: bytes, message: bytes) -> bytes:
    if len(seed) != 32:
        raise ValueError("ed25519_private_key_invalid")
    digest = hashlib.sha512(seed).digest()
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    public = _ed25519_public_key(seed)
    nonce = int.from_bytes(hashlib.sha512(digest[32:] + message).digest(), "little") % _ED25519_L
    encoded_nonce = _ed25519_encode(_ed25519_scalarmult(_ed25519_base(), nonce))
    challenge = int.from_bytes(hashlib.sha512(encoded_nonce + public + message).digest(), "little") % _ED25519_L
    response = (nonce + challenge * scalar) % _ED25519_L
    return encoded_nonce + response.to_bytes(32, "little")


def _ed25519_verify(public: bytes, message: bytes, signature: bytes) -> bool:
    if len(public) != 32 or len(signature) != 64:
        return False
    try:
        r_point = _ed25519_decode(signature[:32])
        public_point = _ed25519_decode(public)
    except ValueError:
        return False
    response = int.from_bytes(signature[32:], "little")
    if response >= _ED25519_L:
        return False
    challenge = int.from_bytes(hashlib.sha512(signature[:32] + public + message).digest(), "little") % _ED25519_L
    left = _ed25519_scalarmult(_ed25519_base(), response)
    right = _ed25519_add(r_point, _ed25519_scalarmult(public_point, challenge))
    return left == right


def _configured_hex_key(name: str, length: int) -> bytes:
    value = os.environ.get(name, "")
    try:
        result = bytes.fromhex(value)
    except ValueError as exc:
        raise P0PackageError(f"{name.lower()}_invalid") from exc
    if len(result) != length:
        raise P0PackageError(f"{name.lower()}_invalid")
    return result


@dataclass(frozen=True)
class SnapshotRecord:
    manifest: SnapshotManifest
    closure: Mapping[str, int]
    source_ref: str | None


@dataclass(frozen=True)
class CandidateContext:
    candidate: Candidate
    changeset: ChangeSet
    baseline: SnapshotRecord
    result: SnapshotRecord
    requirements: SnapshotRecord
    validation: SnapshotRecord


def _now(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _db_time(value: datetime | None = None) -> datetime:
    return _now(value).replace(tzinfo=None)


def _display_time(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _now(value).isoformat()


def _random_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(16)}"


def _json_text(value: Any) -> str:
    return canonical_json(value).decode("utf-8")


def _parse_json(value: str, error: str = "stored_json_invalid") -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise D1bPersistenceError(error) from exc


def _secret_bytes(value: str | bytes, name: str) -> bytes:
    if isinstance(value, bytes):
        result = value
    elif isinstance(value, str):
        result = value.encode("utf-8")
    else:
        raise HumanProtocolError(f"{name}_invalid")
    if not result:
        raise HumanProtocolError(f"{name}_missing")
    return result


def _raw_digest(value: str | bytes, name: str) -> str:
    return hashlib.sha256(_secret_bytes(value, name)).hexdigest()


def _a_lp_config():
    try:
        return load_config()
    except ALPVerificationError as exc:
        raise HumanProtocolError(str(exc)) from exc


def _human_fixture_enabled() -> bool:
    return (
        os.environ.get("POLYNEXUS_D1B_TEST_MODE") == "1"
        and os.environ.get("POLYNEXUS_ENVIRONMENT") == "TEST"
    )


def _trusted_runner_attestation_ref() -> str:
    """Return a non-secret fingerprint for the configured runner attestation."""
    secret = _secret_bytes(
        os.environ.get("POLYNEXUS_TRUSTED_RUNNER_ATTESTATION", ""),
        "trusted_runner_attestation",
    )
    return "sha256:" + hashlib.sha256(secret).hexdigest()


def _evidence_identity(
    *,
    candidate_id: str,
    contract_id: str,
    evidence_refs: Sequence[str],
    observations: Sequence[Mapping[str, Any]],
    trusted_runner_ref: str,
) -> dict[str, Any]:
    """Return the complete content-addressed EvidenceSet closure.

    The identity intentionally covers the candidate/contract binding, every
    normalized observation, and the trusted runner reference.  The stored
    ``evidence_set_id`` must therefore change when any evidence-bearing value
    changes, rather than only when the list of evidence references changes.
    """
    return {
        "candidate_id": candidate_id,
        "contract_id": contract_id,
        "evidence_refs": list(evidence_refs),
        "format": "pn.evidence-set.v1",
        "observations": list(observations),
        "trusted_runner_ref": trusted_runner_ref,
    }


def _urlsafe_json(value: Mapping[str, Any]) -> str:
    return base64.urlsafe_b64encode(canonical_json(value)).decode("ascii").rstrip("=")


def _decode_urlsafe_json(value: str, error: str) -> dict[str, Any]:
    if not isinstance(value, str) or not value:
        raise HumanProtocolError(error)
    try:
        padded = value + "=" * (-len(value) % 4)
        parsed = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error) as exc:
        raise HumanProtocolError(error) from exc
    if not isinstance(parsed, dict) or canonical_json(parsed).decode("utf-8") != json.dumps(
        parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ):
        raise HumanProtocolError(error)
    return parsed


def _enrollment_secret() -> bytes:
    try:
        return _secret_bytes(
            os.environ.get("POLYNEXUS_HUMAN_A_LP_ENROLLMENT_SECRET", ""),
            "human_enrollment_secret",
        )
    except HumanProtocolError as exc:
        raise HumanProtocolError("human_enrollment_unavailable") from exc


def _verify_human_enrollment_assertion(
    *,
    principal_ref: str,
    enrollment_proof: str | bytes,
    expires_at: datetime,
) -> datetime:
    """Verify the deterministic v1 fixture assertion.

    This HMAC path is intentionally limited to the TEST fixture seam. The
    production LOCAL path uses the Core-owned public-key trust registry and
    WebAuthn verification below; this function must never be used as its trust
    root.
    """
    if not _human_fixture_enabled():
        raise HumanProtocolError("enrollment_fixture_only")
    if isinstance(enrollment_proof, bytes):
        try:
            proof = enrollment_proof.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HumanProtocolError("enrollment_proof_invalid") from exc
    else:
        proof = enrollment_proof
    if not isinstance(proof, str):
        raise HumanProtocolError("enrollment_proof_invalid")
    parts = proof.split(".")
    if len(parts) != 3 or parts[0] != HUMAN_ENROLLMENT_ASSERTION_FORMAT:
        raise HumanProtocolError("enrollment_assertion_invalid")
    payload_segment, signature = parts[1], parts[2]
    if len(signature) != 64 or any(char not in "0123456789abcdef" for char in signature):
        raise HumanProtocolError("enrollment_assertion_invalid")
    payload = _decode_urlsafe_json(payload_segment, "enrollment_assertion_invalid")
    if set(payload) != {"expires_at", "issued_at", "nonce", "principal_ref"}:
        raise HumanProtocolError("enrollment_assertion_invalid")
    if payload.get("principal_ref") != principal_ref:
        raise HumanProtocolError("enrollment_principal_mismatch")
    try:
        issued_at = _now(datetime.fromisoformat(payload["issued_at"]))
        assertion_expiry = _now(datetime.fromisoformat(payload["expires_at"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise HumanProtocolError("enrollment_assertion_invalid") from exc
    requested_expiry = _now(expires_at)
    now = _now()
    if not isinstance(payload["nonce"], str) or not payload["nonce"].strip():
        raise HumanProtocolError("enrollment_assertion_invalid")
    if requested_expiry <= now or issued_at > now or assertion_expiry <= now:
        raise HumanProtocolError("enrollment_assertion_expired")
    signed = f"{parts[0]}.{payload_segment}".encode("utf-8")
    expected = hmac.new(_enrollment_secret(), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HumanProtocolError("enrollment_assertion_invalid")
    return assertion_expiry


def _p0_receipt_unsigned(manifest: Mapping[str, Any]) -> dict[str, Any]:
    acceptance = manifest.get("acceptance")
    if not isinstance(acceptance, Mapping):
        raise P0PackageError("p0_receipt_binding_invalid")
    return {
        "acceptance_id": manifest.get("acceptance_id"),
        "candidate_id": manifest.get("candidate_id"),
        "decision_id": acceptance.get("accept_decision_id"),
        "format": P0_RECEIPT_FORMAT,
        "key_id": os.environ.get("POLYNEXUS_P0_RECEIPT_KEY_ID", "default"),
        "manifest_digest": sha256_id(canonical_json(manifest)),
        "view_digest": acceptance.get("view_digest"),
    }


def _p0_receipt(manifest: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = _p0_receipt_unsigned(manifest)
    try:
        private_key = _configured_hex_key("POLYNEXUS_P0_RECEIPT_PRIVATE_KEY", 32)
    except P0PackageError as exc:
        raise P0PackageError("p0_receipt_unavailable") from exc
    signature = _ed25519_sign(private_key, canonical_json(unsigned)).hex()
    return {**unsigned, "signature": signature}


def _verify_p0_receipt(manifest: Mapping[str, Any], receipt: Mapping[str, Any]) -> None:
    if set(receipt) != {
        "acceptance_id", "candidate_id", "decision_id", "format", "key_id", "manifest_digest", "signature", "view_digest",
    }:
        raise P0PackageError("p0_receipt_invalid")
    expected_unsigned = _p0_receipt_unsigned(manifest)
    unsigned = {key: receipt[key] for key in expected_unsigned}
    if unsigned != expected_unsigned:
        raise P0PackageError("p0_receipt_binding_mismatch")
    signature = receipt["signature"]
    if not isinstance(signature, str) or len(signature) != 128 or any(
        char not in "0123456789abcdef" for char in signature
    ):
        raise P0PackageError("p0_receipt_invalid")
    try:
        public_key = _configured_hex_key("POLYNEXUS_P0_RECEIPT_PUBLIC_KEY", 32)
    except P0PackageError as exc:
        raise P0PackageError("p0_receipt_unavailable") from exc
    try:
        signature_bytes = bytes.fromhex(signature)
    except ValueError as exc:
        raise P0PackageError("p0_receipt_invalid") from exc
    if not _ed25519_verify(public_key, canonical_json(unsigned), signature_bytes):
        raise P0PackageError("p0_receipt_signature_invalid")


def _ensure_ref(value: str, name: str) -> str:
    try:
        return validate_digest(value, field_name=name)
    except CanonicalizationError as exc:
        raise D1bPersistenceError(str(exc)) from exc


def _read_closure(value: str) -> dict[str, int]:
    parsed = _parse_json(value, "source_closure_invalid")
    if not isinstance(parsed, dict):
        raise D1bPersistenceError("source_closure_invalid")
    result: dict[str, int] = {}
    for digest, size in parsed.items():
        _ensure_ref(digest, "closure_blob")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise D1bPersistenceError("source_closure_invalid")
        result[digest] = size
    return result


def _row_created(row: Any) -> str | None:
    return _display_time(getattr(row, "created_at", None))


class D1bRepository:
    """Persistence gateway for the D1b immutable graph and Human protocol."""

    def __init__(self, session: Session, content_store: ContentStore | None = None):
        self.session = session
        if content_store is None:
            configured = os.environ.get("POLYNEXUS_CONTENT_ROOT")
            if configured:
                content_store = ContentStore(Path(configured))
        self.content_store = content_store
        # This cache is only a test/degraded-process convenience.  Production
        # P0 export requires a configured Core ContentStore and re-reads bytes
        # through its hash-verified boundary.
        self._blob_cache: dict[str, bytes] = {}

    # ------------------------------------------------------------------
    # W3: exact snapshots, Core-derived changes and immutable Candidates
    # ------------------------------------------------------------------

    def _put_blob(self, digest: str, content: bytes) -> None:
        if not isinstance(content, bytes):
            raise D1bPersistenceError("blob_type_invalid")
        expected = "sha256:" + hashlib.sha256(content).hexdigest()
        if expected != digest:
            raise D1bPersistenceError("blob_identity_mismatch")
        if self.content_store is not None:
            try:
                stored, size = self.content_store.put(content)
            except ContentError as exc:
                raise D1bPersistenceError(str(exc)) from exc
            if stored != digest.removeprefix("sha256:") or size != len(content):
                raise D1bPersistenceError("blob_store_identity_mismatch")
        self._blob_cache[digest] = content

    def _read_blob(self, digest: str, size: int) -> bytes:
        _ensure_ref(digest, "blob")
        if self.content_store is not None:
            try:
                value = self.content_store.read(digest.removeprefix("sha256:"), size)
            except ContentError as exc:
                raise P0PackageError(str(exc)) from exc
        else:
            value = self._blob_cache.get(digest)
            if value is None:
                raise P0PackageError("blob_unavailable")
        if len(value) != size or sha256_id(value) != digest:
            raise P0PackageError("blob_identity_mismatch")
        return value

    def save_snapshot(self, capture: SnapshotCapture) -> str:
        if not capture.quiescent:
            raise D1bPersistenceError("writer_not_quiescent")
        if capture.source_ref is not None and (
            not isinstance(capture.source_ref, str)
            or not capture.source_ref.strip()
            or len(capture.source_ref) > 512
        ):
            raise D1bPersistenceError("snapshot_source_ref_invalid")
        canonical = capture.manifest.canonical_bytes.decode("utf-8")
        closure = {entry.blob: entry.size for entry in capture.manifest.entries}
        row = self.session.get(ContentSnapshotRow, capture.manifest.snapshot_id)
        if row is not None:
            if row.canonical_json != canonical or _read_closure(row.source_closure_json) != closure:
                raise D1bPersistenceError("snapshot_identity_conflict")
        else:
            for digest, content in capture.blobs.items():
                self._put_blob(digest, content)
            row = ContentSnapshotRow(
                snapshot_id=capture.manifest.snapshot_id,
                canonical_json=canonical,
                source_closure_json=_json_text(closure),
                source_ref=capture.source_ref,
                created_at=_db_time(),
            )
            self.session.add(row)
            self.session.flush()
        if capture.source_ref is not None:
            existing_observation = self.session.execute(
                select(ContentSnapshotObservationRow)
                .where(
                    ContentSnapshotObservationRow.snapshot_id == row.snapshot_id,
                    ContentSnapshotObservationRow.source_ref == capture.source_ref,
                )
                .limit(1)
            ).scalar_one_or_none()
            if existing_observation is None:
                observation_id = "snapshot-observation_" + hashlib.sha256(
                    canonical_json({
                        "snapshot_id": row.snapshot_id,
                        "source_ref": capture.source_ref,
                    })
                ).hexdigest()[:48]
                self.session.add(ContentSnapshotObservationRow(
                    observation_id=observation_id,
                    snapshot_id=row.snapshot_id,
                    source_ref=capture.source_ref,
                    observed_at=_db_time(),
                ))
                self.session.flush()
        return row.snapshot_id

    def _snapshot_observed(self, snapshot_id: str, source_ref: str) -> bool:
        return self.session.execute(
            select(ContentSnapshotObservationRow.observation_id)
            .where(
                ContentSnapshotObservationRow.snapshot_id == snapshot_id,
                ContentSnapshotObservationRow.source_ref == source_ref,
            )
            .limit(1)
        ).scalar_one_or_none() is not None

    def _load_snapshot(self, snapshot_id: str) -> SnapshotRecord:
        _ensure_ref(snapshot_id, "snapshot")
        row = self.session.get(ContentSnapshotRow, snapshot_id)
        if row is None:
            raise D1bPersistenceError("snapshot_not_found")
        manifest = manifest_from_json(row.canonical_json)
        if manifest.snapshot_id != snapshot_id:
            raise D1bPersistenceError("snapshot_identity_mismatch")
        closure = _read_closure(row.source_closure_json)
        expected = {entry.blob: entry.size for entry in manifest.entries}
        if closure != expected:
            raise D1bPersistenceError("snapshot_closure_mismatch")
        return SnapshotRecord(manifest=manifest, closure=closure, source_ref=row.source_ref)

    def _validation_checks(self, context: CandidateContext) -> tuple[dict[str, Any], ...]:
        """Read the immutable, Core-owned validation contract bytes."""
        return parse_validation_contract(self._validation_contract_value(context))

    def _assurance_mode(self, context: CandidateContext) -> AssuranceMode:
        contract = self._validation_contract_value(context)
        policy = contract.get("assurance")
        if not isinstance(policy, Mapping):
            raise D1bPersistenceError("assurance_policy_missing")
        try:
            return AssuranceMode(policy["mode"])
        except (KeyError, TypeError, ValueError) as exc:
            raise D1bPersistenceError("assurance_policy_invalid") from exc

    def _validation_contract_value(self, context: CandidateContext) -> dict[str, Any]:
        """Read and canonicalise the exact validation contract object."""
        entries = context.validation.manifest.entries
        json_entries = [entry for entry in entries if entry.path.lower().endswith(".json")]
        if len(json_entries) != 1:
            raise D1bPersistenceError("validation_contract_json_required")
        entry = json_entries[0]
        try:
            raw = self._read_blob(entry.blob, entry.size)
            value = json.loads(raw.decode("utf-8"))
            if canonical_json(value) != raw:
                raise EvidenceBindingError("validation_contract_noncanonical")
            if not isinstance(value, dict):
                raise EvidenceBindingError("validation_contract_object_invalid")
            parse_validation_contract(value)
            return value
        except (UnicodeDecodeError, json.JSONDecodeError, EvidenceBindingError, CanonicalizationError, P0PackageError) as exc:
            raise D1bPersistenceError("validation_contract_invalid") from exc

    def save_changeset(self, changeset: ChangeSet) -> str:
        row = self.session.get(ChangeSetRow, changeset.changeset_id)
        canonical = changeset.canonical_bytes.decode("utf-8")
        if row is not None:
            if row.canonical_json != canonical:
                raise D1bPersistenceError("changeset_identity_conflict")
            return row.changeset_id
        self._load_snapshot(changeset.baseline)
        self._load_snapshot(changeset.result)
        row = ChangeSetRow(
            changeset_id=changeset.changeset_id,
            baseline_snapshot_id=changeset.baseline,
            result_snapshot_id=changeset.result,
            canonical_json=canonical,
            created_at=_db_time(),
        )
        self.session.add(row)
        self.session.flush()
        return row.changeset_id

    def save_candidate(self, candidate: Candidate) -> str:
        row = self.session.get(CandidateRow, candidate.candidate_id)
        canonical = candidate.canonical_bytes.decode("utf-8")
        if row is not None:
            if row.canonical_json != canonical:
                raise D1bPersistenceError("candidate_identity_conflict")
            return row.candidate_id
        changeset_row = self.session.get(ChangeSetRow, candidate.changeset_id)
        if changeset_row is None:
            raise D1bPersistenceError("changeset_not_found")
        # Candidate references are closure edges, not caller-provided labels.
        # Both requirement and validation identities must already be present
        # in the Core-owned immutable snapshot table before a Candidate can be
        # frozen.
        self._load_snapshot(candidate.requirements_snapshot_id)
        self._load_snapshot(candidate.validation_contract_snapshot_id)
        source_closure = _json_text({
            "baseline_snapshot_id": changeset_row.baseline_snapshot_id,
            "result_snapshot_id": changeset_row.result_snapshot_id,
            "requirements_snapshot_id": candidate.requirements_snapshot_id,
            "validation_contract_snapshot_id": candidate.validation_contract_snapshot_id,
        })
        row = CandidateRow(
            candidate_id=candidate.candidate_id,
            changeset_id=candidate.changeset_id,
            requirements_snapshot_id=candidate.requirements_snapshot_id,
            validation_contract_snapshot_id=candidate.validation_contract_snapshot_id,
            canonical_json=canonical,
            source_closure_json=source_closure,
            frozen=True,
            created_at=_db_time(),
        )
        self.session.add(row)
        self.session.flush()
        return row.candidate_id

    def _validate_publication_scope(
        self,
        *,
        candidate: Candidate,
        baseline_snapshot_id: str,
        result_snapshot_id: str,
        task_id: str | None,
        generation_revision: int | None,
        run_id: str | None,
        lineage_ref: str,
    ) -> None:
        """Bind a publication to the durable Task/Run/Generation graph.

        The in-memory snapshot capture path remains available to deterministic
        Core tests, but any publication carrying execution scope must prove
        all three scope coordinates and the writer lineage in the persisted
        D1a graph.  Partial or caller-invented scope is rejected.
        """
        supplied = (task_id, generation_revision, run_id)
        if not any(value is not None for value in supplied):
            return
        if task_id is None or generation_revision is None or run_id is None:
            raise D1bPersistenceError("publication_scope_incomplete")
        task = self.session.get(TaskRow, task_id)
        run = self.session.get(RunRow, run_id)
        if task is None or run is None or run.task_id != task_id or run.generation_revision != generation_revision:
            raise D1bPersistenceError("publication_scope_mismatch")
        generation = self.session.execute(
            text(
                "SELECT * FROM work_generations "
                "WHERE task_id=:task_id AND revision=:revision"
            ),
            {"task_id": task_id, "revision": generation_revision},
        ).mappings().one_or_none()
        if generation is None:
            raise D1bPersistenceError("generation_not_found")
        if generation["aborted"] or generation["ownership_unknown"]:
            raise D1bPersistenceError("generation_not_publishable")
        try:
            inputs = _parse_json(generation["inputs"], "generation_inputs_invalid")
        except KeyError as exc:
            raise D1bPersistenceError("generation_inputs_invalid") from exc
        if not isinstance(inputs, dict):
            raise D1bPersistenceError("generation_inputs_invalid")
        claim = self.session.execute(
            text(
                "SELECT lineage, released FROM generation_writer_claims "
                "WHERE task_id=:task_id AND revision=:revision AND run_id=:run_id"
            ),
            {"task_id": task_id, "revision": generation_revision, "run_id": run_id},
        ).mappings().one_or_none()
        if claim is None or claim["released"] != 1:
            raise D1bPersistenceError("writer_not_quiescent")
        expected_refs = {
            "requirements_ref": (candidate.requirements_snapshot_id, "requirements"),
            "validation_ref": (candidate.validation_contract_snapshot_id, "validation"),
            "baseline_ref": (baseline_snapshot_id, "baseline"),
            "input_ref": (result_snapshot_id, "result"),
        }
        producer_prefix = f"core:generation:{task_id}:{generation_revision}:{run_id}:"
        for field, (snapshot_id, kind) in expected_refs.items():
            actual = inputs.get(field)
            record = self._load_snapshot(snapshot_id)
            if not self._snapshot_observed(snapshot_id, producer_prefix + kind):
                raise D1bPersistenceError("publication_snapshot_scope_mismatch")
            if field in {"requirements_ref", "validation_ref"}:
                if len(record.manifest.entries) != 1 or record.manifest.entries[0].blob != actual:
                    raise D1bPersistenceError("publication_snapshot_scope_mismatch")
            elif field == "baseline_ref" and sha256_id(record.manifest.canonical_bytes) != actual:
                raise D1bPersistenceError("publication_snapshot_scope_mismatch")
        if claim["lineage"] != lineage_ref:
            raise D1bPersistenceError("publication_lineage_scope_mismatch")

    def _capture_from_snapshot_id(self, snapshot_id: str) -> SnapshotCapture:
        record = self._load_snapshot(snapshot_id)
        blobs = {
            entry.blob: self._read_blob(entry.blob, entry.size)
            for entry in record.manifest.entries
        }
        return SnapshotCapture(
            record.manifest,
            blobs,
            quiescent=True,
            source_ref=record.source_ref,
        )

    def publish_candidate_from_snapshot_ids(
        self,
        *,
        task_id: str,
        generation_revision: int,
        run_id: str,
        baseline_snapshot_id: str,
        result_snapshot_id: str,
        requirements_snapshot_id: str,
        validation_contract_snapshot_id: str,
        lineage_ref: str,
        provenance: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Publish only from snapshots already captured by Core."""
        for value, field in (
            (task_id, "task_id"),
            (run_id, "run_id"),
            (lineage_ref, "lineage_ref"),
        ):
            if not isinstance(value, str) or not value.strip():
                raise D1bPersistenceError(f"{field}_invalid")
        if not isinstance(generation_revision, int) or isinstance(generation_revision, bool) or generation_revision < 1:
            raise D1bPersistenceError("generation_revision_invalid")
        baseline = self._capture_from_snapshot_id(baseline_snapshot_id)
        result = self._capture_from_snapshot_id(result_snapshot_id)
        candidate = Candidate(
            derive_changeset(baseline.manifest, result.manifest).changeset_id,
            requirements_snapshot_id,
            validation_contract_snapshot_id,
        )
        self._validate_publication_scope(
            candidate=candidate,
            baseline_snapshot_id=baseline_snapshot_id,
            result_snapshot_id=result_snapshot_id,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=run_id,
            lineage_ref=lineage_ref,
        )
        return self.publish_candidate(
            baseline=baseline,
            result=result,
            requirements_snapshot_id=requirements_snapshot_id,
            validation_contract_snapshot_id=validation_contract_snapshot_id,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=run_id,
            lineage_ref=lineage_ref,
            provenance=provenance,
        )

    def publish_candidate(
        self,
        *,
        baseline: SnapshotCapture,
        result: SnapshotCapture,
        requirements_snapshot_id: str,
        validation_contract_snapshot_id: str,
        task_id: str | None = None,
        generation_revision: int | None = None,
        run_id: str | None = None,
        lineage_ref: str | None = None,
        provenance: Mapping[str, Any] | None = None,
        caller_changes: Any = None,
    ) -> dict[str, Any]:
        if not baseline.quiescent or not result.quiescent:
            raise D1bPersistenceError("writer_not_quiescent")
        # The raw in-memory route is a deterministic fixture seam only.  A
        # production publication must carry the durable generation/run claim;
        # a caller-provided boolean is never a quiescence proof.
        if (
            task_id is None
            and generation_revision is None
            and run_id is None
            and os.environ.get("POLYNEXUS_D1B_TEST_MODE") != "1"
        ):
            raise D1bPersistenceError("publication_scope_required")
        # A caller-supplied diff is advisory at most.  Rejecting it keeps the
        # identity boundary unambiguous: Core derives the ChangeSet from both
        # complete snapshots and never trusts an externally supplied change.
        if caller_changes is not None:
            raise CanonicalizationError("caller_change_manifest_rejected")
        req = _ensure_ref(requirements_snapshot_id, "requirements")
        validation = _ensure_ref(validation_contract_snapshot_id, "validation")
        baseline_id = self.save_snapshot(baseline)
        result_id = self.save_snapshot(result)
        changeset = derive_changeset(baseline.manifest, result.manifest)
        self.save_changeset(changeset)
        candidate = Candidate(changeset.changeset_id, req, validation)
        self._validate_publication_scope(
            candidate=candidate,
            baseline_snapshot_id=baseline_id,
            result_snapshot_id=result_id,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=run_id,
            lineage_ref=lineage_ref or f"candidate:{candidate.candidate_id}",
        )
        self.save_candidate(candidate)
        if lineage_ref is None:
            lineage_ref = f"candidate:{candidate.candidate_id}"
        publication = Publication(
            candidate_id=candidate.candidate_id,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=run_id,
            lineage_ref=lineage_ref,
            provenance=dict(provenance or {}),
        )
        if len(publication.lineage_ref) > 128:
            raise D1bPersistenceError("publication_lineage_too_long")
        self.session.add(CandidatePublicationRow(
            publication_id=publication.publication_id,
            candidate_id=candidate.candidate_id,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=run_id,
            lineage_ref=publication.lineage_ref,
            provenance_json=_json_text(publication.provenance),
            created_at=_db_time(),
        ))
        self.session.flush()
        return {
            "candidate_id": candidate.candidate_id,
            "changeset_id": changeset.changeset_id,
            "baseline_snapshot_id": baseline_id,
            "result_snapshot_id": result_id,
            "publication_id": publication.publication_id,
            "requirements_snapshot_id": candidate.requirements_snapshot_id,
            "validation_contract_snapshot_id": candidate.validation_contract_snapshot_id,
        }

    def _candidate_context(self, candidate_id: str) -> CandidateContext:
        _ensure_ref(candidate_id, "candidate")
        row = self.session.get(CandidateRow, candidate_id)
        if row is None or not row.frozen:
            raise D1bPersistenceError("candidate_not_found")
        candidate = Candidate(
            changeset_id=row.changeset_id,
            requirements_snapshot_id=row.requirements_snapshot_id,
            validation_contract_snapshot_id=row.validation_contract_snapshot_id,
        )
        if candidate.candidate_id != candidate_id or row.canonical_json != candidate.canonical_bytes.decode("utf-8"):
            raise D1bPersistenceError("candidate_identity_mismatch")
        changeset_row = self.session.get(ChangeSetRow, row.changeset_id)
        if changeset_row is None:
            raise D1bPersistenceError("changeset_not_found")
        changeset = changeset_from_json(changeset_row.canonical_json)
        if changeset.changeset_id != row.changeset_id:
            raise D1bPersistenceError("changeset_identity_mismatch")
        baseline = self._load_snapshot(changeset.baseline)
        result = self._load_snapshot(changeset.result)
        requirements = self._load_snapshot(candidate.requirements_snapshot_id)
        validation = self._load_snapshot(candidate.validation_contract_snapshot_id)
        expected_closure = {
            "baseline_snapshot_id": changeset.baseline,
            "result_snapshot_id": changeset.result,
            "requirements_snapshot_id": candidate.requirements_snapshot_id,
            "validation_contract_snapshot_id": candidate.validation_contract_snapshot_id,
        }
        if _parse_json(row.source_closure_json, "candidate_source_closure_invalid") != expected_closure:
            raise D1bPersistenceError("candidate_source_closure_mismatch")
        return CandidateContext(candidate, changeset, baseline, result, requirements, validation)

    # ------------------------------------------------------------------
    # W4: evidence, verification and derived assurance
    # ------------------------------------------------------------------

    def _materialize_d1b_runtime_evidence(
        self,
        *,
        plan: D1bExecutionPlan,
        run: RunRow,
    ) -> None:
        """Materialize D1b observations from one Core runtime result.

        The runtime adapter persists only generic, provenance-rich result
        evidence.  After the immutable Candidate and exact snapshots exist,
        this Core boundary issues the D1b plan and converts the terminal
        ``d1b_checks`` payload into dedicated evidence/artifacts.  A caller
        cannot inject a plan through ContextPackage facts or submit D1b rows
        directly through this path.
        """

        if self.content_store is None:
            raise D1bPersistenceError("verification_content_store_unavailable")
        if run.task_id != plan.task_id or run.generation_revision != plan.generation_revision or run.id != plan.run_id:
            raise D1bPersistenceError("verification_plan_scope_mismatch")
        try:
            evidence_ids = _parse_json(run.result_evidence_ids, "verification_run_evidence_invalid")
            artifact_ids = _parse_json(run.result_artifact_ids, "verification_run_artifacts_invalid")
        except AttributeError as exc:
            raise D1bPersistenceError("verification_run_result_invalid") from exc
        if (
            not isinstance(evidence_ids, list)
            or any(not isinstance(value, str) for value in evidence_ids)
            or not isinstance(artifact_ids, list)
            or any(not isinstance(value, str) for value in artifact_ids)
        ):
            raise D1bPersistenceError("verification_run_result_invalid")
        evidence_rows = list(self.session.execute(
            select(EvidenceRow).where(EvidenceRow.id.in_(evidence_ids))
        ).scalars()) if evidence_ids else []
        if any(row.task_id != plan.task_id or row.run_id != plan.run_id for row in evidence_rows):
            raise D1bPersistenceError("verification_run_evidence_scope_mismatch")
        for row in evidence_rows:
            metadata = _parse_json(row.metadata_json, "verification_run_evidence_invalid")
            if (
                isinstance(metadata, dict)
                and metadata.get("d1b_observation_kind") == plan.observation_kind
                and metadata.get("d1b_run_id") == plan.run_id
            ):
                return

        generic_row: EvidenceRow | None = None
        normalized_result: dict[str, Any] | None = None
        generic_metadata: dict[str, Any] | None = None
        for row in evidence_rows:
            metadata = _parse_json(row.metadata_json, "verification_run_evidence_invalid")
            if not isinstance(metadata, dict) or row.source != "runtime.codex.exec":
                continue
            raw_normalized = metadata.get("normalized_result_json")
            if not isinstance(raw_normalized, str):
                continue
            candidate_result = _parse_json(raw_normalized, "verification_runtime_result_invalid")
            if not isinstance(candidate_result, dict) or not isinstance(candidate_result.get("d1b_checks"), list):
                continue
            expected_digest = hashlib.sha256(
                json.dumps(candidate_result, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            if metadata.get("normalized_result_sha256") != expected_digest:
                raise D1bPersistenceError("verification_runtime_result_digest_mismatch")
            generic_row = row
            normalized_result = candidate_result
            generic_metadata = metadata
            break
        if generic_row is None or normalized_result is None or generic_metadata is None:
            raise D1bPersistenceError("d1b_runtime_evidence_missing")
        try:
            generic_artifact_refs = _parse_json(generic_row.artifact_refs, "verification_run_artifacts_invalid")
        except AttributeError as exc:
            raise D1bPersistenceError("verification_run_artifacts_invalid") from exc
        if not isinstance(generic_artifact_refs, list) or not generic_artifact_refs:
            raise D1bPersistenceError("verification_run_artifacts_invalid")
        generic_artifact = None
        for artifact_id in generic_artifact_refs:
            if not isinstance(artifact_id, str):
                continue
            artifact = self.session.get(ArtifactRow, artifact_id)
            if (
                artifact is not None
                and artifact.task_id == plan.task_id
                and artifact.run_id == plan.run_id
                and artifact.storage_ref == "core-blob:" + artifact.sha256
            ):
                generic_artifact = artifact
                break
        if generic_artifact is None:
            raise D1bPersistenceError("verification_runtime_artifact_missing")
        try:
            self.content_store.read(generic_artifact.sha256, generic_artifact.size)
            runner_exit = int(generic_metadata["exit_code"])
            default_cwd = generic_metadata["cwd"]
        except (ContentError, OSError, KeyError, TypeError, ValueError) as exc:
            raise D1bPersistenceError("verification_runtime_provenance_missing") from exc
        if not isinstance(default_cwd, str) or not default_cwd.strip():
            raise D1bPersistenceError("verification_runtime_provenance_missing")
        try:
            produced_evidence, produced_artifacts = produce_d1b_runtime_evidence(
                plan=plan,
                task_id=plan.task_id,
                run_id=plan.run_id,
                project_id=generic_artifact.project_id,
                normalized_result=normalized_result,
                runner_exit=runner_exit,
                default_cwd=default_cwd,
                content_store=self.content_store,
            )
        except Exception as exc:
            raise D1bPersistenceError("d1b_runtime_evidence_invalid") from exc
        if not produced_evidence or not produced_artifacts:
            raise D1bPersistenceError("d1b_runtime_evidence_missing")
        from polynexus_core.persistence.repository import SqlArtifactRepository, SqlEvidenceRepository

        for artifact in produced_artifacts:
            SqlArtifactRepository(self.session).add(artifact)
        for evidence in produced_evidence:
            SqlEvidenceRepository(self.session).add(evidence)
        self.session.flush()
        run.result_evidence_ids = _json_text([*evidence_ids, *(item.id for item in produced_evidence)])
        run.result_artifact_ids = _json_text([*artifact_ids, *(item.id for item in produced_artifacts)])
        self.session.flush()

    @staticmethod
    def _trusted_runner_name(value: str | None) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > 256:
            raise EvidenceBindingError("trusted_runner_required")
        if value.startswith("core-test:"):
            if (
                os.environ.get("POLYNEXUS_D1B_TEST_MODE") != "1"
                or os.environ.get("POLYNEXUS_ENVIRONMENT") != "TEST"
            ):
                raise EvidenceBindingError("trusted_runner_test_mode_required")
            return value
        if not value.startswith("core-runner:"):
            raise EvidenceBindingError("trusted_runner_invalid")
        if os.environ.get("POLYNEXUS_TRUSTED_RUNNER_REF") != value:
            raise EvidenceBindingError("trusted_runner_capability_invalid")
        return value

    def _validate_trusted_observation(
        self,
        observation: EvidenceObservation,
        *,
        trusted_runner: str,
    ) -> None:
        """Require runner facts and a hash-verified Core artifact.

        A caller may construct an EvidenceObservation for serialization, but
        only a Core runner boundary may persist it as verification evidence.
        The test runner uses the same checks with the explicit ``core-test:``
        namespace; normal HTTP requests never receive that capability.
        """
        if not isinstance(observation.raw_artifact_ref, str) or not observation.raw_artifact_ref.startswith("core-blob:"):
            raise EvidenceBindingError("raw_artifact_required")
        digest = observation.raw_artifact_ref.removeprefix("core-blob:")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise EvidenceBindingError("raw_artifact_ref_invalid")
        if observation.raw_artifact_sha256 != digest:
            raise EvidenceBindingError("raw_artifact_hash_mismatch")
        provenance = dict(observation.provenance)
        if provenance.get("trusted_runner") != trusted_runner:
            raise EvidenceBindingError("trusted_runner_provenance_mismatch")
        if trusted_runner.startswith("core-runner:"):
            if "runner_attestation" in provenance:
                raise EvidenceBindingError("trusted_runner_attestation_secret_forbidden")
            try:
                expected_attestation_ref = _trusted_runner_attestation_ref()
            except HumanProtocolError as exc:
                raise EvidenceBindingError("trusted_runner_attestation_required") from exc
            if provenance.get("runner_attestation_ref") != expected_attestation_ref:
                raise EvidenceBindingError("trusted_runner_attestation_required")
        if (
            not isinstance(observation.command, str)
            or not observation.command.strip()
            or not isinstance(observation.cwd, str)
            or not observation.cwd.strip()
            or not observation.argv
        ):
            raise EvidenceBindingError("execution_provenance_required")
        if observation.runner_exit is None or observation.child_exit is None:
            raise EvidenceBindingError("runner_exit_required")
        if observation.outcome is VerificationOutcome.PASS and (
            observation.runner_exit != 0 or observation.child_exit != 0
        ):
            raise EvidenceBindingError("pass_exit_mismatch")
        if self.content_store is None:
            raise EvidenceBindingError("core_content_store_required")
        try:
            artifact_path = self.content_store.root / digest
            size = artifact_path.stat().st_size
            self.content_store.read(digest, size)
        except (OSError, ContentError) as exc:
            raise EvidenceBindingError("raw_artifact_unavailable") from exc

    @staticmethod
    def _validate_offline_runner_provenance(
        runner_ref: str,
        provenance: Mapping[str, Any],
    ) -> None:
        """Re-apply the runner trust boundary while verifying a P0 bundle.

        P0 verification is intentionally independent of the row and runner
        secret that produced the bundle.  The signed receipt is the portable
        trust anchor; a production runner may carry only a public hash
        reference to its attestation in the package.
        """
        if not isinstance(runner_ref, str) or not runner_ref:
            raise P0PackageError("p0_trusted_runner_invalid")
        if runner_ref.startswith("core-runner:"):
            if "runner_attestation" in provenance:
                raise P0PackageError("p0_trusted_runner_attestation_secret_forbidden")
            attestation_ref = provenance.get("runner_attestation_ref")
            if (
                not isinstance(attestation_ref, str)
                or len(attestation_ref) != 71
                or not attestation_ref.startswith("sha256:")
                or any(char not in "0123456789abcdef" for char in attestation_ref[7:])
            ):
                raise P0PackageError("p0_trusted_runner_attestation_mismatch")
        elif not runner_ref.startswith("core-test:"):
            raise P0PackageError("p0_trusted_runner_invalid")
        if provenance.get("trusted_runner") != runner_ref:
            raise P0PackageError("p0_trusted_runner_provenance_mismatch")

    def _candidate_contract_id(self, candidate_id: str) -> str:
        return self._candidate_context(candidate_id).candidate.validation_contract_snapshot_id

    def record_evidence(
        self,
        *,
        candidate_id: str,
        contract_id: str,
        observations: Sequence[EvidenceObservation],
        trusted_runner: str | None = None,
    ) -> str:
        context = self._candidate_context(candidate_id)
        runner = self._trusted_runner_name(trusted_runner)
        if not contract_id or len(contract_id) > 256:
            raise EvidenceBindingError("contract_invalid")
        if contract_id != context.candidate.validation_contract_snapshot_id:
            raise EvidenceBindingError("validation_contract_mismatch")
        expected_checks = self._validation_checks(context)
        normalized = tuple(observations)
        evidence_ids: set[str] = set()
        for observation in normalized:
            if observation.candidate_id != candidate_id or observation.contract_id != contract_id:
                raise EvidenceBindingError("evidence_cross_candidate_or_contract")
            if observation.evidence_id in evidence_ids:
                raise EvidenceBindingError("duplicate_evidence_id")
            evidence_ids.add(observation.evidence_id)
            self._validate_trusted_observation(observation, trusted_runner=runner)
        # This validates the observed check IDs/requiredness against the
        # immutable contract without turning missing checks into a write error;
        # missing required checks remain a durable BLOCKED verification result.
        evaluate_verification(
            candidate_id,
            contract_id,
            normalized,
            expected_checks=expected_checks,
        )
        observation_values = [item.as_dict() for item in normalized]
        evidence_core = _evidence_identity(
            candidate_id=candidate_id,
            contract_id=contract_id,
            evidence_refs=[item.evidence_id for item in normalized],
            observations=observation_values,
            trusted_runner_ref=runner,
        )
        evidence_object = {
            **evidence_core,
        }
        evidence_set_id = sha256_id(canonical_json(evidence_object))
        row = self.session.get(EvidenceSetRow, evidence_set_id)
        canonical = _json_text(evidence_object)
        if row is None:
            self.session.add(EvidenceSetRow(
                evidence_set_id=evidence_set_id,
                candidate_id=candidate_id,
                contract_id=contract_id,
                trusted_runner_ref=runner,
                canonical_json=canonical,
                created_at=_db_time(),
            ))
            self.session.flush()
        elif row.canonical_json != canonical or row.trusted_runner_ref != runner:
            raise D1bPersistenceError("evidence_set_identity_conflict")
        return evidence_set_id

    def verify_candidate(
        self,
        *,
        candidate_id: str,
        contract_id: str,
        observations: Sequence[EvidenceObservation],
        trusted_runner: str | None = None,
        policy_revision: int = 1,
        verifier_principal: str = "core:d1b",
        verifier_type: str = "CORE_TRUSTED_RUNNER",
        environment: Mapping[str, Any] | None = None,
    ) -> VerificationResult:
        if policy_revision != CURRENT_POLICY_REVISION:
            raise D1bPersistenceError("verification_policy_revision_invalid")
        if not isinstance(verifier_principal, str) or not verifier_principal.strip():
            raise D1bPersistenceError("verifier_principal_invalid")
        if not isinstance(verifier_type, str) or not verifier_type.strip():
            raise D1bPersistenceError("verifier_type_invalid")
        disposition_change = self._latest_disposition_change(candidate_id)
        if disposition_change is not None:
            cutoff = _now(disposition_change.created_at)
            if any(_now(observation.observed_at) <= cutoff for observation in observations):
                raise D1bPersistenceError("fresh_evidence_required")
        started_at = _db_time()
        evidence_set_id = self.record_evidence(
            candidate_id=candidate_id,
            contract_id=contract_id,
            observations=observations,
            trusted_runner=trusted_runner,
        )
        if disposition_change is not None:
            evidence_set = self.session.get(EvidenceSetRow, evidence_set_id)
            if evidence_set is None or _now(evidence_set.created_at) <= _now(disposition_change.created_at):
                raise D1bPersistenceError("fresh_evidence_required")
        context = self._candidate_context(candidate_id)
        result = evaluate_verification(
            candidate_id,
            contract_id,
            tuple(observations),
            expected_checks=self._validation_checks(context),
        )
        completed_at = _db_time()
        self.session.add(VerificationRecordRow(
            verification_id=result.verification_id,
            evidence_set_id=evidence_set_id,
            candidate_id=candidate_id,
            contract_id=contract_id,
            requirements_snapshot_id=context.candidate.requirements_snapshot_id,
            result_json=_json_text(result.as_dict()),
            policy_revision=policy_revision,
            verifier_principal=verifier_principal,
            verifier_type=verifier_type,
            environment_json=_json_text(dict(environment or {
                "environment": os.environ.get("POLYNEXUS_ENVIRONMENT", "UNKNOWN"),
                "trusted_runner": trusted_runner,
            })),
            started_at=started_at,
            completed_at=completed_at,
            created_at=_db_time(),
        ))
        self.session.flush()
        return result

    def verify_candidate_from_run(
        self,
        *,
        candidate_id: str,
        task_id: str,
        generation_revision: int,
        run_id: str,
    ) -> VerificationResult:
        """Produce D1b evidence from a closed Core/D1a Run.

        This is the production bridge for W4.  The request supplies only the
        durable scope coordinates; observations, command facts, artifacts and
        trusted-runner provenance are read from Core-owned Run/Evidence/
        Artifact rows and the configured runner capability.
        """
        runner_ref = self._trusted_runner_name(
            os.environ.get("POLYNEXUS_TRUSTED_RUNNER_REF")
        )
        attestation_ref = _trusted_runner_attestation_ref()
        context = self._candidate_context(candidate_id)
        publication = self.session.execute(
            select(CandidatePublicationRow)
            .where(
                CandidatePublicationRow.candidate_id == candidate_id,
                CandidatePublicationRow.task_id == task_id,
                CandidatePublicationRow.generation_revision == generation_revision,
                CandidatePublicationRow.run_id == run_id,
            )
            .order_by(CandidatePublicationRow.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if publication is None:
            raise D1bPersistenceError("verification_scope_mismatch")
        self._validate_publication_scope(
            candidate=context.candidate,
            baseline_snapshot_id=context.changeset.baseline,
            result_snapshot_id=context.changeset.result,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=run_id,
            lineage_ref=publication.lineage_ref,
        )
        run = self.session.get(RunRow, run_id)
        if run is None or run.task_id != task_id or run.generation_revision != generation_revision:
            raise D1bPersistenceError("verification_scope_mismatch")
        if run.state not in {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}:
            raise D1bPersistenceError("verification_run_not_terminal")
        expected_checks = self._validation_checks(context)
        self._materialize_d1b_runtime_evidence(
            plan=build_d1b_execution_plan(
                task_id=task_id,
                generation_revision=generation_revision,
                run_id=run_id,
                candidate_id=candidate_id,
                contract_id=context.candidate.validation_contract_snapshot_id,
                result_snapshot_id=context.changeset.result,
                check_ids=tuple(item["check_id"] for item in expected_checks),
            ),
            run=run,
        )
        try:
            evidence_ids = _parse_json(run.result_evidence_ids, "verification_run_evidence_invalid")
        except AttributeError as exc:
            raise D1bPersistenceError("verification_run_evidence_invalid") from exc
        if not isinstance(evidence_ids, list) or any(not isinstance(value, str) for value in evidence_ids):
            raise D1bPersistenceError("verification_run_evidence_invalid")
        evidence_rows = list(self.session.execute(
            select(EvidenceRow)
            .where(EvidenceRow.id.in_(evidence_ids))
            .order_by(EvidenceRow.id.asc())
        ).scalars()) if evidence_ids else []
        evidence_rows = [
            row for row in evidence_rows
            if row.task_id == task_id and row.run_id == run_id
        ]
        expected_by_id = {item["check_id"]: item for item in expected_checks}
        selected: dict[str, EvidenceRow] = {}
        for row in evidence_rows:
            metadata = _parse_json(row.metadata_json, "verification_run_evidence_invalid")
            if not isinstance(metadata, dict):
                raise D1bPersistenceError("verification_run_evidence_invalid")
            explicit_check = metadata.get("d1b_check_id")
            if isinstance(explicit_check, str) and explicit_check in expected_by_id:
                if explicit_check in selected:
                    raise D1bPersistenceError("duplicate_verification_check")
                selected.setdefault(explicit_check, row)

        artifact_cache: dict[str, ArtifactRow] = {}
        observations: list[EvidenceObservation] = []
        for check in expected_checks:
            row = selected.get(check["check_id"])
            if row is None:
                continue
            metadata = _parse_json(row.metadata_json, "verification_run_evidence_invalid")
            if (
                metadata.get("d1b_candidate_id") != candidate_id
                or metadata.get("d1b_contract_id") != context.candidate.validation_contract_snapshot_id
                or metadata.get("d1b_result_snapshot_id") != context.changeset.result
                or metadata.get("d1b_task_id") != task_id
                or metadata.get("d1b_generation_revision") != generation_revision
                or metadata.get("d1b_run_id") != run_id
                or metadata.get("d1b_observation_kind") != "D1B_DETERMINISTIC_CHECK"
                or metadata.get("d1b_check_id") != check["check_id"]
            ):
                raise D1bPersistenceError("verification_run_scope_binding_missing")
            try:
                argv_value = metadata.get("argv")
                if argv_value is None:
                    argv_value = json.loads(metadata["argv_json"])
                if not isinstance(argv_value, list) or not all(isinstance(item, str) for item in argv_value):
                    raise ValueError("argv")
                runner_exit = int(metadata["exit_code"])
                child_exit = int(metadata["child_exit"])
                if not isinstance(metadata.get("cwd"), str) or not metadata["cwd"].strip():
                    raise ValueError("cwd")
                artifact_ids = _parse_json(row.artifact_refs, "verification_run_artifacts_invalid")
                if not isinstance(artifact_ids, list) or not artifact_ids:
                    raise ValueError("artifact")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise D1bPersistenceError("verification_run_provenance_missing") from exc
            artifact = None
            for artifact_id in artifact_ids:
                if not isinstance(artifact_id, str):
                    continue
                artifact = artifact_cache.get(artifact_id)
                if artifact is None:
                    artifact = self.session.get(ArtifactRow, artifact_id)
                    if artifact is not None:
                        artifact_cache[artifact_id] = artifact
                if (
                    artifact is not None
                    and artifact.task_id == task_id
                    and artifact.run_id == run_id
                    and artifact.storage_ref == "core-blob:" + artifact.sha256
                ):
                    break
                artifact = None
            if artifact is None:
                raise D1bPersistenceError("verification_run_artifact_missing")
            try:
                self.content_store.read(artifact.sha256, artifact.size)
            except (ContentError, OSError) as exc:
                raise D1bPersistenceError("verification_run_artifact_unavailable") from exc
            outcome = (
                VerificationOutcome.PASS
                if run.state == "COMPLETED" and runner_exit == 0 and child_exit == 0
                else VerificationOutcome.FAIL
            )
            observations.append(EvidenceObservation(
                candidate_id=candidate_id,
                contract_id=context.candidate.validation_contract_snapshot_id,
                check_id=check["check_id"],
                evidence_type=row.type,
                actor_id=row.actor_id,
                source=row.source,
                requiredness=Requiredness(check["requiredness"]),
                applicability=Applicability(check["applicability"]),
                outcome=outcome,
                validity=Validity.VALID,
                command=json.dumps(argv_value, ensure_ascii=False, separators=(",", ":")),
                cwd=metadata["cwd"],
                argv=tuple(argv_value),
                runner_exit=runner_exit,
                child_exit=child_exit,
                raw_artifact_ref="core-blob:" + artifact.sha256,
                raw_artifact_sha256=artifact.sha256,
                freshness="CURRENT",
                provenance={
                    "trusted_runner": runner_ref,
                    "runner_attestation_ref": attestation_ref,
                    "task_id": task_id,
                    "generation_revision": generation_revision,
                    "run_id": run_id,
                    "source_evidence_id": row.id,
                    "execution_id": metadata.get("execution_id", run_id),
                    "review_role": "SELF",
                },
                observed_at=row.observed_at,
            ))
        return self.verify_candidate(
            candidate_id=candidate_id,
            contract_id=context.candidate.validation_contract_snapshot_id,
            observations=observations,
            trusted_runner=runner_ref,
            verifier_principal="core:d1b:generation-run",
            verifier_type="CORE_GENERATION_RUN",
            environment={
                "task_id": task_id,
                "generation_revision": generation_revision,
                "run_id": run_id,
                "publication_id": publication.publication_id,
            },
        )

    def create_cross_review_run(
        self,
        *,
        candidate_id: str,
        task_id: str,
        generation_revision: int,
        target_run_id: str,
    ):
        """Create a Core-owned, pre-bound reviewer Run identity.

        The reviewer runtime reference is issued here from the configured
        reviewer capability.  Callers cannot choose the reviewer identity or
        parent scope; the returned CREATED Run is the only input accepted by
        the reviewer dispatch boundary.
        """

        configured_reviewer = os.environ.get("POLYNEXUS_CROSS_REVIEWER_REF", "")
        if not isinstance(configured_reviewer, str) or not configured_reviewer.strip():
            raise D1bPersistenceError("cross_reviewer_not_configured")
        context = self._candidate_context(candidate_id)
        publication = self.session.execute(
            select(CandidatePublicationRow)
            .where(
                CandidatePublicationRow.candidate_id == candidate_id,
                CandidatePublicationRow.task_id == task_id,
                CandidatePublicationRow.generation_revision == generation_revision,
                CandidatePublicationRow.run_id == target_run_id,
            )
            .order_by(CandidatePublicationRow.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        target_run = self.session.get(RunRow, target_run_id)
        if publication is None or target_run is None:
            raise D1bPersistenceError("cross_review_target_missing")
        self._validate_publication_scope(
            candidate=context.candidate,
            baseline_snapshot_id=context.changeset.baseline,
            result_snapshot_id=context.changeset.result,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=target_run_id,
            lineage_ref=publication.lineage_ref,
        )
        if target_run.state not in {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}:
            raise D1bPersistenceError("cross_review_target_missing")
        target_verification = None
        for row in self.session.execute(
            select(VerificationRecordRow)
            .where(
                VerificationRecordRow.candidate_id == candidate_id,
                VerificationRecordRow.contract_id == context.candidate.validation_contract_snapshot_id,
                VerificationRecordRow.verifier_type == "CORE_GENERATION_RUN",
            )
            .order_by(VerificationRecordRow.created_at.desc())
        ).scalars():
            environment = _parse_json(row.environment_json, "verification_environment_invalid")
            if (
                isinstance(environment, dict)
                and environment.get("task_id") == task_id
                and environment.get("generation_revision") == generation_revision
                and environment.get("run_id") == target_run_id
                and environment.get("publication_id") == publication.publication_id
            ):
                target_verification = self._verification_from_row(row, candidate_id=candidate_id)[1]
                break
        if target_verification is None or not target_verification.acceptance_eligible:
            raise D1bPersistenceError("cross_review_target_not_eligible")
        target_claim = self.session.execute(
            text(
                "SELECT lineage, released FROM generation_writer_claims "
                "WHERE task_id=:task AND revision=:revision AND run_id=:run"
            ),
            {"task": task_id, "revision": generation_revision, "run": target_run_id},
        ).mappings().one_or_none()
        if target_claim is None or target_claim["released"] != 1 or target_claim["lineage"] != publication.lineage_ref:
            raise D1bPersistenceError("cross_review_target_writer_not_quiescent")
        task = self.session.get(TaskRow, task_id)
        if task is None:
            raise D1bPersistenceError("cross_review_target_missing")
        from polynexus_core.domain.models import Run
        from polynexus_core.persistence.repository import SqlRunRepository

        reviewer_run = Run(
            task_id=task_id,
            workflow_id=target_run.workflow_id,
            workflow_version=target_run.workflow_version,
            context_package_id=target_run.context_package_id,
            generation_revision=generation_revision,
            generation_parent_run_id=target_run_id,
            runtime_ref="cross-reviewer:" + configured_reviewer,
        )
        SqlRunRepository(self.session).add(reviewer_run)
        self.session.flush()
        return reviewer_run

    def verify_candidate_cross_review_from_run(
        self,
        *,
        candidate_id: str,
        task_id: str,
        generation_revision: int,
        run_id: str | None = None,
        reviewer_run_id: str,
    ) -> VerificationResult:
        """Persist a cross-review derived only from a closed Core reviewer Run.

        The request carries only the target publication coordinates and the
        reviewer Run identity.  The target Verification/EvidenceSet and the
        reviewer command, exit facts, artifacts, profile and reviewer actor
        are all resolved from immutable Core rows plus the configured trust
        boundary.  No caller-supplied review claim is accepted.
        """
        runner_ref = self._trusted_runner_name(
            os.environ.get("POLYNEXUS_TRUSTED_RUNNER_REF")
        )
        attestation_ref = _trusted_runner_attestation_ref()
        configured_reviewer = os.environ.get("POLYNEXUS_CROSS_REVIEWER_REF", "")
        if not isinstance(configured_reviewer, str) or not configured_reviewer.strip():
            raise D1bPersistenceError("cross_reviewer_not_configured")
        context = self._candidate_context(candidate_id)
        if run_id is None:
            candidate_verifications = self.session.execute(
                select(VerificationRecordRow)
                .where(
                    VerificationRecordRow.candidate_id == candidate_id,
                    VerificationRecordRow.contract_id == context.candidate.validation_contract_snapshot_id,
                    VerificationRecordRow.verifier_type == "CORE_GENERATION_RUN",
                )
                .order_by(VerificationRecordRow.created_at.desc())
            ).scalars()
            for candidate_verification in candidate_verifications:
                environment = _parse_json(
                    candidate_verification.environment_json,
                    "verification_environment_invalid",
                )
                if (
                    isinstance(environment, dict)
                    and environment.get("task_id") == task_id
                    and environment.get("generation_revision") == generation_revision
                    and isinstance(environment.get("run_id"), str)
                ):
                    run_id = environment["run_id"]
                    break
        if not isinstance(run_id, str) or not run_id.strip():
            raise D1bPersistenceError("cross_review_target_missing")
        publication = self.session.execute(
            select(CandidatePublicationRow)
            .where(
                CandidatePublicationRow.candidate_id == candidate_id,
                CandidatePublicationRow.task_id == task_id,
                CandidatePublicationRow.generation_revision == generation_revision,
                CandidatePublicationRow.run_id == run_id,
            )
            .order_by(CandidatePublicationRow.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if publication is None:
            raise D1bPersistenceError("verification_scope_mismatch")
        self._validate_publication_scope(
            candidate=context.candidate,
            baseline_snapshot_id=context.changeset.baseline,
            result_snapshot_id=context.changeset.result,
            task_id=task_id,
            generation_revision=generation_revision,
            run_id=run_id,
            lineage_ref=publication.lineage_ref,
        )
        target_run = self.session.get(RunRow, run_id)
        if (
            target_run is None
            or target_run.task_id != task_id
            or target_run.generation_revision != generation_revision
            or target_run.state not in {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}
        ):
            raise D1bPersistenceError("verification_scope_mismatch")

        target_verification_row = None
        target_result = None
        target_environment: dict[str, Any] | None = None
        target_candidates = self.session.execute(
            select(VerificationRecordRow)
            .where(
                VerificationRecordRow.candidate_id == candidate_id,
                VerificationRecordRow.contract_id == context.candidate.validation_contract_snapshot_id,
            )
            .order_by(VerificationRecordRow.created_at.desc())
        ).scalars()
        for candidate_verification in target_candidates:
            if candidate_verification.verifier_type != "CORE_GENERATION_RUN":
                continue
            environment = _parse_json(
                candidate_verification.environment_json,
                "verification_environment_invalid",
            )
            if not isinstance(environment, dict):
                continue
            if (
                environment.get("task_id") != task_id
                or environment.get("generation_revision") != generation_revision
                or environment.get("run_id") != run_id
                or environment.get("publication_id") != publication.publication_id
            ):
                continue
            target_verification_row, target_result = self._verification_from_row(
                candidate_verification,
                candidate_id=candidate_id,
            )
            target_environment = environment
            break
        if target_verification_row is None or target_result is None or target_environment is None:
            raise D1bPersistenceError("cross_review_target_missing")
        if not target_result.acceptance_eligible:
            raise D1bPersistenceError("cross_review_target_not_eligible")
        target_evidence = self.session.get(EvidenceSetRow, target_verification_row.evidence_set_id)
        if target_evidence is None or not target_evidence.trusted_runner_ref:
            raise D1bPersistenceError("cross_review_target_evidence_missing")
        target_evidence_value = _parse_json(
            target_evidence.canonical_json,
            "evidence_set_json_invalid",
        )
        if not isinstance(target_evidence_value, dict):
            raise D1bPersistenceError("cross_review_target_evidence_invalid")
        target_observation_ids = {
            item.get("evidence_id")
            for item in target_evidence_value.get("observations", [])
            if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
        }
        if not target_observation_ids:
            raise D1bPersistenceError("cross_review_target_evidence_missing")

        reviewer_run = self.session.get(RunRow, reviewer_run_id)
        if (
            reviewer_run is None
            or reviewer_run.id == run_id
            or reviewer_run.task_id != task_id
            or reviewer_run.generation_revision != generation_revision
            or reviewer_run.state not in {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}
            or reviewer_run.updated_at < publication.created_at
            or reviewer_run.updated_at < target_verification_row.created_at
            or reviewer_run.generation_parent_run_id != run_id
            or reviewer_run.runtime_ref != "cross-reviewer:" + configured_reviewer
        ):
            raise D1bPersistenceError("cross_review_scope_mismatch")
        target_claim = self.session.execute(
            text(
                "SELECT lineage, released FROM generation_writer_claims "
                "WHERE task_id=:task AND revision=:revision AND run_id=:run"
            ),
            {"task": task_id, "revision": generation_revision, "run": run_id},
        ).mappings().one_or_none()
        if (
            target_claim is None
            or target_claim["released"] != 1
            or target_claim["lineage"] != publication.lineage_ref
        ):
            raise D1bPersistenceError("cross_review_target_writer_not_quiescent")
        expected_checks = self._validation_checks(context)
        contract_revision = self._validation_contract_value(context).get("revision")
        self._materialize_d1b_runtime_evidence(
            plan=build_d1b_execution_plan(
                task_id=task_id,
                generation_revision=generation_revision,
                run_id=reviewer_run_id,
                candidate_id=candidate_id,
                contract_id=context.candidate.validation_contract_snapshot_id,
                result_snapshot_id=context.changeset.result,
                check_ids=tuple(item["check_id"] for item in expected_checks),
                observation_kind="D1B_CROSS_REVIEW",
                reviewer_ref=configured_reviewer,
                reviewer_profile_ref=context.candidate.validation_contract_snapshot_id,
                reviewer_profile_revision=contract_revision,
                reviewed_candidate_id=candidate_id,
                reviewed_contract_id=context.candidate.validation_contract_snapshot_id,
                reviewed_verification_id=target_verification_row.verification_id,
                reviewed_evidence_set_id=target_verification_row.evidence_set_id,
                reviewed_evidence_id=sorted(target_observation_ids)[0],
            ),
            run=reviewer_run,
        )

        try:
            reviewer_evidence_ids = _parse_json(
                reviewer_run.result_evidence_ids,
                "cross_review_evidence_invalid",
            )
        except AttributeError as exc:
            raise D1bPersistenceError("cross_review_evidence_invalid") from exc
        if not isinstance(reviewer_evidence_ids, list) or any(
            not isinstance(value, str) for value in reviewer_evidence_ids
        ):
            raise D1bPersistenceError("cross_review_evidence_invalid")
        reviewer_evidence_rows = list(self.session.execute(
            select(EvidenceRow)
            .where(EvidenceRow.id.in_(reviewer_evidence_ids))
            .order_by(EvidenceRow.id.asc())
        ).scalars()) if reviewer_evidence_ids else []
        reviewer_evidence_rows = [
            row for row in reviewer_evidence_rows
            if row.task_id == task_id and row.run_id == reviewer_run_id
        ]
        expected_by_id = {item["check_id"]: item for item in expected_checks}
        selected: dict[str, EvidenceRow] = {}
        for row in reviewer_evidence_rows:
            metadata = _parse_json(row.metadata_json, "cross_review_evidence_invalid")
            if not isinstance(metadata, dict):
                raise D1bPersistenceError("cross_review_evidence_invalid")
            check_id = metadata.get("d1b_check_id")
            if isinstance(check_id, str) and check_id in expected_by_id:
                if check_id in selected:
                    raise D1bPersistenceError("duplicate_cross_review_check")
                selected[check_id] = row

        artifact_cache: dict[str, ArtifactRow] = {}
        observations: list[EvidenceObservation] = []
        for check in expected_checks:
            row = selected.get(check["check_id"])
            if row is None:
                continue
            metadata = _parse_json(row.metadata_json, "cross_review_evidence_invalid")
            reviewed_evidence_id = metadata.get("reviewed_evidence_id")
            if (
                metadata.get("d1b_candidate_id") != candidate_id
                or metadata.get("d1b_contract_id") != context.candidate.validation_contract_snapshot_id
                or metadata.get("d1b_result_snapshot_id") != context.changeset.result
                or metadata.get("d1b_task_id") != task_id
                or metadata.get("d1b_generation_revision") != generation_revision
                or metadata.get("d1b_run_id") != reviewer_run_id
                or metadata.get("d1b_observation_kind") != "D1B_CROSS_REVIEW"
                or metadata.get("d1b_check_id") != check["check_id"]
                or metadata.get("reviewer_ref") != configured_reviewer
                or metadata.get("reviewed_candidate_id") != candidate_id
                or metadata.get("reviewed_contract_id") != context.candidate.validation_contract_snapshot_id
                or metadata.get("reviewed_verification_id") != target_verification_row.verification_id
                or metadata.get("reviewed_evidence_set_id") != target_verification_row.evidence_set_id
                or not isinstance(reviewed_evidence_id, str)
                or reviewed_evidence_id not in target_observation_ids
                or metadata.get("reviewer_profile_ref") != context.candidate.validation_contract_snapshot_id
                or metadata.get("reviewer_profile_revision") != contract_revision
            ):
                raise D1bPersistenceError("cross_review_binding_missing")
            try:
                argv_value = metadata.get("argv")
                if argv_value is None:
                    argv_value = json.loads(metadata["argv_json"])
                if not isinstance(argv_value, list) or not all(isinstance(item, str) for item in argv_value):
                    raise ValueError("argv")
                runner_exit = int(metadata["exit_code"])
                child_exit = int(metadata["child_exit"])
                if not isinstance(metadata.get("cwd"), str) or not metadata["cwd"].strip():
                    raise ValueError("cwd")
                artifact_ids = _parse_json(row.artifact_refs, "cross_review_artifacts_invalid")
                if not isinstance(artifact_ids, list) or not artifact_ids:
                    raise ValueError("artifact")
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise D1bPersistenceError("cross_review_provenance_missing") from exc
            artifact = None
            for artifact_id in artifact_ids:
                if not isinstance(artifact_id, str):
                    continue
                artifact = artifact_cache.get(artifact_id)
                if artifact is None:
                    artifact = self.session.get(ArtifactRow, artifact_id)
                    if artifact is not None:
                        artifact_cache[artifact_id] = artifact
                if (
                    artifact is not None
                    and artifact.task_id == task_id
                    and artifact.run_id == reviewer_run_id
                    and artifact.storage_ref == "core-blob:" + artifact.sha256
                ):
                    break
                artifact = None
            if artifact is None:
                raise D1bPersistenceError("cross_review_artifact_missing")
            try:
                self.content_store.read(artifact.sha256, artifact.size)
            except (ContentError, OSError) as exc:
                raise D1bPersistenceError("cross_review_artifact_unavailable") from exc
            outcome = (
                VerificationOutcome.PASS
                if reviewer_run.state == "COMPLETED" and runner_exit == 0 and child_exit == 0
                else VerificationOutcome.FAIL
            )
            observations.append(EvidenceObservation(
                candidate_id=candidate_id,
                contract_id=context.candidate.validation_contract_snapshot_id,
                check_id=check["check_id"],
                evidence_type=row.type,
                actor_id=row.actor_id,
                source=row.source,
                requiredness=Requiredness(check["requiredness"]),
                applicability=Applicability(check["applicability"]),
                outcome=outcome,
                validity=Validity.VALID,
                command=json.dumps(argv_value, ensure_ascii=False, separators=(",", ":")),
                cwd=metadata["cwd"],
                argv=tuple(argv_value),
                runner_exit=runner_exit,
                child_exit=child_exit,
                raw_artifact_ref="core-blob:" + artifact.sha256,
                raw_artifact_sha256=artifact.sha256,
                freshness="CURRENT",
                provenance={
                    "trusted_runner": runner_ref,
                    "runner_attestation_ref": attestation_ref,
                    "task_id": task_id,
                    "generation_revision": generation_revision,
                    "run_id": reviewer_run_id,
                    "source_evidence_id": row.id,
                    "execution_id": metadata.get("execution_id", reviewer_run_id),
                    "review_role": "CROSS",
                    "reviewer_ref": configured_reviewer,
                    "reviewer_run_id": reviewer_run_id,
                    "reviewed_candidate_id": candidate_id,
                    "reviewed_contract_id": context.candidate.validation_contract_snapshot_id,
                    "reviewed_verification_id": target_verification_row.verification_id,
                    "reviewed_evidence_set_id": target_verification_row.evidence_set_id,
                    "reviewed_evidence_id": reviewed_evidence_id,
                    "reviewer_profile_ref": context.candidate.validation_contract_snapshot_id,
                    "reviewer_profile_revision": contract_revision,
                    "independent": True,
                },
                observed_at=row.observed_at,
            ))
        return self.verify_candidate(
            candidate_id=candidate_id,
            contract_id=context.candidate.validation_contract_snapshot_id,
            observations=observations,
            trusted_runner=runner_ref,
            verifier_principal="core:d1b:cross-review-run",
            verifier_type="CORE_CROSS_REVIEW_RUN",
            environment={
                "task_id": task_id,
                "generation_revision": generation_revision,
                "run_id": reviewer_run_id,
                "reviewed_run_id": run_id,
                "reviewer_run_id": reviewer_run_id,
                "reviewed_verification_id": target_verification_row.verification_id,
                "publication_id": publication.publication_id,
            },
        )

    def _verification_from_row(
        self,
        row: VerificationRecordRow,
        *,
        candidate_id: str | None = None,
    ) -> tuple[VerificationRecordRow, VerificationResult]:
        value = _parse_json(row.result_json, "verification_json_invalid")
        try:
            result = VerificationResult(
                candidate_id=value["candidate_id"],
                contract_id=value["contract_id"],
                outcome=value["outcome"],
                validity=Validity(value["validity"]),
                mandatory_pass=bool(value["mandatory_pass"]),
                complete=bool(value["complete"]),
                failures=tuple(value.get("failures", [])),
                optional_failures=tuple(value.get("optional_failures", [])),
                verification_id=value["verification_id"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise D1bPersistenceError("verification_json_invalid") from exc
        if (
            (candidate_id is not None and row.candidate_id != candidate_id)
            or row.contract_id != result.contract_id
            or (candidate_id is not None and result.candidate_id != candidate_id)
            or result.verification_id != row.verification_id
        ):
            raise D1bPersistenceError("verification_identity_mismatch")
        evidence = self.session.get(EvidenceSetRow, row.evidence_set_id)
        candidate_row = self.session.get(CandidateRow, row.candidate_id)
        if (
            evidence is None
            or evidence.candidate_id != row.candidate_id
            or evidence.contract_id != result.contract_id
            or candidate_row is None
            or row.requirements_snapshot_id != candidate_row.requirements_snapshot_id
        ):
            raise D1bPersistenceError("verification_evidence_binding_mismatch")
        return row, result

    def _latest_verification(self, candidate_id: str) -> tuple[VerificationRecordRow, VerificationResult] | None:
        row = self.session.execute(
            select(VerificationRecordRow)
            .where(VerificationRecordRow.candidate_id == candidate_id)
            .order_by(VerificationRecordRow.created_at.desc(), VerificationRecordRow.verification_id.desc())
            .limit(1)
        ).scalar_one_or_none()
        if row is None:
            return None
        parsed = self._verification_from_row(row, candidate_id=candidate_id)
        return parsed

    def _verification_by_id(self, verification_id: str) -> tuple[VerificationRecordRow, VerificationResult]:
        row = self.session.get(VerificationRecordRow, verification_id)
        if row is None:
            raise D1bPersistenceError("verification_not_found")
        return self._verification_from_row(row)

    def _review_facts(self, evidence_set_id: str | None) -> tuple[bool, bool]:
        if evidence_set_id is None:
            return False, False
        row = self.session.get(EvidenceSetRow, evidence_set_id)
        if row is None or not row.trusted_runner_ref:
            raise D1bPersistenceError("trusted_evidence_required")
        value = _parse_json(row.canonical_json, "evidence_set_json_invalid")
        observations = value.get("observations") if isinstance(value, dict) else None
        if not isinstance(observations, list):
            raise D1bPersistenceError("evidence_set_json_invalid")
        context = self._candidate_context(row.candidate_id)
        contract = self._validation_contract_value(context)
        configured_reviewer = os.environ.get("POLYNEXUS_CROSS_REVIEWER_REF", "")
        self_review = False
        cross_review = False
        for observation in observations:
            if not isinstance(observation, dict):
                raise D1bPersistenceError("evidence_set_json_invalid")
            provenance = observation.get("provenance")
            if not isinstance(provenance, dict):
                raise D1bPersistenceError("evidence_provenance_invalid")
            role = str(provenance.get("review_role", "")).upper()
            evidence_type = str(observation.get("evidence_type", "")).upper()
            if role == "SELF" or evidence_type == "SELF_REVIEW":
                self_review = True
            if role == "CROSS" or evidence_type == "CROSS_REVIEW":
                reviewer_ref = provenance.get("reviewer_ref")
                reviewer_run_id = provenance.get("reviewer_run_id")
                reviewer_run = (
                    self.session.get(RunRow, reviewer_run_id)
                    if isinstance(reviewer_run_id, str) and reviewer_run_id
                    else None
                )
                candidate_revision = contract.get("revision")
                profile_ok = (
                    provenance.get("reviewer_profile_ref")
                    == context.candidate.validation_contract_snapshot_id
                    and provenance.get("reviewer_profile_revision") == candidate_revision
                )
                reviewed_evidence_set_id = provenance.get("reviewed_evidence_set_id")
                reviewed_verification_id = provenance.get("reviewed_verification_id")
                reviewed_evidence_id = provenance.get("reviewed_evidence_id")
                target_evidence = (
                    self.session.get(EvidenceSetRow, reviewed_evidence_set_id)
                    if isinstance(reviewed_evidence_set_id, str) and reviewed_evidence_set_id
                    else None
                )
                target_verification_row = None
                target_verification = None
                if isinstance(reviewed_verification_id, str) and reviewed_verification_id:
                    try:
                        target_verification_row, target_verification = self._verification_by_id(
                            reviewed_verification_id
                        )
                    except D1bPersistenceError:
                        target_verification_row = None
                        target_verification = None
                target_evidence_value = None
                if target_evidence is not None:
                    target_evidence_value = _parse_json(
                        target_evidence.canonical_json,
                        "evidence_set_json_invalid",
                    )
                target_observation_ids = {
                    item.get("evidence_id")
                    for item in (
                        target_evidence_value.get("observations", [])
                        if isinstance(target_evidence_value, dict)
                        else []
                    )
                    if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)
                }
                target_environment = None
                target_run = None
                target_publication = None
                if target_verification_row is not None:
                    target_environment = _parse_json(
                        target_verification_row.environment_json,
                        "verification_environment_invalid",
                    )
                if isinstance(target_environment, dict):
                    target_run_id = target_environment.get("run_id")
                    publication_id = target_environment.get("publication_id")
                    if isinstance(target_run_id, str):
                        target_run = self.session.get(RunRow, target_run_id)
                    if isinstance(publication_id, str):
                        target_publication = self.session.get(CandidatePublicationRow, publication_id)
                target_binding_ok = (
                    target_evidence is not None
                    and target_evidence.candidate_id == row.candidate_id
                    and target_evidence.contract_id == row.contract_id
                    and target_evidence.evidence_set_id == reviewed_evidence_set_id
                    and target_verification_row is not None
                    and target_verification is not None
                    and target_verification_row.candidate_id == row.candidate_id
                    and target_verification_row.contract_id == row.contract_id
                    and target_verification_row.evidence_set_id == reviewed_evidence_set_id
                    and target_verification_row.verifier_type == "CORE_GENERATION_RUN"
                    and target_verification_row.created_at < row.created_at
                    and isinstance(reviewed_evidence_id, str)
                    and reviewed_evidence_id in target_observation_ids
                    and isinstance(target_environment, dict)
                    and target_environment.get("task_id") is not None
                    and target_environment.get("generation_revision") is not None
                    and target_environment.get("run_id") is not None
                    and target_environment.get("publication_id") is not None
                    and target_publication is not None
                    and target_publication.candidate_id == row.candidate_id
                    and target_publication.task_id == target_environment.get("task_id")
                    and target_publication.generation_revision == target_environment.get("generation_revision")
                    and target_publication.run_id == target_environment.get("run_id")
                    and target_run is not None
                    and target_run.task_id == target_publication.task_id
                    and target_run.generation_revision == target_publication.generation_revision
                )
                reviewer_scope_ok = False
                target_claim = None
                if reviewer_run is not None and target_binding_ok:
                    target_claim = self.session.execute(
                        text(
                            "SELECT lineage, released FROM generation_writer_claims "
                            "WHERE task_id=:task AND revision=:revision AND run_id=:run"
                        ),
                        {
                            "task": target_publication.task_id,
                            "revision": target_publication.generation_revision,
                            "run": target_publication.run_id,
                        },
                    ).mappings().one_or_none()
                    reviewer_scope_ok = bool(
                        target_publication is not None
                        and target_publication.task_id is not None
                        and target_publication.generation_revision is not None
                        and target_publication.run_id is not None
                        and reviewer_run.task_id == target_publication.task_id
                        and reviewer_run.generation_revision == target_publication.generation_revision
                        and reviewer_run.id != target_publication.run_id
                        and reviewer_run.state in {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}
                        and reviewer_run.updated_at >= target_publication.created_at
                        and target_verification_row is not None
                        and reviewer_run.updated_at >= target_verification_row.created_at
                        and reviewer_run.generation_parent_run_id == target_publication.run_id
                        and reviewer_run.runtime_ref == "cross-reviewer:" + configured_reviewer
                        and target_claim is not None
                        and target_claim["released"] == 1
                        and target_claim["lineage"] == target_publication.lineage_ref
                    )
                if (
                    isinstance(configured_reviewer, str)
                    and configured_reviewer.strip()
                    and isinstance(reviewer_ref, str)
                    and reviewer_ref == configured_reviewer
                    and reviewer_ref != row.trusted_runner_ref
                    and isinstance(reviewer_run_id, str)
                    and provenance.get("reviewed_candidate_id") == row.candidate_id
                    and provenance.get("reviewed_contract_id") == row.contract_id
                    and profile_ok
                    and target_binding_ok
                    and reviewer_scope_ok
                ):
                    cross_review = True
        return self_review, cross_review

    def _profile_satisfied(
        self,
        mode: AssuranceMode,
        profile_ref: str | None,
        profile_revision: int | None,
        context: CandidateContext,
    ) -> bool:
        if mode is AssuranceMode.FLEXIBLE:
            if (profile_ref is None) != (profile_revision is None):
                raise D1bPersistenceError("assurance_profile_incomplete")
            return True
        if (
            not isinstance(profile_ref, str)
            or not profile_ref.strip()
            or not isinstance(profile_revision, int)
            or isinstance(profile_revision, bool)
            or profile_revision < 0
        ):
            raise D1bPersistenceError("assurance_profile_required")
        if profile_ref != context.candidate.validation_contract_snapshot_id:
            raise D1bPersistenceError("assurance_profile_target_mismatch")
        contract = self._validation_contract_value(context)
        if contract.get("revision") != profile_revision:
            raise D1bPersistenceError("assurance_profile_revision_mismatch")
        return True

    def append_assurance(
        self,
        *,
        candidate_id: str,
        mode: AssuranceMode,
        target_type: str = "CANDIDATE",
        target_id: str | None = None,
        profile_ref: str | None = None,
        profile_revision: int | None = None,
        self_review: bool = False,
        cross_review: bool = False,
        reason: str = "derived_from_current_evidence",
    ) -> dict[str, Any]:
        context = self._candidate_context(candidate_id)
        if not isinstance(mode, AssuranceMode):
            raise D1bPersistenceError("assurance_mode_invalid")
        if mode is not self._assurance_mode(context):
            raise D1bPersistenceError("assurance_mode_mismatch")
        if target_type != "CANDIDATE" or (target_id is not None and target_id != candidate_id):
            raise D1bPersistenceError("assurance_target_mismatch")
        if not reason:
            raise D1bPersistenceError("assurance_reason_missing")
        if self_review or cross_review:
            raise D1bPersistenceError("caller_review_flags_rejected")
        latest = self._latest_verification(candidate_id)
        verification = latest[1] if latest else None
        profile_satisfied = self._profile_satisfied(mode, profile_ref, profile_revision, context)
        derived_self_review, derived_cross_review = self._review_facts(
            latest[0].evidence_set_id if latest else None
        )
        status = self._derived_assurance_status(
            context,
            mode,
            self_review=derived_self_review,
            cross_review=derived_cross_review,
            verification=verification,
            profile_satisfied=profile_satisfied,
        )
        max_revision = self.session.execute(
            select(func.max(AssuranceAssessmentRow.revision))
            .where(AssuranceAssessmentRow.candidate_id == candidate_id)
        ).scalar_one()
        revision = int(max_revision or 0) + 1
        row = AssuranceAssessmentRow(
            assessment_id=_random_id("assessment"),
            target_type=target_type,
            target_id=target_id or candidate_id,
            candidate_id=candidate_id,
            mode=mode.value,
            profile_ref=profile_ref,
            profile_revision=profile_revision,
            status=status.value,
            outcome=verification.outcome if verification else "UNREVIEWED",
            validity=verification.validity.value if verification else Validity.INVALID.value,
            reason=reason,
            verification_id=latest[0].verification_id if latest else None,
            evidence_set_id=latest[0].evidence_set_id if latest else None,
            revision=revision,
            created_at=_db_time(),
        )
        self.session.add(row)
        self.session.flush()
        return {
            "assessment_id": row.assessment_id,
            "candidate_id": candidate_id,
            "mode": row.mode,
            "status": row.status,
            "outcome": row.outcome,
            "validity": row.validity,
            "revision": revision,
            "verification_id": row.verification_id,
            "evidence_set_id": row.evidence_set_id,
        }

    def _latest_assurance(self, candidate_id: str) -> AssuranceAssessmentRow | None:
        return self.session.execute(
            select(AssuranceAssessmentRow)
            .where(AssuranceAssessmentRow.candidate_id == candidate_id)
            .order_by(AssuranceAssessmentRow.revision.desc())
            .limit(1)
        ).scalar_one_or_none()

    def _assurance_requires_cross_review(
        self,
        context: CandidateContext,
        mode: AssuranceMode,
    ) -> bool:
        """Return the immutable contract's independent-review obligation."""
        if mode is AssuranceMode.STANDARD:
            return True
        policy = self._validation_contract_value(context).get("assurance")
        review = policy.get("review") if isinstance(policy, Mapping) else None
        return isinstance(review, Mapping) and review.get("cross_review_required") is True

    def _derived_assurance_status(
        self,
        context: CandidateContext,
        mode: AssuranceMode,
        *,
        self_review: bool,
        cross_review: bool,
        verification: VerificationResult | None,
        profile_satisfied: bool,
    ) -> AssuranceStatus:
        status = derive_assurance_status(
            mode,
            self_review=self_review,
            cross_review=cross_review,
            verification=verification,
            review_profile_satisfied=profile_satisfied,
        )
        # A contract may add a cross-review obligation to VERIFIED.  The
        # deterministic result remains independent from the review depth, but
        # VERIFIED status is withheld until that immutable obligation is met.
        if (
            mode is AssuranceMode.VERIFIED
            and self._assurance_requires_cross_review(context, mode)
            and not cross_review
        ):
            return AssuranceStatus.SELF_REVIEWED if self_review else AssuranceStatus.UNREVIEWED
        return status

    def _ensure_current_assurance(
        self,
        candidate_id: str,
        latest_verification: tuple[VerificationRecordRow, VerificationResult] | None,
    ) -> tuple[AssuranceAssessmentRow, AssuranceMode]:
        """Persist a Core-derived assessment for the exact current evidence."""
        context = self._candidate_context(candidate_id)
        mode = self._assurance_mode(context)
        verification_id = latest_verification[0].verification_id if latest_verification else None
        evidence_set_id = latest_verification[0].evidence_set_id if latest_verification else None
        contract = self._validation_contract_value(context)
        profile_ref = None if mode is AssuranceMode.FLEXIBLE else context.candidate.validation_contract_snapshot_id
        profile_revision = None if mode is AssuranceMode.FLEXIBLE else contract["revision"]
        profile_satisfied = self._profile_satisfied(mode, profile_ref, profile_revision, context)
        self_review, cross_review = self._review_facts(evidence_set_id)
        status = self._derived_assurance_status(
            context,
            mode,
            self_review=self_review,
            cross_review=cross_review,
            verification=latest_verification[1] if latest_verification else None,
            profile_satisfied=profile_satisfied,
        )
        current = self._latest_assurance(candidate_id)
        if current is not None and (
            current.target_type == "CANDIDATE"
            and current.target_id == candidate_id
            and current.mode == mode.value
            and current.profile_ref == profile_ref
            and current.profile_revision == profile_revision
            and current.status == status.value
            and current.verification_id == verification_id
            and current.evidence_set_id == evidence_set_id
        ):
            return current, mode
        self.append_assurance(
            candidate_id=candidate_id,
            mode=mode,
            profile_ref=profile_ref,
            profile_revision=profile_revision,
            reason="derived_for_current_candidate_evidence",
        )
        current = self._latest_assurance(candidate_id)
        if current is None:
            raise D1bPersistenceError("assurance_assessment_missing")
        return current, mode

    # ------------------------------------------------------------------
    # Exact candidate views and append-only Human decision protocol
    # ------------------------------------------------------------------

    def _decision_history(self, candidate_id: str) -> list[HumanDecisionEventRow]:
        return list(self.session.execute(
            select(HumanDecisionEventRow)
            .where(HumanDecisionEventRow.candidate_id == candidate_id)
            .order_by(HumanDecisionEventRow.revision.asc())
        ).scalars())

    def _latest_disposition_change(self, candidate_id: str) -> HumanDecisionEventRow | None:
        return next(
            (
                row
                for row in reversed(self._decision_history(candidate_id))
                if row.action in {"Revoke", "Supersede"}
            ),
            None,
        )

    def _current_disposition(self, candidate_id: str) -> tuple[str, str | None]:
        history = self._decision_history(candidate_id)
        if not history:
            return "NEED_ACTION", None
        latest = history[-1]
        if latest.action == "Accept":
            return "ACCEPTED", latest.acceptance_id
        if latest.action == "Reject":
            return "REJECTED", None
        if latest.action == "Revoke":
            return "REVOKED", latest.prior_acceptance_id
        if latest.action == "Supersede":
            return "SUPERSEDED", latest.replacement_acceptance_id
        raise HumanProtocolError("decision_action_invalid")

    def _decision_view_item(self, row: HumanDecisionEventRow) -> dict[str, Any]:
        protocol_evidence = None
        if row.protocol_evidence_json is not None:
            protocol_evidence = _parse_json(
                row.protocol_evidence_json, "decision_protocol_evidence_invalid"
            )
        return {
            "action": row.action,
            "acceptance_id": row.acceptance_id,
            "challenge_id": row.challenge_id,
            "decision_id": row.decision_id,
            "created_at": _display_time(row.created_at),
            "prior_acceptance_id": row.prior_acceptance_id,
            "principal_ref": row.principal_ref,
            "protocol_evidence": protocol_evidence,
            "reason": row.reason,
            "replacement_acceptance_id": row.replacement_acceptance_id,
            "revision": row.revision,
            "auth_method": row.auth_method,
            "trust_scope": row.trust_scope,
            "view_digest": row.view_digest,
        }

    def _view_entry(self, entry: SnapshotEntry) -> dict[str, Any]:
        value = self._read_blob(entry.blob, entry.size)
        return {
            **entry.as_dict(),
            "content_base64": base64.b64encode(value).decode("ascii"),
        }

    def _view_diff(self, context: CandidateContext) -> list[dict[str, Any]]:
        result_by_path = context.result.manifest.by_path()
        baseline_by_path = context.baseline.manifest.by_path()
        values: list[dict[str, Any]] = []
        for change in context.changeset.changes:
            values.append({
                "after": None if change.after is None else self._view_entry(result_by_path[change.path]),
                "before": None if change.before is None else self._view_entry(baseline_by_path[change.path]),
                "op": change.op,
                "path": change.path,
            })
        return values

    def _view_publication(self, candidate_id: str) -> dict[str, Any] | None:
        publication_id = self._latest_publication_id(candidate_id)
        if publication_id is None:
            return None
        row = self.session.get(CandidatePublicationRow, publication_id)
        if row is None or row.candidate_id != candidate_id:
            raise HumanProtocolError("publication_scope_mismatch")
        return {
            "publication_id": row.publication_id,
            "candidate_id": row.candidate_id,
            "task_id": row.task_id,
            "generation_revision": row.generation_revision,
            "run_id": row.run_id,
            "lineage_ref": row.lineage_ref,
            "provenance": _parse_json(row.provenance_json, "publication_json_invalid"),
        }

    def candidate_view(self, candidate_id: str, *, policy_revision: int = 1) -> dict[str, Any]:
        if policy_revision != CURRENT_POLICY_REVISION:
            raise HumanProtocolError("policy_revision_invalid")
        context = self._candidate_context(candidate_id)
        latest_verification = self._latest_verification(candidate_id)
        latest_assurance = self._latest_assurance(candidate_id)
        disposition, acceptance_id = self._current_disposition(candidate_id)
        history = self._decision_history(candidate_id)
        latest_evidence: dict[str, Any] | None = None
        checks: list[dict[str, Any]] = []
        if latest_verification is not None:
            evidence_row = self.session.get(EvidenceSetRow, latest_verification[0].evidence_set_id)
            if evidence_row is None or evidence_row.candidate_id != candidate_id:
                raise HumanProtocolError("evidence_set_binding_mismatch")
            latest_evidence = _parse_json(evidence_row.canonical_json, "evidence_set_json_invalid")
            if not isinstance(latest_evidence, dict):
                raise HumanProtocolError("evidence_set_json_invalid")
            latest_evidence = {
                **latest_evidence,
                "evidence_set_id": evidence_row.evidence_set_id,
                "trusted_runner_ref": evidence_row.trusted_runner_ref,
            }
            checks = list(latest_evidence.get("observations", []))
        verification_value = None if latest_verification is None else {
            **latest_verification[1].as_dict(),
            "evidence_set_id": latest_verification[0].evidence_set_id,
            "requirements_snapshot_id": latest_verification[0].requirements_snapshot_id,
            "policy_revision": latest_verification[0].policy_revision,
            "verifier_principal": latest_verification[0].verifier_principal,
            "verifier_type": latest_verification[0].verifier_type,
            "environment": _parse_json(latest_verification[0].environment_json, "verification_environment_invalid"),
            "started_at": _display_time(latest_verification[0].started_at),
            "completed_at": _display_time(latest_verification[0].completed_at),
        }
        missing_reasons = (
            ["verification_missing"]
            if verification_value is None
            else list(verification_value.get("failures", []))
        )
        validation_checks = [dict(item) for item in self._validation_checks(context)]
        assurance_mode = self._assurance_mode(context)
        validation_contract = self._validation_contract_value(context)
        decision_revision = max((item.revision for item in history), default=0)
        base: dict[str, Any] = {
            "assurance": None if latest_assurance is None else {
                "assessment_id": latest_assurance.assessment_id,
                "mode": latest_assurance.mode,
                "outcome": latest_assurance.outcome,
                "status": latest_assurance.status,
                "validity": latest_assurance.validity,
                "verification_id": latest_assurance.verification_id,
                "evidence_set_id": latest_assurance.evidence_set_id,
                "revision": latest_assurance.revision,
            },
            "assurance_policy": {
                "mode": assurance_mode.value,
                "profile_ref": context.candidate.validation_contract_snapshot_id,
                "profile_revision": validation_contract["revision"],
            },
            "baseline": context.baseline.manifest.as_dict(),
            "candidate": context.candidate.as_dict(),
            "candidate_id": candidate_id,
            "changeset": context.changeset.as_dict(),
            "changeset_id": context.changeset.changeset_id,
            "decision_history": [self._decision_view_item(item) for item in history],
            "decision_revision": decision_revision,
            "diff": self._view_diff(context),
            "disposition": {"acceptance_id": acceptance_id, "state": disposition},
            "evidence": latest_evidence,
            "evidence_set_id": None if latest_verification is None else latest_verification[0].evidence_set_id,
            "eligibility_revision": latest_assurance.revision if latest_assurance is not None else 0,
            "format": "pn.candidate.view.v1",
            "missing_reasons": missing_reasons,
            "policy_revision": policy_revision,
            "publication": self._view_publication(candidate_id),
            "result": context.result.manifest.as_dict(),
            "requirements_snapshot_id": context.candidate.requirements_snapshot_id,
            "requirements": context.requirements.manifest.as_dict(),
            "validation_contract_snapshot_id": context.candidate.validation_contract_snapshot_id,
            "validation_contract": validation_checks,
            "verification": verification_value,
            "verification_id": None if latest_verification is None else latest_verification[0].verification_id,
            "checks": checks,
            "review_round": decision_revision,
        }
        result = dict(base)
        result["view_digest"] = sha256_id(canonical_json(base))
        return result

    def _load_enrollment_challenge(
        self,
        *,
        challenge_id: str,
        ceremony: str,
        now: datetime | None = None,
    ) -> tuple[HumanEnrollmentChallengeRow, Any]:
        if not isinstance(challenge_id, str) or not challenge_id.strip() or len(challenge_id) > 80:
            raise HumanProtocolError("enrollment_challenge_invalid")
        config = _a_lp_config()
        row = self.session.get(HumanEnrollmentChallengeRow, challenge_id)
        if row is None or row.ceremony != ceremony:
            raise HumanProtocolError("enrollment_challenge_invalid")
        if row.consumed_at is not None:
            raise HumanProtocolError("enrollment_challenge_replayed")
        if (
            row.installation_id != config.installation_id
            or row.rp_id != config.rp_id
            or row.origin != config.origin
        ):
            raise HumanProtocolError("enrollment_challenge_scope_invalid")
        if _now(now) >= _now(row.expires_at):
            raise HumanProtocolError("enrollment_challenge_expired")
        return row, config

    def _authorize_key_management(
        self,
        *,
        key_id: str,
        session_id: str | None,
        csrf_token: str | bytes | None,
        now: datetime | None = None,
    ) -> HumanTrustKeyRow:
        if not isinstance(session_id, str) or not isinstance(csrf_token, (str, bytes)):
            raise HumanProtocolError("key_management_session_required")
        session = self._active_session(session_id, now)
        if not hmac.compare_digest(session.csrf_digest, _raw_digest(csrf_token, "csrf_token")):
            raise HumanProtocolError("csrf_rejected")
        grant = self.session.get(HumanPairingGrantRow, session.grant_id)
        key = self.session.get(HumanTrustKeyRow, key_id)
        if (
            grant is None
            or key is None
            or grant.key_id != key_id
            or key.principal_ref != session.principal_ref
        ):
            raise HumanProtocolError("key_management_scope_invalid")
        self._validate_web_grant(grant, now=now)
        config = _a_lp_config()
        if (
            key.installation_id != config.installation_id
            or key.rp_id != config.rp_id
            or key.origin != config.origin
            or key.algorithm != "ES256"
            or key.status not in {HUMAN_KEY_ACTIVE, HUMAN_KEY_RETIRING}
            or (key.status == HUMAN_KEY_RETIRING and key.retire_at is not None and _now(now) >= _now(key.retire_at))
        ):
            raise HumanProtocolError("human_key_unavailable")
        return key

    def _validate_web_grant(
        self,
        grant: HumanPairingGrantRow,
        *,
        now: datetime | None = None,
    ) -> None:
        """Re-check a WebAuthn grant's live trust binding on every use."""
        if grant.key_id is None:
            if not _human_fixture_enabled() or grant.auth_method != HUMAN_TEST_AUTH_METHOD:
                raise HumanProtocolError("pairing_fixture_only")
            return
        config = _a_lp_config()
        key = self.session.get(HumanTrustKeyRow, grant.key_id)
        if (
            grant.auth_method != HUMAN_WEBAUTHN_AUTH_METHOD
            or grant.installation_id != config.installation_id
            or key is None
            or key.principal_ref != grant.principal_ref
            or key.installation_id != config.installation_id
            or key.rp_id != config.rp_id
            or key.origin != config.origin
            or key.algorithm != "ES256"
            or key.status not in {HUMAN_KEY_ACTIVE, HUMAN_KEY_RETIRING}
            or (
                key.status == HUMAN_KEY_RETIRING
                and key.retire_at is not None
                and _now(now) >= _now(key.retire_at)
            )
        ):
            raise HumanProtocolError("human_key_unavailable")

    def _usable_web_keys(self, *, now: datetime | None = None) -> list[HumanTrustKeyRow]:
        config = _a_lp_config()
        current = _now(now)
        rows = list(
            self.session.execute(
                select(HumanTrustKeyRow)
                .where(
                    HumanTrustKeyRow.installation_id == config.installation_id,
                    HumanTrustKeyRow.rp_id == config.rp_id,
                    HumanTrustKeyRow.origin == config.origin,
                    HumanTrustKeyRow.status.in_((HUMAN_KEY_ACTIVE, HUMAN_KEY_RETIRING)),
                )
                .order_by(HumanTrustKeyRow.created_at.asc(), HumanTrustKeyRow.key_id.asc())
            ).scalars()
        )
        return [
            row
            for row in rows
            if row.status == HUMAN_KEY_ACTIVE
            or row.retire_at is None
            or current < _now(row.retire_at)
        ]

    def issue_enrollment_challenge(
        self,
        *,
        ceremony: str,
        key_id: str | None = None,
        session_id: str | None = None,
        csrf_token: str | bytes | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        if ceremony not in {"registration", "authentication", "revocation"}:
            raise HumanProtocolError("enrollment_ceremony_invalid")
        current = _now(now)
        config = _a_lp_config()
        principal_ref: str | None = None
        user_id: str | None = None
        selected_key_id: str | None = None
        if ceremony == "registration":
            if key_id is not None:
                old_key = self._authorize_key_management(
                    key_id=key_id,
                    session_id=session_id,
                    csrf_token=csrf_token,
                    now=now,
                )
                if old_key.installation_id != config.installation_id:
                    raise HumanProtocolError("key_scope_invalid")
                principal_ref = old_key.principal_ref
                selected_key_id = old_key.key_id
            else:
                if self._usable_web_keys(now=now):
                    raise HumanProtocolError("enrollment_rotation_required")
                principal_ref = "human:" + secrets.token_hex(16)
            user_id = b64u_encode(secrets.token_bytes(32))
            audience = "polynexus-human-enrollment"
        elif ceremony == "authentication":
            available = self._usable_web_keys(now=now)
            if key_id is not None:
                available = [row for row in available if row.key_id == key_id]
                if not available:
                    raise HumanProtocolError("human_key_unavailable")
                selected_key_id = key_id
            if not available:
                raise HumanProtocolError("human_enrollment_required")
            audience = "polynexus-human-pairing"
        else:
            if not isinstance(key_id, str) or not key_id:
                raise HumanProtocolError("key_id_required")
            key = self._authorize_key_management(
                key_id=key_id,
                session_id=session_id,
                csrf_token=csrf_token,
                now=now,
            )
            if key.status not in {HUMAN_KEY_ACTIVE, HUMAN_KEY_RETIRING}:
                raise HumanProtocolError("human_key_unavailable")
            selected_key_id = key.key_id
            principal_ref = key.principal_ref
            audience = "polynexus-human-key-revocation"

        challenge = secrets.token_bytes(32)
        row = HumanEnrollmentChallengeRow(
            challenge_id=_random_id("enrollment"),
            ceremony=ceremony,
            principal_ref=principal_ref,
            key_id=selected_key_id,
            challenge_digest=challenge_digest(challenge),
            audience=audience,
            installation_id=config.installation_id,
            rp_id=config.rp_id,
            origin=config.origin,
            expires_at=_db_time(current + timedelta(minutes=5)),
            consumed_at=None,
            created_at=_db_time(current),
        )
        self.session.add(row)
        self.session.flush()
        available_keys = self._usable_web_keys(now=now) if ceremony != "registration" else []
        if selected_key_id is not None:
            available_keys = [item for item in available_keys if item.key_id == selected_key_id]
        return {
            "challenge_id": row.challenge_id,
            "challenge": b64u_encode(challenge),
            "ceremony": ceremony,
            "audience": audience,
            "origin": config.origin,
            "rp_id": config.rp_id,
            "principal_ref": principal_ref,
            "user_id": user_id,
            "allow_credentials": [
                {"id": item.credential_id, "type": "public-key"}
                for item in available_keys
            ],
            "expires_at": _display_time(row.expires_at),
        }

    def register_webauthn_credential(
        self,
        *,
        challenge_id: str,
        credential: Mapping[str, Any],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        challenge, config = self._load_enrollment_challenge(
            challenge_id=challenge_id,
            ceremony="registration",
            now=now,
        )
        if not challenge.principal_ref:
            raise HumanProtocolError("enrollment_principal_missing")
        try:
            registered = verify_registration(
                credential,
                expected_challenge_digest=challenge.challenge_digest,
                expected_origin=config.origin,
                rp_id=config.rp_id,
            )
        except ALPVerificationError as exc:
            raise HumanProtocolError(str(exc)) from exc
        credential_ref = b64u_encode(registered.credential_id)
        existing = self.session.execute(
            select(HumanTrustKeyRow.key_id)
            .where(HumanTrustKeyRow.credential_id == credential_ref)
            .limit(1)
        ).scalar_one_or_none()
        if existing is not None:
            raise HumanProtocolError("credential_already_registered")
        rotation_source = None
        if challenge.key_id is not None:
            rotation_source = self.session.get(HumanTrustKeyRow, challenge.key_id)
            if (
                rotation_source is None
                or rotation_source.principal_ref != challenge.principal_ref
                or rotation_source.installation_id != config.installation_id
                or rotation_source.rp_id != config.rp_id
                or rotation_source.origin != config.origin
                or rotation_source.status not in {HUMAN_KEY_ACTIVE, HUMAN_KEY_RETIRING}
            ):
                raise HumanProtocolError("rotation_source_invalid")
        elif self._usable_web_keys(now=now):
            # A delayed or concurrent bootstrap challenge must not create a
            # second Human principal after the first trust key is active.
            # Recovery from a revoked/compromised registry remains possible
            # because _usable_web_keys excludes those terminal states.
            raise HumanProtocolError("enrollment_rotation_required")
        key = HumanTrustKeyRow(
            key_id=_random_id("key"),
            principal_ref=challenge.principal_ref,
            credential_id=credential_ref,
            public_key=b64u_encode(registered.public_key),
            algorithm="ES256",
            rp_id=config.rp_id,
            origin=config.origin,
            installation_id=config.installation_id,
            status=HUMAN_KEY_ACTIVE,
            sign_count=registered.sign_count,
            rotated_from=rotation_source.key_id if rotation_source is not None else None,
            retire_at=None,
            revoked_at=None,
            created_at=_db_time(now),
            last_used_at=None,
        )
        if rotation_source is not None:
            rotation_source.status = HUMAN_KEY_RETIRING
            rotation_source.retire_at = _db_time(_now(now) + timedelta(minutes=15))
        self.session.add(key)
        challenge.consumed_at = _db_time(now)
        try:
            self.session.flush()
        except IntegrityError as exc:
            raise HumanProtocolError("credential_already_registered") from exc
        return {
            "key_id": key.key_id,
            "principal_ref": key.principal_ref,
            "status": key.status,
            "algorithm": key.algorithm,
            "fingerprint": credential_fingerprint(registered.public_key),
            "rp_id": key.rp_id,
            "origin": key.origin,
        }

    def create_webauthn_pairing(
        self,
        *,
        challenge_id: str,
        credential: Mapping[str, Any],
        expires_at: datetime,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        challenge, config = self._load_enrollment_challenge(
            challenge_id=challenge_id,
            ceremony="authentication",
            now=now,
        )
        try:
            credential_id = b64u_decode(credential.get("raw_id"), "raw_id", max_length=2048)
        except ALPVerificationError as exc:
            raise HumanProtocolError(str(exc)) from exc
        credential_ref = b64u_encode(credential_id)
        key = self.session.execute(
            select(HumanTrustKeyRow)
            .where(
                HumanTrustKeyRow.credential_id == credential_ref,
                HumanTrustKeyRow.installation_id == config.installation_id,
            )
            .limit(1)
        ).scalar_one_or_none()
        if key is None:
            raise HumanProtocolError("human_key_unavailable")
        if challenge.key_id is not None and challenge.key_id != key.key_id:
            raise HumanProtocolError("enrollment_challenge_key_mismatch")
        if key.status not in {HUMAN_KEY_ACTIVE, HUMAN_KEY_RETIRING}:
            raise HumanProtocolError("human_key_unavailable")
        if key.status == HUMAN_KEY_RETIRING and key.retire_at is not None and _now(now) >= _now(key.retire_at):
            raise HumanProtocolError("human_key_retired")
        if (
            key.rp_id != config.rp_id
            or key.origin != config.origin
            or key.algorithm != "ES256"
        ):
            raise HumanProtocolError("human_key_scope_invalid")
        try:
            verified = verify_assertion(
                credential,
                expected_challenge_digest=challenge.challenge_digest,
                expected_origin=config.origin,
                rp_id=config.rp_id,
                expected_credential_id=credential_id,
                public_key=b64u_decode(key.public_key, "public_key", max_length=256),
                stored_sign_count=key.sign_count,
            )
        except ALPVerificationError as exc:
            raise HumanProtocolError(str(exc)) from exc
        requested_expiry = _now(expires_at)
        current = _now(now)
        if requested_expiry <= current or requested_expiry > current + timedelta(hours=8):
            raise HumanProtocolError("pairing_expiry_invalid")
        pairing_token = secrets.token_urlsafe(32)
        grant = HumanPairingGrantRow(
            grant_id=_random_id("grant"),
            principal_ref=key.principal_ref,
            proof_digest=_raw_digest(pairing_token, "pairing_token"),
            key_id=key.key_id,
            auth_method=HUMAN_WEBAUTHN_AUTH_METHOD,
            installation_id=config.installation_id,
            enrollment_challenge_id=challenge.challenge_id,
            status="ACTIVE",
            expires_at=_db_time(requested_expiry),
            revoked_at=None,
            created_at=_db_time(now),
        )
        key.sign_count = verified.sign_count
        key.last_used_at = _db_time(now)
        challenge.consumed_at = _db_time(now)
        self.session.add(grant)
        try:
            self.session.flush()
        except IntegrityError as exc:
            raise HumanProtocolError("pairing_token_collision") from exc
        return {
            "grant_id": grant.grant_id,
            "principal_ref": grant.principal_ref,
            "status": grant.status,
            "expires_at": _display_time(grant.expires_at),
            "key_id": grant.key_id,
            "auth_method": grant.auth_method,
            "enrollment_challenge_id": grant.enrollment_challenge_id,
            "pairing_token": pairing_token,
        }

    def revoke_webauthn_key(
        self,
        *,
        challenge_id: str,
        key_id: str,
        credential: Mapping[str, Any],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        challenge, config = self._load_enrollment_challenge(
            challenge_id=challenge_id,
            ceremony="revocation",
            now=now,
        )
        key = self.session.get(HumanTrustKeyRow, key_id)
        if key is None or challenge.key_id != key_id or challenge.principal_ref != key.principal_ref:
            raise HumanProtocolError("key_scope_invalid")
        if (
            key.status not in {HUMAN_KEY_ACTIVE, HUMAN_KEY_RETIRING}
            or key.installation_id != config.installation_id
            or key.rp_id != config.rp_id
            or key.origin != config.origin
            or key.algorithm != "ES256"
        ):
            raise HumanProtocolError("human_key_unavailable")
        try:
            credential_id = b64u_decode(credential.get("raw_id"), "raw_id", max_length=2048)
            verified = verify_assertion(
                credential,
                expected_challenge_digest=challenge.challenge_digest,
                expected_origin=config.origin,
                rp_id=config.rp_id,
                expected_credential_id=credential_id,
                public_key=b64u_decode(key.public_key, "public_key", max_length=256),
                stored_sign_count=key.sign_count,
            )
        except ALPVerificationError as exc:
            raise HumanProtocolError(str(exc)) from exc
        if b64u_encode(verified.credential_id) != key.credential_id:
            raise HumanProtocolError("credential_id_mismatch")
        key.sign_count = verified.sign_count
        key.last_used_at = _db_time(now)
        key.status = HUMAN_KEY_REVOKED
        key.revoked_at = _db_time(now)
        key.retire_at = None
        for grant in self.session.execute(
            select(HumanPairingGrantRow).where(HumanPairingGrantRow.key_id == key_id)
        ).scalars():
            if grant.status != "REVOKED":
                grant.status = "REVOKED"
                grant.revoked_at = _db_time(now)
                for session in self.session.execute(
                    select(HumanSessionRow).where(HumanSessionRow.grant_id == grant.grant_id)
                ).scalars():
                    if session.status != "REVOKED":
                        session.status = "REVOKED"
                        session.revoked_at = _db_time(now)
        challenge.consumed_at = _db_time(now)
        self.session.flush()
        return {
            "key_id": key.key_id,
            "principal_ref": key.principal_ref,
            "status": key.status,
            "revoked_grants": True,
        }

    def create_pairing(
        self,
        *,
        principal_ref: str,
        enrollment_proof: str | bytes,
        expires_at: datetime,
    ) -> dict[str, Any]:
        if not _human_fixture_enabled():
            raise HumanProtocolError("enrollment_fixture_only")
        if not isinstance(principal_ref, str) or not principal_ref.strip() or len(principal_ref) > 256:
            raise HumanProtocolError("principal_invalid")
        expiry = _now(expires_at)
        if expiry <= _now():
            raise HumanProtocolError("pairing_expired")
        assertion_expiry = _verify_human_enrollment_assertion(
            principal_ref=principal_ref,
            enrollment_proof=enrollment_proof,
            expires_at=expiry,
        )
        expiry = min(expiry, assertion_expiry)
        if expiry <= _now():
            raise HumanProtocolError("pairing_expired")
        proof_digest = _raw_digest(enrollment_proof, "enrollment_proof")
        replayed = self.session.execute(
            select(HumanPairingGrantRow.grant_id)
            .where(HumanPairingGrantRow.proof_digest == proof_digest)
            .limit(1)
        ).scalar_one_or_none()
        if replayed is not None:
            raise HumanProtocolError("enrollment_assertion_replayed")
        row = HumanPairingGrantRow(
            grant_id=_random_id("grant"),
            principal_ref=principal_ref,
            proof_digest=proof_digest,
            key_id=None,
            auth_method=HUMAN_TEST_AUTH_METHOD,
            installation_id=None,
            enrollment_challenge_id=None,
            status="ACTIVE",
            expires_at=_db_time(expiry),
            revoked_at=None,
            created_at=_db_time(),
        )
        try:
            # The preflight lookup above gives the normal error path.  The
            # unique proof digest is the authoritative race guard when two
            # requests cross between lookup and insert.
            with self.session.begin_nested():
                self.session.add(row)
                self.session.flush()
        except IntegrityError as exc:
            raise HumanProtocolError("enrollment_assertion_replayed") from exc
        return {
            "grant_id": row.grant_id,
            "principal_ref": row.principal_ref,
            "status": row.status,
            "expires_at": _display_time(row.expires_at),
        }

    def _active_grant(self, grant_id: str, proof: str | bytes, now: datetime | None = None) -> HumanPairingGrantRow:
        row = self.session.get(HumanPairingGrantRow, grant_id)
        if row is None or row.status != "ACTIVE" or row.revoked_at is not None:
            raise HumanProtocolError("pairing_invalid")
        if _now(now) >= _now(row.expires_at):
            raise HumanProtocolError("pairing_expired")
        if not hmac.compare_digest(row.proof_digest, _raw_digest(proof, "pairing_proof")):
            raise HumanProtocolError("pairing_proof_invalid")
        self._validate_web_grant(row, now=now)
        return row

    def create_session(
        self,
        *,
        grant_id: str,
        pairing_proof: str | bytes,
        audience: str,
        csrf_token: str | bytes,
        expires_at: datetime | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        grant = self._active_grant(grant_id, pairing_proof, now)
        if not isinstance(audience, str) or not audience.strip() or len(audience) > 64:
            raise HumanProtocolError("audience_invalid")
        requested_expiry = _now(expires_at) if expires_at is not None else _now(now) + timedelta(minutes=15)
        if requested_expiry <= _now(now) or requested_expiry > _now(grant.expires_at):
            raise HumanProtocolError("session_expiry_invalid")
        row = HumanSessionRow(
            session_id=_random_id("session"),
            grant_id=grant.grant_id,
            principal_ref=grant.principal_ref,
            audience=audience,
            csrf_digest=_raw_digest(csrf_token, "csrf_token"),
            status="ACTIVE",
            expires_at=_db_time(requested_expiry),
            revoked_at=None,
            created_at=_db_time(now),
        )
        self.session.add(row)
        self.session.flush()
        return {
            "session_id": row.session_id,
            "principal_ref": row.principal_ref,
            "audience": row.audience,
            "status": row.status,
            "expires_at": _display_time(row.expires_at),
        }

    def revoke_session(
        self,
        session_id: str,
        *,
        csrf_token: str | bytes,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        row = self.session.get(HumanSessionRow, session_id)
        if row is None:
            raise HumanProtocolError("session_not_found")
        if not hmac.compare_digest(row.csrf_digest, _raw_digest(csrf_token, "csrf_token")):
            raise HumanProtocolError("csrf_rejected")
        if row.status != "REVOKED":
            row.status = "REVOKED"
            row.revoked_at = _db_time(now)
        self.session.flush()
        return {"session_id": row.session_id, "status": row.status}

    def revoke_pairing(self, grant_id: str, *, now: datetime | None = None) -> None:
        row = self.session.get(HumanPairingGrantRow, grant_id)
        if row is None:
            raise HumanProtocolError("pairing_not_found")
        if row.status != "REVOKED":
            row.status = "REVOKED"
            row.revoked_at = _db_time(now)
        for session in self.session.execute(
            select(HumanSessionRow).where(HumanSessionRow.grant_id == grant_id)
        ).scalars():
            if session.status != "REVOKED":
                session.status = "REVOKED"
                session.revoked_at = _db_time(now)
        self.session.flush()

    def _active_session(self, session_id: str, now: datetime | None = None) -> HumanSessionRow:
        row = self.session.get(HumanSessionRow, session_id)
        if row is None or row.status != "ACTIVE" or row.revoked_at is not None:
            raise HumanProtocolError("session_invalid")
        if _now(now) >= _now(row.expires_at):
            raise HumanProtocolError("session_expired")
        grant = self.session.get(HumanPairingGrantRow, row.grant_id)
        if grant is None or grant.status != "ACTIVE" or grant.revoked_at is not None:
            raise HumanProtocolError("pairing_invalid")
        if _now(now) >= _now(grant.expires_at):
            raise HumanProtocolError("pairing_expired")
        if grant.principal_ref != row.principal_ref:
            raise HumanProtocolError("principal_binding_invalid")
        self._validate_web_grant(grant, now=now)
        return row

    def issue_challenge(
        self,
        *,
        session_id: str,
        candidate_id: str,
        action: str,
        replacement_acceptance_id: str | None = None,
        policy_revision: int = 1,
        expires_at: datetime | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        self._active_session(session_id, now)
        if action not in {"Accept", "Reject", "Revoke", "Supersede"}:
            raise HumanProtocolError("decision_action_invalid")
        if action == "Supersede" and not replacement_acceptance_id:
            raise HumanProtocolError("replacement_acceptance_required")
        if action != "Supersede" and replacement_acceptance_id is not None:
            raise HumanProtocolError("replacement_acceptance_unexpected")
        if policy_revision != CURRENT_POLICY_REVISION:
            raise HumanProtocolError("policy_revision_invalid")
        if action == "Accept":
            latest = self._latest_verification(candidate_id)
            if latest is not None:
                self._ensure_current_assurance(candidate_id, latest)
        view = self.candidate_view(candidate_id, policy_revision=policy_revision)
        expiry = _now(expires_at) if expires_at is not None else _now(now) + timedelta(minutes=5)
        if expiry <= _now(now):
            raise HumanProtocolError("challenge_expired")
        nonce = secrets.token_urlsafe(32)
        row = HumanChallengeRow(
            challenge_id=_random_id("challenge"),
            session_id=session_id,
            candidate_id=candidate_id,
            view_digest=view["view_digest"],
            action=action,
            replacement_acceptance_id=replacement_acceptance_id,
            policy_revision=policy_revision,
            nonce_digest=_raw_digest(nonce, "nonce"),
            expires_at=_db_time(expiry),
            consumed_at=None,
            created_at=_db_time(now),
        )
        self.session.add(row)
        self.session.flush()
        return {
            "challenge_id": row.challenge_id,
            "candidate_id": candidate_id,
            "action": action,
            "replacement_acceptance_id": replacement_acceptance_id,
            "view_digest": row.view_digest,
            "nonce": nonce,
            "expires_at": _display_time(row.expires_at),
        }

    def _latest_publication_id(self, candidate_id: str) -> str | None:
        return self.session.execute(
            select(CandidatePublicationRow.publication_id)
            .where(CandidatePublicationRow.candidate_id == candidate_id)
            .order_by(CandidatePublicationRow.created_at.desc(), CandidatePublicationRow.publication_id.desc())
            .limit(1)
        ).scalar_one_or_none()

    def _acceptance_scope(self, acceptance_id: str) -> tuple[str | None, int | None, str | None]:
        accepted = self.session.get(AcceptedResultRow, acceptance_id)
        if accepted is None:
            raise HumanProtocolError("replacement_acceptance_invalid")
        if accepted.publication_id is None:
            return None, None, None
        publication = self.session.get(CandidatePublicationRow, accepted.publication_id)
        if publication is None or publication.candidate_id != accepted.candidate_id:
            raise HumanProtocolError("replacement_publication_invalid")
        return publication.task_id, publication.generation_revision, publication.run_id

    def _decision_receipt(self, row: HumanDecisionEventRow, *, idempotent: bool = False) -> dict[str, Any]:
        state = {
            "Accept": "ACCEPTED",
            "Reject": "REJECTED",
            "Revoke": "REVOKED",
            "Supersede": "SUPERSEDED",
        }[row.action]
        return {
            "action": row.action,
            "acceptance_id": row.acceptance_id,
            "candidate_id": row.candidate_id,
            "decision_id": row.decision_id,
            "disposition": state,
            "idempotent": idempotent,
            "revision": row.revision,
        }

    def submit_decision(
        self,
        *,
        session_id: str,
        challenge_id: str,
        nonce: str,
        action: str,
        candidate_id: str,
        view_digest: str,
        csrf_token: str | bytes,
        origin: str,
        expected_origin: str,
        command_id: str,
        reason: str | None = None,
        policy_revision: int = 1,
        replacement_acceptance_id: str | None = None,
        mandatory_pass: bool | None = None,
        human: Any = None,
        actor_claim: Any = None,
        now: datetime | None = None,
        **unsupported: Any,
    ) -> dict[str, Any]:
        if mandatory_pass is not None or human is not None or actor_claim is not None or unsupported:
            raise HumanProtocolError("agent_promotion_forbidden")
        session = self._active_session(session_id, now)
        if action not in {"Accept", "Reject", "Revoke", "Supersede"}:
            raise HumanProtocolError("decision_action_invalid")
        if policy_revision != CURRENT_POLICY_REVISION:
            raise HumanProtocolError("policy_revision_invalid")
        if not isinstance(command_id, str) or not command_id or len(command_id) > 128:
            raise HumanProtocolError("command_id_invalid")
        if not isinstance(origin, str) or not isinstance(expected_origin, str) or origin != expected_origin:
            raise HumanProtocolError("origin_rejected")
        if not hmac.compare_digest(session.csrf_digest, _raw_digest(csrf_token, "csrf_token")):
            raise HumanProtocolError("csrf_rejected")
        challenge = self.session.get(HumanChallengeRow, challenge_id)
        if challenge is None or challenge.session_id != session_id or challenge.candidate_id != candidate_id:
            raise HumanProtocolError("challenge_binding_invalid")
        if challenge.action != action:
            raise HumanProtocolError("challenge_action_mismatch")
        if challenge.replacement_acceptance_id != replacement_acceptance_id:
            raise HumanProtocolError("challenge_replacement_mismatch")
        if challenge.policy_revision != policy_revision:
            raise HumanProtocolError("policy_revision_mismatch")
        if not hmac.compare_digest(challenge.nonce_digest, _raw_digest(nonce, "nonce")):
            raise HumanProtocolError("challenge_nonce_invalid")
        existing = self.session.execute(
            select(HumanDecisionEventRow)
            .where(
                HumanDecisionEventRow.principal_ref == session.principal_ref,
                HumanDecisionEventRow.command_id == command_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            if (
                existing.candidate_id != candidate_id
                or existing.action != action
                or existing.challenge_id != challenge_id
                or existing.view_digest != view_digest
                or existing.replacement_acceptance_id != replacement_acceptance_id
                or existing.reason != reason
            ):
                raise HumanProtocolError("command_replay_conflict")
            return self._decision_receipt(existing, idempotent=True)
        if challenge.consumed_at is not None:
            raise HumanProtocolError("challenge_replayed")
        if _now(now) >= _now(challenge.expires_at):
            raise HumanProtocolError("challenge_expired")
        disposition, active_acceptance = self._current_disposition(candidate_id)
        latest = self._latest_verification(candidate_id)
        assurance: AssuranceAssessmentRow | None = None
        assurance_mode: AssuranceMode | None = None
        if action == "Accept" and latest is not None:
            assurance, assurance_mode = self._ensure_current_assurance(candidate_id, latest)
        view = self.candidate_view(candidate_id, policy_revision=policy_revision)
        if view["view_digest"] != challenge.view_digest or view["view_digest"] != view_digest:
            raise HumanProtocolError("stale_candidate_view")
        if action == "Accept":
            if latest is None or not latest[1].acceptance_eligible:
                raise HumanProtocolError("acceptance_gate_blocked")
            if assurance is None or assurance_mode is None:
                raise HumanProtocolError("assurance_policy_blocked")
            if assurance_mode is AssuranceMode.STANDARD and assurance.status not in {
                AssuranceStatus.CROSS_REVIEWED.value,
                AssuranceStatus.VERIFIED.value,
            }:
                raise HumanProtocolError("assurance_policy_blocked")
            if assurance_mode is AssuranceMode.VERIFIED and assurance.status != AssuranceStatus.VERIFIED.value:
                raise HumanProtocolError("assurance_policy_blocked")
            disposition_change = self._latest_disposition_change(candidate_id)
            if (
                disposition_change is not None
                and _now(latest[0].created_at) <= _now(disposition_change.created_at)
            ):
                raise HumanProtocolError("fresh_verification_required")
            if disposition == "ACCEPTED":
                raise HumanProtocolError("candidate_already_accepted")
        elif action == "Reject":
            if disposition == "ACCEPTED" or any(item.action == "Accept" for item in self._decision_history(candidate_id)):
                raise HumanProtocolError("accepted_result_requires_revoke_or_supersede")
        elif action == "Revoke":
            if disposition != "ACCEPTED" or active_acceptance is None:
                raise HumanProtocolError("active_acceptance_required")
        elif action == "Supersede":
            if disposition != "ACCEPTED" or active_acceptance is None:
                raise HumanProtocolError("active_acceptance_required")
            if not replacement_acceptance_id or replacement_acceptance_id == active_acceptance:
                raise HumanProtocolError("replacement_acceptance_required")
            replacement = self.session.get(AcceptedResultRow, replacement_acceptance_id)
            if replacement is None:
                raise HumanProtocolError("replacement_acceptance_invalid")
            replacement_decision = self.session.get(HumanDecisionEventRow, replacement.accept_decision_id)
            if (
                replacement_decision is None
                or replacement_decision.candidate_id != replacement.candidate_id
                or replacement_decision.action != "Accept"
                or replacement_decision.acceptance_id != replacement_acceptance_id
            ):
                raise HumanProtocolError("replacement_acceptance_invalid")
            replacement_state, replacement_active = self._current_disposition(replacement.candidate_id)
            if replacement_state != "ACCEPTED" or replacement_active != replacement_acceptance_id:
                raise HumanProtocolError("replacement_acceptance_not_current")
            if self._acceptance_scope(active_acceptance) != self._acceptance_scope(replacement_acceptance_id):
                raise HumanProtocolError("replacement_scope_mismatch")
            if any(
                item.action == "Supersede" and item.replacement_acceptance_id == replacement_acceptance_id
                for item in self.session.execute(
                    select(HumanDecisionEventRow)
                    .where(HumanDecisionEventRow.replacement_acceptance_id == replacement_acceptance_id)
                ).scalars()
            ):
                raise HumanProtocolError("replacement_acceptance_already_used")
        if action in {"Reject", "Revoke", "Supersede"} and not (reason or "").strip():
            raise HumanProtocolError("decision_reason_required")
        max_revision = self.session.execute(
            select(func.max(HumanDecisionEventRow.revision))
            .where(HumanDecisionEventRow.candidate_id == candidate_id)
        ).scalar_one()
        revision = int(max_revision or 0) + 1
        acceptance_id = _random_id("acceptance") if action == "Accept" else None
        protocol_evidence = {
            "challenge_id": challenge_id,
            "csrf_validated": True,
            "nonce_validated": True,
            "origin": expected_origin,
            "policy_revision": policy_revision,
            "session_id": session_id,
            "view_digest": view_digest,
        }
        grant = self.session.get(HumanPairingGrantRow, session.grant_id)
        if grant is None:
            raise HumanProtocolError("pairing_invalid")
        auth_method = grant.auth_method or D11_AUTH_METHOD
        protocol_evidence["auth_method"] = auth_method
        if grant.key_id is not None:
            protocol_evidence["key_id"] = grant.key_id
        if grant.enrollment_challenge_id is not None:
            protocol_evidence["enrollment_challenge_id"] = grant.enrollment_challenge_id
        row = HumanDecisionEventRow(
            decision_id=_random_id("decision"),
            candidate_id=candidate_id,
            acceptance_id=acceptance_id,
            action=action,
            principal_ref=session.principal_ref,
            session_id=session_id,
            challenge_id=challenge_id,
            command_id=command_id,
            view_digest=view_digest,
            prior_acceptance_id=active_acceptance if action in {"Revoke", "Supersede"} else None,
            replacement_acceptance_id=replacement_acceptance_id,
            reason=reason,
            revision=revision,
            trust_scope=D11_TRUST_SCOPE,
            auth_method=auth_method,
            protocol_evidence_json=_json_text(protocol_evidence),
            created_at=_db_time(now),
        )
        self.session.add(row)
        self.session.flush()
        if action == "Accept":
            publication_id = self._latest_publication_id(candidate_id)
            if publication_id is None:
                raise HumanProtocolError("publication_required")
            publication = self.session.get(CandidatePublicationRow, publication_id)
            if publication is None or publication.candidate_id != candidate_id:
                raise HumanProtocolError("publication_scope_mismatch")
            self.session.add(AcceptedResultRow(
                acceptance_id=acceptance_id,
                candidate_id=candidate_id,
                accept_decision_id=row.decision_id,
                publication_id=publication_id,
                verification_id=latest[0].verification_id,
                evidence_set_id=latest[0].evidence_set_id,
                policy_revision=policy_revision,
                view_digest=view_digest,
                created_at=_db_time(now),
            ))
            self.session.flush()
        challenge.consumed_at = _db_time(now)
        self.session.flush()
        return self._decision_receipt(row)

    # ------------------------------------------------------------------
    # W6: accepted managed worktree and portable P0 package
    # ------------------------------------------------------------------

    @staticmethod
    def _plain_path(path: Path) -> None:
        try:
            info = path.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise P0PackageError("reparse_or_symlink_unsupported")

    @classmethod
    def _safe_parent(cls, path: Path) -> None:
        if not path.is_absolute():
            raise P0PackageError("path_must_be_absolute")
        current = path
        while True:
            if current.exists():
                cls._plain_path(current)
            if current.parent == current:
                break
            current = current.parent

    @classmethod
    def _prepare_empty_directory(cls, root: Path) -> None:
        cls._safe_parent(root.parent)
        if root.exists():
            cls._plain_path(root)
            if not root.is_dir():
                raise P0PackageError("target_not_directory")
            if any(root.iterdir()):
                raise P0PackageError("target_not_empty")
        else:
            root.mkdir(parents=True, exist_ok=False)
        cls._plain_path(root)

    @classmethod
    def _safe_mkdirs(cls, root: Path, target_parent: Path) -> None:
        try:
            relative = target_parent.relative_to(root)
        except ValueError as exc:
            raise P0PackageError("target_path_escape") from exc
        current = root
        for component in relative.parts:
            current = current / component
            if current.exists():
                cls._plain_path(current)
                if not current.is_dir():
                    raise P0PackageError("target_parent_invalid")
            else:
                try:
                    current.mkdir()
                except OSError as exc:
                    raise P0PackageError("target_parent_invalid") from exc
                cls._plain_path(current)

    @classmethod
    def _write_materialized_files(
        cls,
        root: Path,
        entries: Sequence[SnapshotEntry],
        read_blob,
        *,
        marker: Mapping[str, Any] | None = None,
    ) -> None:
        reserved = {".polynexus-working-copy.json"}
        for entry in entries:
            if entry.path in reserved:
                raise P0PackageError("working_copy_namespace_collision")
            validate_relative_path(entry.path)
            target = root.joinpath(*entry.path.split("/"))
            parent = target.parent
            cls._safe_mkdirs(root, parent)
            cls._plain_path(target) if target.exists() else None
            if target.exists():
                raise P0PackageError("target_namespace_collision")
            data = read_blob(entry.blob, entry.size)
            try:
                with target.open("xb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.chmod(target, int(entry.mode, 8) & 0o777)
            except OSError as exc:
                raise P0PackageError("target_write_failed") from exc
        if marker is not None:
            marker_path = root / ".polynexus-working-copy.json"
            if marker_path.exists():
                raise P0PackageError("working_copy_namespace_collision")
            try:
                marker_path.write_bytes(canonical_json(dict(marker)))
                os.chmod(marker_path, 0o600)
            except OSError as exc:
                raise P0PackageError("working_copy_marker_failed") from exc

    @classmethod
    def _verify_materialized_worktree(
        cls,
        root: Path,
        entries: Sequence[SnapshotEntry],
        *,
        candidate_id: str,
        acceptance_id: str,
        workspace_id: str,
    ) -> None:
        cls._plain_path(root)
        if not root.is_dir():
            raise P0PackageError("workspace_path_invalid")
        marker_path = root / ".polynexus-working-copy.json"
        cls._plain_path(marker_path)
        try:
            marker_bytes = marker_path.read_bytes()
            marker = _parse_json(marker_bytes.decode("utf-8"), "working_copy_marker_invalid")
        except (OSError, UnicodeDecodeError) as exc:
            raise P0PackageError("working_copy_marker_invalid") from exc
        expected_marker = {
            "accepted_candidate_id": candidate_id,
            "acceptance_id": acceptance_id,
            "label": "Working Copy",
            "workspace_id": workspace_id,
        }
        if marker != expected_marker or canonical_json(marker) != marker_bytes:
            raise P0PackageError("working_copy_marker_mismatch")
        expected = {entry.path: entry for entry in entries}
        actual: set[str] = set()
        try:
            for path in root.rglob("*"):
                cls._plain_path(path)
                relative = path.relative_to(root).as_posix()
                if path.is_dir():
                    continue
                if relative == ".polynexus-working-copy.json":
                    continue
                validate_relative_path(relative)
                actual.add(relative)
                entry = expected.get(relative)
                if entry is None or not path.is_file():
                    raise P0PackageError("working_copy_closure_mismatch")
                value = path.read_bytes()
                if len(value) != entry.size or sha256_id(value) != entry.blob:
                    raise P0PackageError("working_copy_blob_mismatch")
        except OSError as exc:
            raise P0PackageError("working_copy_read_failed") from exc
        if actual != set(expected):
            raise P0PackageError("working_copy_closure_mismatch")

    def _accepted_context(self, acceptance_id: str) -> tuple[AcceptedResultRow, CandidateContext]:
        accepted = self.session.get(AcceptedResultRow, acceptance_id)
        if accepted is None:
            raise P0PackageError("accepted_result_not_found")
        state, active = self._current_disposition(accepted.candidate_id)
        if state not in {"ACCEPTED", "SUPERSEDED"} or active != acceptance_id:
            raise P0PackageError("accepted_result_not_current")
        context = self._candidate_context(accepted.candidate_id)
        decision = self.session.get(HumanDecisionEventRow, accepted.accept_decision_id)
        if (
            decision is None
            or decision.candidate_id != accepted.candidate_id
            or decision.action != "Accept"
            or decision.acceptance_id != accepted.acceptance_id
            or decision.trust_scope != D11_TRUST_SCOPE
            or decision.auth_method not in _ACCEPTED_AUTH_METHODS
            or decision.protocol_evidence_json is None
        ):
            raise P0PackageError("accepted_decision_binding_mismatch")
        try:
            protocol_evidence = _parse_json(
                decision.protocol_evidence_json,
                "accepted_decision_protocol_invalid",
            )
        except D1bPersistenceError as exc:
            raise P0PackageError("accepted_decision_protocol_invalid") from exc
        if not isinstance(protocol_evidence, dict):
            raise P0PackageError("accepted_decision_protocol_invalid")
        if protocol_evidence.get("auth_method") != decision.auth_method:
            raise P0PackageError("accepted_decision_protocol_mismatch")
        if decision.auth_method == HUMAN_WEBAUTHN_AUTH_METHOD:
            session_row = self.session.get(HumanSessionRow, decision.session_id)
            grant = None if session_row is None else self.session.get(HumanPairingGrantRow, session_row.grant_id)
            if (
                grant is None
                or grant.auth_method != HUMAN_WEBAUTHN_AUTH_METHOD
                or grant.key_id is None
                or grant.enrollment_challenge_id is None
                or protocol_evidence.get("key_id") != grant.key_id
                or protocol_evidence.get("enrollment_challenge_id") != grant.enrollment_challenge_id
            ):
                raise P0PackageError("accepted_decision_protocol_mismatch")
        if protocol_evidence.get("view_digest") != decision.view_digest:
            raise P0PackageError("accepted_decision_protocol_mismatch")
        if protocol_evidence.get("policy_revision") != accepted.policy_revision:
            raise P0PackageError("accepted_decision_protocol_mismatch")
        if not all(protocol_evidence.get(key) is True for key in ("csrf_validated", "nonce_validated")):
            raise P0PackageError("accepted_decision_protocol_incomplete")
        if any(
            value is None
            for value in (
                accepted.verification_id,
                accepted.evidence_set_id,
                accepted.policy_revision,
                accepted.view_digest,
            )
        ):
            # 0005-era accepted rows are retained, never guessed into a new
            # trust closure, and cannot be opened/exported as P0.
            raise P0PackageError("accepted_closure_incomplete")
        verification_row, verification = self._verification_by_id(accepted.verification_id)
        if (
            verification_row.candidate_id != accepted.candidate_id
            or verification_row.evidence_set_id != accepted.evidence_set_id
            or verification.contract_id != context.candidate.validation_contract_snapshot_id
            or not verification.acceptance_eligible
            or verification_row.policy_revision != accepted.policy_revision
        ):
            raise P0PackageError("accepted_verification_binding_mismatch")
        if accepted.policy_revision != CURRENT_POLICY_REVISION:
            raise P0PackageError("accepted_policy_revision_invalid")
        if accepted.view_digest != decision.view_digest:
            raise P0PackageError("accepted_view_binding_mismatch")
        if accepted.publication_id is not None:
            publication = self.session.get(CandidatePublicationRow, accepted.publication_id)
            if publication is None or publication.candidate_id != accepted.candidate_id:
                raise P0PackageError("accepted_publication_binding_mismatch")
        return accepted, context

    def open_accepted_worktree(
        self,
        *,
        acceptance_id: str,
        target_dir: Path,
        owner_ref: str,
    ) -> dict[str, Any]:
        if not isinstance(owner_ref, str) or not owner_ref.strip() or len(owner_ref) > 256:
            raise P0PackageError("owner_invalid")
        accepted, context = self._accepted_context(acceptance_id)
        target = Path(target_dir)
        self._prepare_empty_directory(target)
        workspace_id = _random_id("workspace")
        self._write_materialized_files(
            target,
            context.result.manifest.entries,
            self._read_blob,
            marker={
                "accepted_candidate_id": context.candidate.candidate_id,
                "acceptance_id": accepted.acceptance_id,
                "label": "Working Copy",
                "workspace_id": workspace_id,
            },
        )
        row = ManagedWorktreeRow(
            workspace_id=workspace_id,
            acceptance_id=accepted.acceptance_id,
            candidate_id=context.candidate.candidate_id,
            path_ref=str(target),
            label="Working Copy",
            # Opening creates an unclaimed Working Copy.  Ownership is an
            # explicit, separately audited takeover operation.
            owner_ref="unassigned",
            taken_over=False,
            created_at=_db_time(),
        )
        self.session.add(row)
        self.session.flush()
        return {
            "workspace_id": workspace_id,
            "acceptance_id": accepted.acceptance_id,
            "candidate_id": context.candidate.candidate_id,
            "label": row.label,
            "owner_ref": row.owner_ref,
            "path_ref": row.path_ref,
            "taken_over": row.taken_over,
        }

    def takeover_workspace(self, workspace_id: str, *, owner_ref: str) -> dict[str, Any]:
        if not isinstance(owner_ref, str) or not owner_ref.strip() or len(owner_ref) > 256:
            raise P0PackageError("owner_invalid")
        row = self.session.get(ManagedWorktreeRow, workspace_id)
        if row is None:
            raise P0PackageError("workspace_not_found")
        if owner_ref == "unassigned":
            raise P0PackageError("owner_invalid")
        accepted, context = self._accepted_context(row.acceptance_id)
        if row.candidate_id != context.candidate.candidate_id:
            raise P0PackageError("workspace_candidate_mismatch")
        workspace_path = Path(row.path_ref)
        self._plain_path(workspace_path)
        if not workspace_path.is_dir():
            raise P0PackageError("workspace_path_invalid")
        if row.taken_over and row.owner_ref != owner_ref:
            raise P0PackageError("workspace_already_owned")
        self._verify_materialized_worktree(
            workspace_path,
            context.result.manifest.entries,
            candidate_id=context.candidate.candidate_id,
            acceptance_id=accepted.acceptance_id,
            workspace_id=row.workspace_id,
        )
        row.owner_ref = owner_ref
        row.taken_over = True
        self.session.flush()
        return {
            "workspace_id": row.workspace_id,
            "acceptance_id": row.acceptance_id,
            "candidate_id": row.candidate_id,
            "label": row.label,
            "owner_ref": row.owner_ref,
            "path_ref": row.path_ref,
            "taken_over": row.taken_over,
        }

    def _package_manifest(self, accepted: AcceptedResultRow, context: CandidateContext) -> dict[str, Any]:
        verification_row, verification_result = self._verification_by_id(accepted.verification_id)
        evidence_row = self.session.get(EvidenceSetRow, accepted.evidence_set_id)
        if evidence_row is None or evidence_row.candidate_id != context.candidate.candidate_id:
            raise P0PackageError("accepted_evidence_not_found")
        evidence = _parse_json(evidence_row.canonical_json, "evidence_set_json_invalid")
        if canonical_json(evidence) != evidence_row.canonical_json.encode("utf-8"):
            raise P0PackageError("accepted_evidence_noncanonical")
        evidence = {
            "evidence_set_id": evidence_row.evidence_set_id,
            "trusted_runner_ref": evidence_row.trusted_runner_ref,
            **evidence,
        }
        verification = {
            "completed_at": _display_time(verification_row.completed_at),
            "environment": _parse_json(verification_row.environment_json, "verification_environment_invalid"),
            "evidence_set_id": evidence_row.evidence_set_id,
            "policy_revision": verification_row.policy_revision,
            "requirements_snapshot_id": verification_row.requirements_snapshot_id,
            "started_at": _display_time(verification_row.started_at),
            "verifier_principal": verification_row.verifier_principal,
            "verifier_type": verification_row.verifier_type,
            "verification_id": verification_row.verification_id,
            "result": _parse_json(verification_row.result_json, "verification_json_invalid"),
        }
        publication = None
        if accepted.publication_id is not None:
            publication_row = self.session.get(CandidatePublicationRow, accepted.publication_id)
            if publication_row is None or publication_row.candidate_id != context.candidate.candidate_id:
                raise P0PackageError("accepted_publication_not_found")
            publication = {
                "publication_id": publication_row.publication_id,
                "candidate_id": publication_row.candidate_id,
                "task_id": publication_row.task_id,
                "generation_revision": publication_row.generation_revision,
                "run_id": publication_row.run_id,
                "lineage_ref": publication_row.lineage_ref,
                "provenance": _parse_json(publication_row.provenance_json, "publication_json_invalid"),
            }
        acceptance = {
            "acceptance_id": accepted.acceptance_id,
            "candidate_id": accepted.candidate_id,
            "accept_decision_id": accepted.accept_decision_id,
            "publication_id": accepted.publication_id,
            "verification_id": accepted.verification_id,
            "evidence_set_id": accepted.evidence_set_id,
            "policy_revision": accepted.policy_revision,
            "view_digest": accepted.view_digest,
            "created_at": _display_time(accepted.created_at),
        }
        history = [
            {
                "action": item.action,
                "acceptance_id": item.acceptance_id,
                "candidate_id": item.candidate_id,
                "challenge_id": item.challenge_id,
                "command_id": item.command_id,
                "created_at": _display_time(item.created_at),
                "decision_id": item.decision_id,
                "auth_method": item.auth_method,
                "principal_ref": item.principal_ref,
                "prior_acceptance_id": item.prior_acceptance_id,
                "protocol_evidence": None if item.protocol_evidence_json is None else _parse_json(
                    item.protocol_evidence_json, "decision_protocol_evidence_invalid"
                ),
                "reason": item.reason,
                "replacement_acceptance_id": item.replacement_acceptance_id,
                "revision": item.revision,
                "trust_scope": item.trust_scope,
                "view_digest": item.view_digest,
            }
            for item in self._decision_history(context.candidate.candidate_id)
        ]
        return {
            "acceptance": acceptance,
            "acceptance_id": accepted.acceptance_id,
            "baseline_manifest": context.baseline.manifest.as_dict(),
            "baseline_snapshot_id": context.changeset.baseline,
            "candidate": context.candidate.as_dict(),
            "candidate_id": context.candidate.candidate_id,
            "changeset": context.changeset.as_dict(),
            "changeset_id": context.changeset.changeset_id,
            "decision_history": history,
            "decision_history_refs": history,
            "evidence_set": evidence,
            "format": "pn.p0.v1",
            "publication": publication,
            "requirements_snapshot_id": context.candidate.requirements_snapshot_id,
            "requirements_manifest": context.requirements.manifest.as_dict(),
            "result_manifest": context.result.manifest.as_dict(),
            "result_snapshot_id": context.changeset.result,
            "validation_contract_snapshot_id": context.candidate.validation_contract_snapshot_id,
            "validation_manifest": context.validation.manifest.as_dict(),
            "verification": verification,
        }

    def _evidence_artifacts(self, evidence: Mapping[str, Any]) -> dict[str, bytes]:
        artifacts: dict[str, bytes] = {}
        observations = evidence.get("observations")
        if not isinstance(observations, list):
            raise P0PackageError("evidence_set_json_invalid")
        for observation in observations:
            if not isinstance(observation, Mapping):
                raise P0PackageError("evidence_set_json_invalid")
            reference = observation.get("raw_artifact_ref")
            digest = observation.get("raw_artifact_sha256")
            if not isinstance(reference, str) or not reference.startswith("core-blob:"):
                raise P0PackageError("evidence_artifact_ref_invalid")
            if not isinstance(digest, str) or reference != "core-blob:" + digest:
                raise P0PackageError("evidence_artifact_hash_invalid")
            if self.content_store is None:
                raise P0PackageError("core_content_store_required")
            try:
                path = self.content_store.root / digest
                size = path.stat().st_size
                value = self.content_store.read(digest, size)
            except (OSError, ContentError) as exc:
                raise P0PackageError("evidence_artifact_unavailable") from exc
            name = f"evidence/{digest}"
            previous = artifacts.get(name)
            if previous is not None and previous != value:
                raise P0PackageError("evidence_artifact_identity_conflict")
            artifacts[name] = value
        return artifacts

    @staticmethod
    def _zip_info_is_unsafe(info: zipfile.ZipInfo) -> bool:
        mode = (info.external_attr >> 16) & 0xFFFF
        return stat.S_ISLNK(mode) or stat.S_ISDIR(mode)

    @staticmethod
    def _validate_zip_name(name: str) -> None:
        if not isinstance(name, str) or not name or "\\" in name or "\x00" in name or name.endswith("/"):
            raise P0PackageError("zip_entry_name_invalid")
        if name.startswith("source/"):
            try:
                validate_relative_path(name.removeprefix("source/"))
            except CanonicalizationError as exc:
                raise P0PackageError("zip_entry_name_invalid") from exc
        elif name.startswith("baseline/") or name.startswith("requirements/") or name.startswith("validation/"):
            prefix = name.split("/", 1)[0] + "/"
            try:
                validate_relative_path(name.removeprefix(prefix))
            except CanonicalizationError as exc:
                raise P0PackageError("zip_entry_name_invalid") from exc
        elif name.startswith("evidence/"):
            digest = name.removeprefix("evidence/")
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise P0PackageError("zip_entry_name_invalid")
        elif name not in {
            "manifest.json",
            "candidate.json",
            "changeset.json",
            "baseline_manifest.json",
            "requirements_manifest.json",
            "result_manifest.json",
            "validation_manifest.json",
            "evidence.json",
            "verification.json",
            "acceptance.json",
            "publication.json",
            "receipt.json",
        }:
            raise P0PackageError("zip_namespace_invalid")

    def export_p0(self, *, acceptance_id: str, package_path: Path) -> dict[str, Any]:
        accepted, context = self._accepted_context(acceptance_id)
        path = Path(package_path)
        if not path.is_absolute():
            raise P0PackageError("package_path_must_be_absolute")
        self._safe_parent(path.parent)
        if path.exists():
            self._plain_path(path)
            raise P0PackageError("package_exists")
        manifest = self._package_manifest(accepted, context)
        manifest_bytes = canonical_json(manifest)
        receipt_bytes = canonical_json(_p0_receipt(manifest))
        names: set[str] = set()
        try:
            with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
                control = {
                    "manifest.json": manifest_bytes,
                    "candidate.json": canonical_json(manifest["candidate"]),
                    "changeset.json": canonical_json(manifest["changeset"]),
                    "baseline_manifest.json": canonical_json(manifest["baseline_manifest"]),
                    "requirements_manifest.json": canonical_json(manifest["requirements_manifest"]),
                    "result_manifest.json": canonical_json(manifest["result_manifest"]),
                    "validation_manifest.json": canonical_json(manifest["validation_manifest"]),
                    "evidence.json": canonical_json(manifest["evidence_set"]),
                    "verification.json": canonical_json(manifest["verification"]),
                    "acceptance.json": canonical_json(manifest["acceptance"]),
                    "publication.json": canonical_json(manifest["publication"]),
                    "receipt.json": receipt_bytes,
                }
                for name, data in control.items():
                    self._validate_zip_name(name)
                    if name in names:
                        raise P0PackageError("zip_namespace_collision")
                    names.add(name)
                    archive.writestr(name, data)
                for prefix, snapshot in (
                    ("baseline", context.baseline),
                    ("requirements", context.requirements),
                    ("result", context.result),
                    ("validation", context.validation),
                ):
                    for entry in snapshot.manifest.entries:
                        namespace = "source" if prefix == "result" else prefix
                        name = f"{namespace}/{entry.path}"
                        self._validate_zip_name(name)
                        if name in names:
                            raise P0PackageError("zip_namespace_collision")
                        names.add(name)
                        archive.writestr(name, self._read_blob(entry.blob, entry.size))
                for name, value in self._evidence_artifacts(manifest["evidence_set"]).items():
                    self._validate_zip_name(name)
                    if name in names:
                        raise P0PackageError("zip_namespace_collision")
                    names.add(name)
                    archive.writestr(name, value)
        except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
            if isinstance(exc, P0PackageError):
                raise
            raise P0PackageError("p0_export_failed") from exc
        package_id = _random_id("p0")
        row = P0PackageRow(
            package_id=package_id,
            acceptance_id=accepted.acceptance_id,
            candidate_id=context.candidate.candidate_id,
            package_path=str(path),
            manifest_json=manifest_bytes.decode("utf-8"),
            manifest_digest=sha256_id(manifest_bytes),
            created_at=_db_time(),
        )
        self.session.add(row)
        self.session.flush()
        return {
            "package_id": package_id,
            "acceptance_id": accepted.acceptance_id,
            "candidate_id": context.candidate.candidate_id,
            "package_path": str(path),
            "manifest_digest": row.manifest_digest,
        }

    @classmethod
    def _verify_zip_snapshot(
        cls,
        data: Mapping[str, bytes],
        *,
        prefix: str,
        manifest: SnapshotManifest,
    ) -> dict[str, bytes]:
        expected = {f"{prefix}/{entry.path}": entry for entry in manifest.entries}
        actual = {name: value for name, value in data.items() if name.startswith(prefix + "/")}
        if set(expected) != set(actual):
            raise P0PackageError(f"p0_{prefix}_closure_mismatch")
        for name, entry in expected.items():
            value = actual[name]
            if len(value) != entry.size or sha256_id(value) != entry.blob:
                raise P0PackageError(f"p0_{prefix}_blob_mismatch")
        return actual

    @classmethod
    def _read_verified_zip(cls, package_path: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
        path = Path(package_path)
        if not path.is_absolute() or not path.is_file():
            raise P0PackageError("p0_package_not_found")
        cls._plain_path(path)
        try:
            with zipfile.ZipFile(path, "r") as archive:
                infos = archive.infolist()
                if len(infos) > 10000:
                    raise P0PackageError("zip_entry_count_limit")
                names: set[str] = set()
                total = 0
                data: dict[str, bytes] = {}
                for info in infos:
                    cls._validate_zip_name(info.filename)
                    if info.filename in names or cls._zip_info_is_unsafe(info):
                        raise P0PackageError("zip_entry_unsafe")
                    names.add(info.filename)
                    per_entry_limit = (
                        1_048_576
                        if info.filename.startswith(("source/", "baseline/", "requirements/", "validation/"))
                        else 16 * 1024 * 1024
                    )
                    if info.file_size > per_entry_limit or total + info.file_size > 64 * 1024 * 1024:
                        raise P0PackageError("zip_size_limit")
                    total += info.file_size
                    value = archive.read(info)
                    if len(value) != info.file_size:
                        raise P0PackageError("zip_entry_truncated")
                    data[info.filename] = value
        except P0PackageError:
            raise
        except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile, RuntimeError) as exc:
            raise P0PackageError("p0_package_invalid") from exc
        required = {
            "manifest.json",
            "candidate.json",
            "changeset.json",
            "baseline_manifest.json",
            "requirements_manifest.json",
            "result_manifest.json",
            "validation_manifest.json",
            "evidence.json",
            "verification.json",
            "acceptance.json",
            "publication.json",
            "receipt.json",
        }
        if not required.issubset(data):
            raise P0PackageError("p0_control_file_missing")
        manifest_bytes = data["manifest.json"]
        try:
            parsed = _parse_json(manifest_bytes.decode("utf-8"), "p0_manifest_invalid")
        except UnicodeDecodeError as exc:
            raise P0PackageError("p0_manifest_invalid") from exc
        if not isinstance(parsed, dict) or parsed.get("format") != "pn.p0.v1":
            raise P0PackageError("p0_manifest_invalid")
        if canonical_json(parsed) != manifest_bytes:
            raise P0PackageError("p0_manifest_noncanonical")
        try:
            candidate = Candidate(**{
                "changeset_id": parsed["candidate"]["changeset"],
                "requirements_snapshot_id": parsed["candidate"]["requirements"],
                "validation_contract_snapshot_id": parsed["candidate"]["validation"],
            })
            changeset = changeset_from_json(canonical_json(parsed["changeset"]).decode("utf-8"))
            baseline = SnapshotManifest.from_dict(parsed["baseline_manifest"])
            requirements = SnapshotManifest.from_dict(parsed["requirements_manifest"])
            result = SnapshotManifest.from_dict(parsed["result_manifest"])
            validation = SnapshotManifest.from_dict(parsed["validation_manifest"])
        except (KeyError, TypeError, ValueError, UnicodeDecodeError, CanonicalizationError) as exc:
            raise P0PackageError("p0_identity_invalid") from exc
        controls = {
            "candidate.json": parsed["candidate"],
            "changeset.json": parsed["changeset"],
            "baseline_manifest.json": parsed["baseline_manifest"],
            "requirements_manifest.json": parsed["requirements_manifest"],
            "result_manifest.json": parsed["result_manifest"],
            "validation_manifest.json": parsed["validation_manifest"],
            "evidence.json": parsed["evidence_set"],
            "verification.json": parsed["verification"],
            "acceptance.json": parsed["acceptance"],
            "publication.json": parsed["publication"],
        }
        if any(canonical_json(value) != data[name] for name, value in controls.items()):
            raise P0PackageError("p0_control_noncanonical")
        computed_changeset = derive_changeset(baseline, result)
        if (
            parsed.get("candidate_id") != candidate.candidate_id
            or parsed.get("changeset_id") != computed_changeset.changeset_id
            or parsed.get("changeset_id") != changeset.changeset_id
            or parsed.get("baseline_snapshot_id") != baseline.snapshot_id
            or parsed.get("result_snapshot_id") != result.snapshot_id
            or parsed.get("requirements_snapshot_id") != requirements.snapshot_id
            or parsed.get("validation_contract_snapshot_id") != validation.snapshot_id
            or changeset.canonical_bytes != computed_changeset.canonical_bytes
            or changeset.baseline != baseline.snapshot_id
            or changeset.result != result.snapshot_id
            or candidate.changeset_id != changeset.changeset_id
            or candidate.requirements_snapshot_id != requirements.snapshot_id
            or candidate.validation_contract_snapshot_id != validation.snapshot_id
        ):
            raise P0PackageError("p0_identity_mismatch")
        cls._verify_zip_snapshot(data, prefix="baseline", manifest=baseline)
        cls._verify_zip_snapshot(data, prefix="requirements", manifest=requirements)
        source = cls._verify_zip_snapshot(data, prefix="source", manifest=result)
        validation_files = cls._verify_zip_snapshot(data, prefix="validation", manifest=validation)
        validation_json = [
            value for name, value in validation_files.items() if name.lower().endswith(".json")
        ]
        if len(validation_json) != 1:
            raise P0PackageError("p0_validation_contract_invalid")
        try:
            validation_value = json.loads(validation_json[0].decode("utf-8"))
            if canonical_json(validation_value) != validation_json[0]:
                raise P0PackageError("p0_validation_contract_noncanonical")
            expected_checks = parse_validation_contract(validation_value)
        except (UnicodeDecodeError, json.JSONDecodeError, EvidenceBindingError, CanonicalizationError, P0PackageError) as exc:
            raise P0PackageError("p0_validation_contract_invalid") from exc
        evidence = parsed["evidence_set"]
        if (
            not isinstance(evidence, dict)
            or evidence.get("candidate_id") != candidate.candidate_id
            or evidence.get("contract_id") != candidate.validation_contract_snapshot_id
            or evidence.get("format") != "pn.evidence-set.v1"
            or not isinstance(evidence.get("evidence_refs"), list)
            or not isinstance(evidence.get("observations"), list)
            or not isinstance(evidence.get("evidence_set_id"), str)
            or not isinstance(evidence.get("trusted_runner_ref"), str)
            or not evidence.get("trusted_runner_ref")
        ):
            raise P0PackageError("p0_evidence_binding_mismatch")
        acceptance = parsed.get("acceptance")
        if not isinstance(acceptance, dict):
            raise P0PackageError("p0_acceptance_binding_mismatch")
        verification = parsed["verification"]
        if (
            not isinstance(verification, dict)
            or verification.get("verification_id") != acceptance.get("verification_id")
            or verification.get("evidence_set_id") != acceptance.get("evidence_set_id")
            or verification.get("evidence_set_id") != parsed["evidence_set"]["evidence_set_id"]
            or verification.get("requirements_snapshot_id") != candidate.requirements_snapshot_id
            or not isinstance(verification.get("policy_revision"), int)
            or not isinstance(verification.get("verifier_principal"), str)
            or not isinstance(verification.get("verifier_type"), str)
            or not isinstance(verification.get("environment"), dict)
            or not isinstance(verification.get("started_at"), str)
            or not isinstance(verification.get("completed_at"), str)
            or not isinstance(verification.get("result"), dict)
            or verification["result"].get("candidate_id") != candidate.candidate_id
            or verification["result"].get("contract_id") != candidate.validation_contract_snapshot_id
            or verification["result"].get("acceptance_eligible") is not True
        ):
            raise P0PackageError("p0_verification_binding_mismatch")
        if (
            verification["policy_revision"] != parsed["acceptance"].get("policy_revision")
            or verification["policy_revision"] != CURRENT_POLICY_REVISION
        ):
            raise P0PackageError("p0_policy_revision_binding_mismatch")
        if (
            not isinstance(acceptance, dict)
            or acceptance.get("acceptance_id") != parsed.get("acceptance_id")
            or acceptance.get("candidate_id") != candidate.candidate_id
            or acceptance.get("view_digest") is None
            or acceptance.get("policy_revision") is None
        ):
            raise P0PackageError("p0_acceptance_binding_mismatch")
        publication = parsed["publication"]
        if (
            not isinstance(publication, dict)
            or publication.get("candidate_id") != candidate.candidate_id
            or acceptance.get("publication_id") != publication.get("publication_id")
        ):
            raise P0PackageError("p0_publication_binding_mismatch")
        history = parsed.get("decision_history")
        if not isinstance(history, list):
            raise P0PackageError("p0_decision_history_missing")
        decision = next(
            (item for item in history if isinstance(item, dict) and item.get("decision_id") == acceptance.get("accept_decision_id")),
            None,
        )
        if (
            not isinstance(decision, dict)
            or decision.get("candidate_id") != candidate.candidate_id
            or decision.get("action") != "Accept"
            or decision.get("acceptance_id") != acceptance.get("acceptance_id")
            or decision.get("view_digest") != acceptance.get("view_digest")
            or not isinstance(decision.get("created_at"), str)
            or decision.get("trust_scope") != D11_TRUST_SCOPE
            or decision.get("auth_method") not in _ACCEPTED_AUTH_METHODS
            or not isinstance(decision.get("protocol_evidence"), dict)
        ):
            raise P0PackageError("p0_accept_decision_binding_mismatch")
        protocol_evidence = decision["protocol_evidence"]
        if (
            protocol_evidence.get("auth_method") != decision.get("auth_method")
            or
            protocol_evidence.get("challenge_id") != decision.get("challenge_id")
            or protocol_evidence.get("session_id") is None
            or protocol_evidence.get("view_digest") != decision.get("view_digest")
            or protocol_evidence.get("policy_revision") != acceptance.get("policy_revision")
            or protocol_evidence.get("csrf_validated") is not True
            or protocol_evidence.get("nonce_validated") is not True
        ):
            raise P0PackageError("p0_accept_decision_protocol_mismatch")
        if decision.get("auth_method") == HUMAN_WEBAUTHN_AUTH_METHOD and (
            not isinstance(protocol_evidence.get("key_id"), str)
            or not isinstance(protocol_evidence.get("enrollment_challenge_id"), str)
        ):
            raise P0PackageError("p0_accept_decision_protocol_mismatch")
        if not isinstance(acceptance.get("created_at"), str):
            raise P0PackageError("p0_acceptance_time_missing")
        evidence_identity = _evidence_identity(
            candidate_id=evidence["candidate_id"],
            contract_id=evidence["contract_id"],
            evidence_refs=evidence["evidence_refs"],
            observations=evidence["observations"],
            trusted_runner_ref=evidence["trusted_runner_ref"],
        )
        if sha256_id(canonical_json(evidence_identity)) != evidence["evidence_set_id"]:
            raise P0PackageError("p0_evidence_identity_mismatch")
        if evidence["evidence_refs"] != [
            item.get("evidence_id") for item in evidence["observations"]
        ]:
            raise P0PackageError("p0_evidence_reference_closure_mismatch")
        if len(set(evidence["evidence_refs"])) != len(evidence["evidence_refs"]):
            raise P0PackageError("p0_evidence_reference_duplicate")
        try:
            observations = tuple(
                EvidenceObservation(
                    candidate_id=item["candidate_id"],
                    contract_id=item["contract_id"],
                    check_id=item["check_id"],
                    evidence_type=item["evidence_type"],
                    actor_id=item["actor_id"],
                    source=item["source"],
                    requiredness=Requiredness(item["requiredness"]),
                    applicability=Applicability(item["applicability"]),
                    outcome=VerificationOutcome(item["outcome"]),
                    validity=Validity(item["validity"]),
                    command=item.get("command"),
                    cwd=item.get("cwd"),
                    argv=tuple(item.get("argv", ())),
                    runner_exit=item.get("runner_exit"),
                    child_exit=item.get("child_exit"),
                    raw_artifact_ref=item.get("raw_artifact_ref"),
                    raw_artifact_sha256=item.get("raw_artifact_sha256"),
                    freshness=item.get("freshness", "CURRENT"),
                    provenance=item.get("provenance", {}),
                    reason=item.get("reason"),
                    observed_at=datetime.fromisoformat(item["observed_at"]),
                    evidence_id=item["evidence_id"],
                )
                for item in evidence["observations"]
            )
            for observation in observations:
                provenance = dict(observation.provenance)
                cls._validate_offline_runner_provenance(
                    evidence["trusted_runner_ref"], provenance
                )
                if (
                    not isinstance(observation.command, str)
                    or not observation.command.strip()
                    or not isinstance(observation.cwd, str)
                    or not observation.cwd.strip()
                    or not observation.argv
                    or observation.runner_exit is None
                    or observation.child_exit is None
                ):
                    raise P0PackageError("p0_execution_provenance_missing")
                if (
                    not isinstance(observation.raw_artifact_ref, str)
                    or not observation.raw_artifact_ref.startswith("core-blob:")
                    or observation.raw_artifact_sha256 != observation.raw_artifact_ref.removeprefix("core-blob:")
                    or len(observation.raw_artifact_sha256) != 64
                    or any(char not in "0123456789abcdef" for char in observation.raw_artifact_sha256)
                ):
                    raise P0PackageError("p0_trusted_artifact_binding_missing")
                if observation.outcome is VerificationOutcome.PASS and (
                    observation.runner_exit != 0 or observation.child_exit != 0
                ):
                    raise P0PackageError("p0_pass_exit_mismatch")
            recomputed = evaluate_verification(
                candidate.candidate_id,
                candidate.validation_contract_snapshot_id,
                observations,
                expected_checks=expected_checks,
            ).as_dict()
        except P0PackageError:
            raise
        except (KeyError, TypeError, ValueError, CanonicalizationError, EvidenceBindingError) as exc:
            raise P0PackageError("p0_evidence_invalid") from exc
        stored_result = verification["result"]
        result_keys = {
            "acceptance_eligible",
            "candidate_id",
            "complete",
            "contract_id",
            "failures",
            "mandatory_pass",
            "optional_failures",
            "outcome",
            "validity",
        }
        if any(stored_result.get(key) != recomputed.get(key) for key in result_keys):
            raise P0PackageError("p0_verification_recompute_mismatch")
        expected_evidence = {
            f"evidence/{item['raw_artifact_sha256']}"
            for item in evidence.get("observations", [])
            if isinstance(item, dict) and isinstance(item.get("raw_artifact_sha256"), str)
        }
        actual_evidence = {name for name in data if name.startswith("evidence/")}
        if expected_evidence != actual_evidence:
            raise P0PackageError("p0_evidence_artifact_closure_mismatch")
        for name in expected_evidence:
            digest = name.removeprefix("evidence/")
            if sha256_id(data[name]) != "sha256:" + digest:
                raise P0PackageError("p0_evidence_artifact_mismatch")
        try:
            receipt = _parse_json(data["receipt.json"].decode("utf-8"), "p0_receipt_invalid")
        except UnicodeDecodeError as exc:
            raise P0PackageError("p0_receipt_invalid") from exc
        if not isinstance(receipt, dict) or canonical_json(receipt) != data["receipt.json"]:
            raise P0PackageError("p0_receipt_noncanonical")
        _verify_p0_receipt(parsed, receipt)
        return parsed, data

    def _local_acceptance_if_available(self, manifest: Mapping[str, Any]) -> AcceptedResultRow | None:
        """Apply local disposition checks without making P0 verification DB-bound.

        A copied P0 package is verified from its signed closure and receipt.  A
        verifier that has the originating D1b database may additionally reject
        a currently revoked or superseded acceptance, but an empty or
        unrelated database must not be required for offline verification.
        """
        try:
            accepted = self.session.get(AcceptedResultRow, manifest["acceptance_id"])
        except OperationalError:
            self.session.rollback()
            return None
        if accepted is None:
            return None
        current, _ = self._accepted_context(manifest["acceptance_id"])
        if current.candidate_id != manifest.get("candidate_id"):
            raise P0PackageError("p0_acceptance_candidate_mismatch")
        return current

    def verify_p0_package(self, package_path: Path) -> dict[str, Any]:
        path = Path(package_path)
        manifest, data = self._read_verified_zip(path)
        self._local_acceptance_if_available(manifest)
        try:
            registered = self.session.execute(
                select(P0PackageRow)
                .where(P0PackageRow.package_path == str(path))
                .order_by(P0PackageRow.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
        except OperationalError:
            self.session.rollback()
            registered = None
        if registered is not None and (
            registered.acceptance_id != manifest["acceptance_id"]
            or registered.candidate_id != manifest["candidate_id"]
            or registered.manifest_digest != sha256_id(canonical_json(manifest))
        ):
            raise P0PackageError("p0_registered_manifest_mismatch")
        source = {name: value for name, value in data.items() if name.startswith("source/")}
        return {
            "acceptance_id": manifest["acceptance_id"],
            "candidate_id": manifest["candidate_id"],
            "changeset_id": manifest["changeset_id"],
            "manifest_digest": sha256_id(canonical_json(manifest)),
            "source_paths": sorted(name.removeprefix("source/") for name in source),
            "verified": True,
        }

    def reconstruct_p0_package(self, *, package_path: Path, target_dir: Path) -> dict[str, Any]:
        package_path = Path(package_path)
        try:
            registered = self.session.execute(
                select(P0PackageRow)
                .where(P0PackageRow.package_path == str(package_path))
                .order_by(P0PackageRow.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
        except OperationalError:
            self.session.rollback()
            registered = None
        manifest, data = self._read_verified_zip(package_path)
        self._local_acceptance_if_available(manifest)
        if registered is not None and (
            registered.acceptance_id != manifest["acceptance_id"]
            or registered.candidate_id != manifest["candidate_id"]
            or registered.manifest_digest != sha256_id(canonical_json(manifest))
        ):
            raise P0PackageError("p0_registered_manifest_mismatch")
        source = {name: value for name, value in data.items() if name.startswith("source/")}
        target = Path(target_dir)
        self._prepare_empty_directory(target)
        entries = SnapshotManifest.from_dict(manifest["result_manifest"]).entries
        self._write_materialized_files(
            target,
            entries,
            lambda digest, size: self._verify_package_blob(source, digest, size),
            marker={
                "accepted_candidate_id": manifest["candidate_id"],
                "acceptance_id": manifest["acceptance_id"],
                "label": "Working Copy",
                "source": "P0",
            },
        )
        return {
            "acceptance_id": manifest["acceptance_id"],
            "candidate_id": manifest["candidate_id"],
            "changeset_id": manifest["changeset_id"],
            "target_dir": str(target),
            "verified": True,
        }

    @staticmethod
    def _verify_package_blob(source: Mapping[str, bytes], digest: str, size: int) -> bytes:
        for name, value in source.items():
            if len(value) == size and sha256_id(value) == digest:
                return value
        raise P0PackageError("p0_source_blob_missing")
