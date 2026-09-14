"""D1b value objects and deterministic rules.

This module is intentionally independent of SQLAlchemy and FastAPI.  It owns
the content identity boundary used by W3 and the evidence/assurance rules used
by W4.  Persistence and transport layers may store or expose these values, but
they cannot redefine their canonical bytes or silently promote an observation.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


SNAPSHOT_FORMAT = "pn.snapshot.v1"
CHANGESET_FORMAT = "pn.changeset.v1"
CANDIDATE_FORMAT = "pn.candidate.v1"
VALIDATION_CONTRACT_FORMAT = "pn.validation-contract.v1"
MAX_SNAPSHOT_ENTRY_BYTES = 1_048_576
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_MODE = re.compile(r"^100[0-7]{3}$")


class D1bError(ValueError):
    """Base class for a bounded, fail-closed D1b rejection."""


class CanonicalizationError(D1bError):
    pass


class QuiescenceError(D1bError):
    pass


class EvidenceBindingError(D1bError):
    pass


class AssuranceError(D1bError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def canonical_json(value: Any) -> bytes:
    """Return the restricted UTF-8 canonical JSON used by D1b identities."""
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise CanonicalizationError("canonical_json_invalid") from exc


def sha256_id(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _hash_object(value: Mapping[str, Any]) -> str:
    return sha256_id(canonical_json(value))


def validate_digest(value: str, *, field_name: str = "digest") -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise CanonicalizationError(f"{field_name}_invalid")
    return value


def validate_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise CanonicalizationError("path_invalid")
    if "\\" in value or "\x00" in value or value.startswith("/"):
        raise CanonicalizationError("path_invalid")
    if len(value) >= 2 and value[1] == ":":
        raise CanonicalizationError("path_absolute")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise CanonicalizationError("path_invalid")
    if str(PurePosixPath(value)) != value:
        raise CanonicalizationError("path_invalid")
    return value


def _sort_key(path: str) -> bytes:
    return path.encode("utf-8")


@dataclass(frozen=True)
class SnapshotEntry:
    path: str
    blob: str
    size: int
    mode: str = "100644"
    kind: str = "file"

    def __post_init__(self) -> None:
        validate_relative_path(self.path)
        validate_digest(self.blob, field_name="blob")
        if self.kind != "file":
            raise CanonicalizationError("snapshot_kind_unsupported")
        if _MODE.fullmatch(self.mode) is None:
            raise CanonicalizationError("snapshot_mode_invalid")
        if not isinstance(self.size, int) or isinstance(self.size, bool) or self.size < 0:
            raise CanonicalizationError("snapshot_size_invalid")
        if self.size > MAX_SNAPSHOT_ENTRY_BYTES:
            raise CanonicalizationError("snapshot_size_limit")

    def as_dict(self) -> dict[str, Any]:
        return {
            "blob": self.blob,
            "kind": self.kind,
            "mode": self.mode,
            "path": self.path,
            "size": self.size,
        }


@dataclass(frozen=True)
class SnapshotManifest:
    entries: tuple[SnapshotEntry, ...] = ()
    snapshot_id: str = field(init=False)

    def __post_init__(self) -> None:
        entries = tuple(sorted(self.entries, key=lambda item: _sort_key(item.path)))
        seen_exact: set[str] = set()
        seen_case: set[str] = set()
        for entry in entries:
            validate_relative_path(entry.path)
            if entry.path in seen_exact:
                raise CanonicalizationError("snapshot_duplicate_path")
            if entry.path.casefold() in seen_case:
                raise CanonicalizationError("snapshot_case_collision")
            seen_exact.add(entry.path)
            seen_case.add(entry.path.casefold())
        object.__setattr__(self, "entries", entries)
        object.__setattr__(self, "snapshot_id", _hash_object(self.as_dict()))

    def as_dict(self) -> dict[str, Any]:
        return {"entries": [entry.as_dict() for entry in self.entries], "format": SNAPSHOT_FORMAT}

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json(self.as_dict())

    def by_path(self) -> dict[str, SnapshotEntry]:
        return {entry.path: entry for entry in self.entries}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SnapshotManifest":
        if not isinstance(value, Mapping) or value.get("format") != SNAPSHOT_FORMAT:
            raise CanonicalizationError("snapshot_format_invalid")
        entries = value.get("entries")
        if not isinstance(entries, list):
            raise CanonicalizationError("snapshot_entries_invalid")
        parsed: list[SnapshotEntry] = []
        for item in entries:
            if not isinstance(item, Mapping):
                raise CanonicalizationError("snapshot_entry_invalid")
            if set(item) != {"blob", "kind", "mode", "path", "size"}:
                raise CanonicalizationError("snapshot_entry_keys_invalid")
            parsed.append(SnapshotEntry(**dict(item)))
        result = cls(tuple(parsed))
        if canonical_json(dict(value)) != result.canonical_bytes:
            raise CanonicalizationError("snapshot_canonical_mismatch")
        return result


@dataclass(frozen=True)
class SnapshotCapture:
    manifest: SnapshotManifest
    blobs: Mapping[str, bytes]
    quiescent: bool = True
    source_ref: str | None = None

    def __post_init__(self) -> None:
        normalized: dict[str, bytes] = {}
        for entry in self.manifest.entries:
            content = self.blobs.get(entry.blob)
            if not isinstance(content, bytes):
                raise CanonicalizationError("snapshot_blob_missing")
            if len(content) != entry.size or sha256_id(content) != entry.blob:
                raise CanonicalizationError("snapshot_blob_mismatch")
            normalized[entry.blob] = content
        object.__setattr__(self, "blobs", normalized)
        if not self.quiescent:
            raise QuiescenceError("writer_not_quiescent")


def capture_mapping(
    values: Mapping[str, bytes | tuple[bytes, str]],
    *,
    source_ref: str | None = None,
    quiescent: bool = True,
) -> SnapshotCapture:
    entries: list[SnapshotEntry] = []
    blobs: dict[str, bytes] = {}
    for path, value in values.items():
        mode = "100644"
        content: bytes
        if isinstance(value, tuple):
            if len(value) != 2:
                raise CanonicalizationError("snapshot_value_invalid")
            content, mode = value
        else:
            content = value
        if not isinstance(content, bytes):
            raise CanonicalizationError("snapshot_value_invalid")
        blob = sha256_id(content)
        entry = SnapshotEntry(path=path, blob=blob, size=len(content), mode=mode)
        entries.append(entry)
        blobs[blob] = content
    manifest = SnapshotManifest(tuple(entries))
    return SnapshotCapture(manifest, blobs, quiescent=quiescent, source_ref=source_ref)


def _directory_state(root: Path) -> dict[str, tuple[int, int, int, int]]:
    """Return the complete regular-file fence state for ``root``.

    The state is deliberately derived from a fresh walk rather than from the
    first set of paths observed by a caller.  That lets the capture boundary
    reject files added or removed while bytes are being read instead of
    silently publishing a partial snapshot.
    """
    state: dict[str, tuple[int, int, int, int]] = {}
    for path in sorted(root.rglob("*"), key=lambda item: _sort_key(item.relative_to(root).as_posix())):
        relative = path.relative_to(root).as_posix()
        # A managed Git worktree contains a ``.git`` pointer (and may contain
        # control data below it).  Git metadata is not product content and may
        # contain an absolute path back to the source repository, so it must
        # never enter a D1b identity or reconstructed Working Copy.
        if ".git" in relative.split("/"):
            continue
        if path.is_symlink():
            raise CanonicalizationError("source_reparse_unsupported")
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            raise CanonicalizationError("source_entry_unsupported")
        validate_relative_path(relative)
        if info.st_size > MAX_SNAPSHOT_ENTRY_BYTES:
            raise CanonicalizationError("snapshot_size_limit")
        state[relative] = (info.st_size, info.st_mtime_ns, info.st_ino, stat.S_IMODE(info.st_mode))
    return state


def capture_directory(root: Path, *, source_ref: str | None = None) -> SnapshotCapture:
    """Capture a materialized directory and fail closed on partial capture."""
    if not root.is_absolute() or not root.is_dir():
        raise CanonicalizationError("source_root_invalid")
    before = _directory_state(root)
    values: dict[str, bytes | tuple[bytes, str]] = {}
    for relative in before:
        mode = f"100{before[relative][3]:03o}"
        values[relative] = ((root / relative).read_bytes(), mode)
    after = _directory_state(root)
    if before != after:
        raise QuiescenceError("source_changed_during_capture")
    # Metadata can be unchanged on filesystems with coarse mtime resolution;
    # compare every captured byte again before returning the frozen snapshot.
    for relative, expected in values.items():
        current = (root / relative).read_bytes()
        expected_bytes = expected[0] if isinstance(expected, tuple) else expected
        if current != expected_bytes:
            raise QuiescenceError("source_changed_during_capture")
    capture = capture_mapping(values, source_ref=source_ref, quiescent=True)
    return capture


@dataclass(frozen=True)
class Change:
    path: str
    op: str
    before: SnapshotEntry | None
    after: SnapshotEntry | None

    def __post_init__(self) -> None:
        validate_relative_path(self.path)
        if self.op not in {"add", "delete", "modify"}:
            raise CanonicalizationError("change_operation_invalid")
        if self.op == "add" and (self.before is not None or self.after is None):
            raise CanonicalizationError("change_add_invalid")
        if self.op == "delete" and (self.before is None or self.after is not None):
            raise CanonicalizationError("change_delete_invalid")
        if self.op == "modify" and (self.before is None or self.after is None):
            raise CanonicalizationError("change_modify_invalid")
        if self.before is not None and self.before.path != self.path:
            raise CanonicalizationError("change_before_path_mismatch")
        if self.after is not None and self.after.path != self.path:
            raise CanonicalizationError("change_after_path_mismatch")

    def as_dict(self) -> dict[str, Any]:
        return {
            "after": self.after.as_dict() if self.after else None,
            "before": self.before.as_dict() if self.before else None,
            "op": self.op,
            "path": self.path,
        }


@dataclass(frozen=True)
class ChangeSet:
    baseline: str
    result: str
    changes: tuple[Change, ...]
    changeset_id: str = field(init=False)

    def __post_init__(self) -> None:
        validate_digest(self.baseline, field_name="baseline")
        validate_digest(self.result, field_name="result")
        changes = tuple(sorted(self.changes, key=lambda item: _sort_key(item.path)))
        if len({item.path.casefold() for item in changes}) != len(changes):
            raise CanonicalizationError("changeset_case_collision")
        object.__setattr__(self, "changes", changes)
        object.__setattr__(self, "changeset_id", _hash_object(self.as_dict()))

    def as_dict(self) -> dict[str, Any]:
        return {
            "baseline": self.baseline,
            "changes": [change.as_dict() for change in self.changes],
            "format": CHANGESET_FORMAT,
            "result": self.result,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json(self.as_dict())


def derive_changeset(baseline: SnapshotManifest, result: SnapshotManifest) -> ChangeSet:
    """Derive changes only from complete Core snapshots."""
    before = baseline.by_path()
    after = result.by_path()
    changes: list[Change] = []
    for path in sorted(set(before) | set(after), key=_sort_key):
        old = before.get(path)
        new = after.get(path)
        if old is None:
            changes.append(Change(path, "add", None, new))
        elif new is None:
            changes.append(Change(path, "delete", old, None))
        elif old != new:
            changes.append(Change(path, "modify", old, new))
    return ChangeSet(baseline.snapshot_id, result.snapshot_id, tuple(changes))


@dataclass(frozen=True)
class Candidate:
    changeset_id: str
    requirements_snapshot_id: str
    validation_contract_snapshot_id: str
    candidate_id: str = field(init=False)

    def __post_init__(self) -> None:
        validate_digest(self.changeset_id, field_name="changeset")
        validate_digest(self.requirements_snapshot_id, field_name="requirements")
        validate_digest(self.validation_contract_snapshot_id, field_name="validation")
        object.__setattr__(self, "candidate_id", _hash_object(self.as_dict()))

    def as_dict(self) -> dict[str, str]:
        return {
            "changeset": self.changeset_id,
            "format": CANDIDATE_FORMAT,
            "requirements": self.requirements_snapshot_id,
            "validation": self.validation_contract_snapshot_id,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json(self.as_dict())


@dataclass(frozen=True)
class Publication:
    candidate_id: str
    task_id: str | None
    generation_revision: int | None
    run_id: str | None
    lineage_ref: str
    provenance: Mapping[str, Any]
    publication_id: str = field(init=False)

    def __post_init__(self) -> None:
        validate_digest(self.candidate_id, field_name="candidate")
        if not self.lineage_ref.strip():
            raise CanonicalizationError("publication_lineage_missing")
        object.__setattr__(self, "provenance", dict(self.provenance))
        object.__setattr__(
            self,
            "publication_id",
            "publication_" + hashlib.sha256(os.urandom(16)).hexdigest()[:32],
        )


class Requiredness(StrEnum):
    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"


class Applicability(StrEnum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNKNOWN = "UNKNOWN"


class VerificationOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class Validity(StrEnum):
    VALID = "VALID"
    STALE = "STALE"
    MISMATCH = "MISMATCH"
    INVALID = "INVALID"


class AssuranceMode(StrEnum):
    FLEXIBLE = "FLEXIBLE"
    STANDARD = "STANDARD"
    VERIFIED = "VERIFIED"


class AssuranceStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    SELF_REVIEWED = "SELF_REVIEWED"
    CROSS_REVIEWED = "CROSS_REVIEWED"
    VERIFIED = "VERIFIED"


def parse_validation_contract(value: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    """Parse the small immutable validation contract used by D1b.

    The contract is deliberately data-only: Core owns the requiredness and
    check identifiers, while a runner can only submit observations for the
    declared checks.  This prevents a caller from inventing a passing check at
    verification time.
    """
    if not isinstance(value, Mapping) or value.get("format") != VALIDATION_CONTRACT_FORMAT:
        raise EvidenceBindingError("validation_contract_format_invalid")
    revision = value.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise EvidenceBindingError("validation_contract_revision_invalid")
    checks = value.get("checks")
    if not isinstance(checks, list) or not checks:
        raise EvidenceBindingError("validation_contract_checks_invalid")
    parsed: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in checks:
        if not isinstance(item, Mapping):
            raise EvidenceBindingError("validation_contract_check_invalid")
        check_id = item.get("check_id")
        if not isinstance(check_id, str) or not check_id.strip() or len(check_id) > 256:
            raise EvidenceBindingError("validation_contract_check_id_invalid")
        if check_id in seen:
            raise EvidenceBindingError("validation_contract_duplicate_check")
        seen.add(check_id)
        try:
            requiredness = Requiredness(item.get("requiredness", Requiredness.REQUIRED.value))
        except (TypeError, ValueError) as exc:
            raise EvidenceBindingError("validation_contract_requiredness_invalid") from exc
        applicability = item.get("applicability", Applicability.APPLICABLE.value)
        if applicability == "UNRESOLVED":
            applicability = Applicability.UNKNOWN.value
        try:
            applicability = Applicability(applicability)
        except (TypeError, ValueError) as exc:
            raise EvidenceBindingError("validation_contract_applicability_invalid") from exc
        predicate = item.get("applicability_predicate")
        if predicate is not None and (not isinstance(predicate, str) or not predicate.strip()):
            raise EvidenceBindingError("validation_contract_predicate_invalid")
        parsed.append({
            "check_id": check_id,
            "requiredness": requiredness.value,
            "applicability": applicability.value,
            "applicability_predicate": predicate,
        })
    if not any(item["requiredness"] == Requiredness.REQUIRED.value for item in parsed):
        raise EvidenceBindingError("validation_contract_required_gate_missing")
    return tuple(parsed)


@dataclass(frozen=True)
class EvidenceObservation:
    candidate_id: str
    contract_id: str
    check_id: str
    evidence_type: str
    actor_id: str
    source: str
    requiredness: Requiredness
    applicability: Applicability
    outcome: VerificationOutcome
    validity: Validity
    command: str | None = None
    cwd: str | None = None
    argv: tuple[str, ...] = ()
    runner_exit: int | None = None
    child_exit: int | None = None
    raw_artifact_ref: str | None = None
    raw_artifact_sha256: str | None = None
    freshness: str = "CURRENT"
    provenance: Mapping[str, Any] = field(default_factory=dict)
    reason: str | None = None
    observed_at: datetime = field(default_factory=utc_now)
    evidence_id: str = field(default_factory=lambda: "evidence_" + hashlib.sha256(os.urandom(16)).hexdigest()[:32])

    def __post_init__(self) -> None:
        validate_digest(self.candidate_id, field_name="candidate")
        if not self.contract_id or not self.check_id or not self.actor_id or not self.source:
            raise EvidenceBindingError("evidence_binding_missing")
        if self.outcome is VerificationOutcome.SKIPPED and self.requiredness is Requiredness.REQUIRED:
            # Required skips remain representable as evidence, but can never
            # be turned into a passing mandatory gate.
            pass
        if self.runner_exit is not None and (not isinstance(self.runner_exit, int) or isinstance(self.runner_exit, bool)):
            raise EvidenceBindingError("runner_exit_invalid")
        if self.child_exit is not None and (not isinstance(self.child_exit, int) or isinstance(self.child_exit, bool)):
            raise EvidenceBindingError("child_exit_invalid")
        object.__setattr__(self, "argv", tuple(self.argv))
        object.__setattr__(self, "provenance", dict(self.provenance))

    def as_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "applicability": self.applicability.value,
            "argv": list(self.argv),
            "candidate_id": self.candidate_id,
            "check_id": self.check_id,
            "child_exit": self.child_exit,
            "command": self.command,
            "contract_id": self.contract_id,
            "cwd": self.cwd,
            "evidence_id": self.evidence_id,
            "evidence_type": self.evidence_type,
            "freshness": self.freshness,
            "observed_at": self.observed_at.isoformat(),
            "outcome": self.outcome.value,
            "provenance": dict(self.provenance),
            "raw_artifact_ref": self.raw_artifact_ref,
            "raw_artifact_sha256": self.raw_artifact_sha256,
            "reason": self.reason,
            "requiredness": self.requiredness.value,
            "runner_exit": self.runner_exit,
            "source": self.source,
            "validity": self.validity.value,
        }


@dataclass(frozen=True)
class VerificationResult:
    candidate_id: str
    contract_id: str
    outcome: str
    validity: Validity
    mandatory_pass: bool
    complete: bool
    failures: tuple[str, ...] = ()
    optional_failures: tuple[str, ...] = ()
    verification_id: str = field(default_factory=lambda: "verification_" + hashlib.sha256(os.urandom(16)).hexdigest()[:32])

    @property
    def acceptance_eligible(self) -> bool:
        return self.mandatory_pass and self.validity is Validity.VALID and self.outcome == "PASS"

    def as_dict(self) -> dict[str, Any]:
        return {
            "acceptance_eligible": self.acceptance_eligible,
            "candidate_id": self.candidate_id,
            "complete": self.complete,
            "contract_id": self.contract_id,
            "failures": list(self.failures),
            "mandatory_pass": self.mandatory_pass,
            "optional_failures": list(self.optional_failures),
            "outcome": self.outcome,
            "validity": self.validity.value,
            "verification_id": self.verification_id,
        }


def evaluate_verification(
    candidate_id: str,
    contract_id: str,
    observations: Sequence[EvidenceObservation],
    *,
    expected_checks: Sequence[Mapping[str, Any]] | None = None,
) -> VerificationResult:
    validate_digest(candidate_id, field_name="candidate")
    if not contract_id:
        raise EvidenceBindingError("contract_missing")
    failures: list[str] = []
    optional_failures: list[str] = []
    complete = True
    stale = False
    applicable_required = False
    required_outcomes: list[VerificationOutcome] = []
    expected_by_id: dict[str, Mapping[str, Any]] = {}
    if expected_checks is not None:
        for item in expected_checks:
            check_id = item.get("check_id") if isinstance(item, Mapping) else None
            if not isinstance(check_id, str) or check_id in expected_by_id:
                raise EvidenceBindingError("validation_contract_check_invalid")
            expected_by_id[check_id] = item
    observed_by_id: dict[str, EvidenceObservation] = {}
    for observation in observations:
        if observation.candidate_id != candidate_id or observation.contract_id != contract_id:
            raise EvidenceBindingError("evidence_cross_candidate_or_contract")
        if observation.check_id in observed_by_id:
            raise EvidenceBindingError("duplicate_check_observation")
        observed_by_id[observation.check_id] = observation
        expected = expected_by_id.get(observation.check_id)
        if expected_checks is not None and expected is None:
            raise EvidenceBindingError("validation_contract_check_unknown")
        if expected is not None:
            expected_requiredness = expected.get("requiredness", Requiredness.REQUIRED.value)
            if observation.requiredness.value != expected_requiredness:
                raise EvidenceBindingError("validation_contract_requiredness_mismatch")
            expected_applicability = expected.get("applicability", Applicability.APPLICABLE.value)
            if expected_applicability == "UNRESOLVED":
                expected_applicability = Applicability.UNKNOWN.value
            if observation.applicability.value != expected_applicability:
                raise EvidenceBindingError("validation_contract_applicability_mismatch")
            expected_predicate = expected.get("applicability_predicate")
            observed_predicate = observation.provenance.get("applicability_predicate")
            if observed_predicate != expected_predicate:
                raise EvidenceBindingError("validation_contract_applicability_mismatch")
        is_required = observation.requiredness is Requiredness.REQUIRED
        # A model/agent assertion is not tool-backed evidence.  It remains
        # serialisable for audit, but it can never satisfy a required gate.
        opinion_marker = " ".join(
            (observation.source, observation.evidence_type)
        ).upper()
        ai_opinion = any(
            marker in opinion_marker
            for marker in ("AI_OPINION", "AGENT_OPINION", "MODEL_OPINION", "OPINION_ONLY")
        ) and not observation.raw_artifact_ref
        if ai_opinion:
            if is_required:
                failures.append(f"{observation.check_id}:ai_opinion_not_tool")
            else:
                optional_failures.append(f"{observation.check_id}:ai_opinion_not_tool")
            complete = False if is_required else complete
            continue
        if observation.validity is not Validity.VALID or observation.freshness != "CURRENT":
            if is_required:
                failures.append(f"{observation.check_id}:invalid_or_stale")
                stale = True
                complete = False
            continue
        if observation.applicability is Applicability.UNKNOWN:
            if is_required:
                failures.append(f"{observation.check_id}:applicability_unknown")
            complete = False
            continue
        if observation.applicability is Applicability.NOT_APPLICABLE:
            if not observation.reason or not observation.provenance.get("applicability_predicate"):
                if is_required:
                    failures.append(f"{observation.check_id}:unproven_not_applicable")
                complete = False
            continue
        if is_required:
            applicable_required = True
        if observation.outcome is VerificationOutcome.SKIPPED:
            if is_required:
                failures.append(f"{observation.check_id}:required_skipped")
                complete = False
            continue
        if is_required:
            required_outcomes.append(observation.outcome)
        if observation.outcome is not VerificationOutcome.PASS:
            if is_required:
                failures.append(f"{observation.check_id}:{observation.outcome.value.lower()}")
            else:
                optional_failures.append(f"{observation.check_id}:{observation.outcome.value.lower()}")
    if expected_checks is not None:
        for check_id, expected in expected_by_id.items():
            if check_id in observed_by_id:
                continue
            is_required = expected.get("requiredness", Requiredness.REQUIRED.value) == Requiredness.REQUIRED.value
            if is_required:
                failures.append(f"{check_id}:missing")
                complete = False
            else:
                optional_failures.append(f"{check_id}:missing")
    if not observations:
        complete = False
        failures.append("evidence_missing")
    if not applicable_required and observations:
        # A contract with no required check is not evidence of a verified
        # result; the caller must make that applicability explicit.
        complete = False
        failures.append("required_gate_set_missing")
    if failures:
        blocking_suffixes = (":invalid_or_stale", ":applicability_unknown", ":required_skipped", ":unproven_not_applicable", ":ai_opinion_not_tool")
        if any(item.endswith(blocking_suffixes) for item in failures):
            outcome = "BLOCKED"
        elif VerificationOutcome.TIMEOUT in required_outcomes:
            outcome = VerificationOutcome.TIMEOUT.value
        elif VerificationOutcome.ERROR in required_outcomes:
            outcome = VerificationOutcome.ERROR.value
        else:
            outcome = "FAIL"
    else:
        outcome = "PASS"
    validity = Validity.STALE if stale else (Validity.VALID if complete else Validity.INVALID)
    return VerificationResult(
        candidate_id=candidate_id,
        contract_id=contract_id,
        outcome=outcome,
        validity=validity,
        mandatory_pass=not failures,
        complete=complete,
        failures=tuple(failures),
        optional_failures=tuple(optional_failures),
    )


def derive_assurance_status(
    mode: AssuranceMode,
    *,
    self_review: bool = False,
    cross_review: bool = False,
    verification: VerificationResult | None = None,
    review_profile_satisfied: bool = True,
) -> AssuranceStatus:
    if not isinstance(mode, AssuranceMode):
        raise AssuranceError("assurance_mode_invalid")
    if verification is not None and verification.candidate_id:
        verified = (
            verification.complete
            and verification.validity is Validity.VALID
            and verification.outcome in {"PASS", "FAIL"}
            and review_profile_satisfied
        )
        if mode is AssuranceMode.VERIFIED and verified:
            return AssuranceStatus.VERIFIED
        # STANDARD describes the required independent review depth.  It does
        # not silently promote the result to deterministic VERIFIED; only the
        # explicit VERIFIED mode plus its exact deterministic contract can do
        # that.  Verification outcome and assurance depth remain separate.
    if cross_review and review_profile_satisfied:
        return AssuranceStatus.CROSS_REVIEWED
    if self_review:
        return AssuranceStatus.SELF_REVIEWED
    return AssuranceStatus.UNREVIEWED


def manifest_from_json(value: str) -> SnapshotManifest:
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CanonicalizationError("snapshot_json_invalid") from exc
    return SnapshotManifest.from_dict(parsed)


def changeset_from_json(value: str) -> ChangeSet:
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise CanonicalizationError("changeset_json_invalid") from exc
    if parsed.get("format") != CHANGESET_FORMAT or not isinstance(parsed.get("changes"), list):
        raise CanonicalizationError("changeset_json_invalid")
    def parse_entry(item: Any) -> SnapshotEntry | None:
        return None if item is None else SnapshotEntry(**item)
    changes = tuple(Change(item["path"], item["op"], parse_entry(item.get("before")), parse_entry(item.get("after"))) for item in parsed["changes"])
    result = ChangeSet(parsed["baseline"], parsed["result"], changes)
    if result.canonical_bytes != canonical_json(parsed):
        raise CanonicalizationError("changeset_canonical_mismatch")
    return result
