"""One normalized, bounded output-redaction boundary for runtime data.

The runtime adapter is not trusted to make exception text, paths, credentials,
or payload sizes safe.  This module deliberately keeps PolyNexus identifiers
and lifecycle values intact while sanitizing human-readable output before it
is persisted or returned through an API.
"""

from __future__ import annotations

import re
import json
from dataclasses import replace
from typing import Any, Mapping

from polynexus_core.domain.models import (
    Artifact,
    Evidence,
    Finding,
    Run,
    RunEvent,
    RunResult,
)
from polynexus_core.runtime.contracts import RuntimeResult


MAX_TEXT_LENGTH = 4096
MAX_COLLECTION_ITEMS = 64
MAX_NESTING_DEPTH = 4

REDACTED = "[REDACTED]"
PATH_REDACTED = "[PATH_REDACTED]"
TRUNCATED = "[TRUNCATED]"

# These patterns are intentionally conservative.  They protect common
# credential forms and marker-style test secrets without treating all normal
# runtime identifiers as secrets.
_ASSIGNED_SECRET = re.compile(
    r"(?ix)\b"
    r"(api[_ -]?key|access[_ -]?token|authorization|auth|bearer|"
    r"credential|password|passwd|private[_ -]?key|secret|token)"
    r"\s*[:=]\s*[^\s,;]+"
)
_BEARER_SECRET = re.compile(r"(?i)\bBearer\s+[^\s,;]+")
_SENSITIVE_VALUE_PHRASE = re.compile(
    r"(?ix)\b"
    r"(api[_ -]?key|access[_ -]?token|credential|password|passwd|"
    r"secret|token)"
    r"\s+(?:value|fragment|text)\s*[:=]?\s*[^\s,;]+"
)
_MARKER_SECRET = re.compile(
    r"(?i)\b(?:secret|token|password|credential|api[_-]?key)"
    r"[_-][A-Za-z0-9][A-Za-z0-9._-]*\b"
)
_WINDOWS_PATH = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\s,;]+")
_UNC_PATH = re.compile(r"(?<![A-Za-z0-9_])\\\\[^\s,;]+")
_POSIX_PATH = re.compile(r"(?<![A-Za-z0-9_])/(?:[^\s,;]+/)+[^\s,;]*")


def redact_text(
    value: object,
    *,
    fallback: str = REDACTED,
    max_length: int = MAX_TEXT_LENGTH,
) -> str:
    """Return bounded text with common secret/path forms removed.

    ``fallback`` is used only when the value cannot be represented safely as
    text.  Callers handling exceptions should use :func:`redact_exception`
    instead, because exception text is never an approved output source.
    """

    if value is None:
        text = fallback
    elif isinstance(value, str):
        text = value
    else:
        try:
            text = str(value)
        except Exception:
            text = fallback

    from polynexus_core.security.secret_refs import redact_active_secret
    text = redact_active_secret(text)
    text = _ASSIGNED_SECRET.sub(lambda match: f"{match.group(1)}={REDACTED}", text)
    text = _BEARER_SECRET.sub(f"Bearer {REDACTED}", text)
    text = _SENSITIVE_VALUE_PHRASE.sub(lambda match: f"{match.group(1)} {REDACTED}", text)
    text = _MARKER_SECRET.sub(REDACTED, text)
    text = _WINDOWS_PATH.sub(PATH_REDACTED, text)
    text = _UNC_PATH.sub(PATH_REDACTED, text)
    text = _POSIX_PATH.sub(PATH_REDACTED, text)

    if max_length < 1:
        return ""
    if len(text) <= max_length:
        return text
    suffix = f" {TRUNCATED}"
    return text[: max(0, max_length - len(suffix))] + suffix


def redact_exception(_error: BaseException, *, fallback: str) -> str:
    """Return a public-safe reason without inspecting exception text."""

    return redact_text(fallback, fallback=fallback)


def redact_value(value: object, *, depth: int = 0) -> object:
    """Recursively sanitize JSON-like metadata with depth/item bounds."""

    if depth >= MAX_NESTING_DEPTH:
        return REDACTED
    if isinstance(value, str):
        return redact_text(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, Mapping):
        output: dict[str, object] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= MAX_COLLECTION_ITEMS:
                output[TRUNCATED] = TRUNCATED
                break
            safe_key = redact_text(key, max_length=256)
            output[safe_key] = redact_value(item, depth=depth + 1)
        return output
    if isinstance(value, (list, tuple, set, frozenset)):
        return [
            redact_value(item, depth=depth + 1)
            for item in list(value)[:MAX_COLLECTION_ITEMS]
        ]
    return REDACTED


def sanitize_event(event: RunEvent) -> RunEvent:
    """Sanitize only the public reason while retaining event identity/timing."""

    return replace(
        event,
        reason=(redact_text(event.reason) if event.reason is not None else None),
    )


def sanitize_result(result: RunResult | None) -> RunResult | None:
    if result is None:
        return None
    return replace(result, summary=redact_text(result.summary))


def sanitize_evidence(evidence: Evidence) -> Evidence:
    return replace(
        evidence,
        actor_id=redact_text(evidence.actor_id, max_length=256),
        source=redact_text(evidence.source, max_length=256),
        artifact_refs=tuple(redact_text(ref, max_length=512) for ref in evidence.artifact_refs),
        metadata=sanitize_metadata(evidence.metadata),
    )


def sanitize_finding(finding: Finding) -> Finding:
    return replace(
        finding,
        title=redact_text(finding.title, max_length=512),
        description=redact_text(finding.description),
        evidence_refs=tuple(redact_text(ref, max_length=256) for ref in finding.evidence_refs),
    )


def sanitize_artifact(artifact: Artifact) -> Artifact:
    return replace(
        artifact,
        mime_type=redact_text(artifact.mime_type, max_length=256),
        source_type=redact_text(artifact.source_type, max_length=256),
        storage_ref=redact_text(artifact.storage_ref, max_length=1024),
        sha256=redact_text(artifact.sha256, max_length=128),
    )


def sanitize_runtime_result(result: RuntimeResult) -> RuntimeResult:
    """Sanitize all adapter-produced output before Core persistence."""

    return replace(
        result,
        summary=redact_text(result.summary),
        evidence=tuple(sanitize_evidence(item) for item in result.evidence),
        findings=tuple(sanitize_finding(item) for item in result.findings),
        artifacts=tuple(sanitize_artifact(item) for item in result.artifacts),
    )


def sanitize_run(run: Run) -> Run:
    """Sanitize mutable Run output in place and return the same Run object."""

    run.events = [sanitize_event(event) for event in run.events]
    run.result = sanitize_result(run.result)
    return run


def sanitize_metadata(metadata: Mapping[str, Any]) -> dict[str, object]:
    """Sanitize metadata while preserving safe scalar types for persistence."""

    value = redact_value(metadata)
    if not isinstance(value, dict):
        return {REDACTED: REDACTED}

    return {str(key): item for key, item in value.items()}


def sanitize_metadata_for_api(metadata: Mapping[str, Any]) -> dict[str, str]:
    """Convert sanitized metadata to the API's string-valued schema."""

    value = sanitize_metadata(metadata)

    output: dict[str, str] = {}
    for key, item in value.items():
        if isinstance(item, str):
            output[str(key)] = item
            continue
        try:
            encoded = json.dumps(item, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        except (TypeError, ValueError):
            encoded = REDACTED
        output[str(key)] = redact_text(encoded)
    return output
