"""Run-scoped contracts for an externally implemented local executor.

The envelope is deliberately a Core-owned, immutable description of one
dispatch.  It is not a provider configuration format and it never contains a
credential, prompt transcript, or raw tool output.  A target adapter may use
the envelope to launch a process, but it cannot widen the working directory,
input/output allowlist, or egress declarations after binding.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping


class ExternalContractError(ValueError):
    """A bounded external dispatch contract cannot be established."""


class EgressChannel(StrEnum):
    PROVIDER_MODEL = "PROVIDER_MODEL_EGRESS"
    AGENT_EXTENSION = "AGENT_EXTENSION_EGRESS"


class EgressDisposition(StrEnum):
    DENY = "DENY"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    RUNTIME_MANAGED = "RUNTIME_MANAGED"


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9._-]{0,63}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SENSITIVE_ARGUMENT = re.compile(
    r"(?i)(token|secret|password|cookie|authorization|api[_-]?key|credential)"
)


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ExternalContractError(f"{field}_invalid")
    return value


def _plain(path: Path) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise ExternalContractError("path_unavailable") from exc
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ExternalContractError("path_reparse_unsupported")


def _absolute_plain_directory(value: object, field: str) -> Path:
    if not isinstance(value, Path) or not value.is_absolute():
        raise ExternalContractError(f"{field}_invalid")
    candidate = value.resolve(strict=False)
    for ancestor in (candidate, *candidate.parents):
        if ancestor.exists():
            _plain(ancestor)
    if not candidate.is_dir():
        raise ExternalContractError(f"{field}_unavailable")
    return candidate


def relative_path(value: object) -> str:
    """Validate a repository-relative path without allowing traversal."""

    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ExternalContractError("relative_path_invalid")
    if value.startswith("/") or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ExternalContractError("relative_path_invalid")
    if any(part.casefold() == ".git" for part in value.split("/")):
        raise ExternalContractError("relative_path_forbidden")
    if any(ord(char) < 32 for char in value):
        raise ExternalContractError("relative_path_invalid")
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _file_digest(root: Path, paths: tuple[str, ...]) -> str:
    """Hash the allowlisted file observations, including absence and metadata."""

    observations: list[dict[str, object]] = []
    for relative in paths:
        path = root / relative
        try:
            _plain(path)
            info = path.stat()
        except FileNotFoundError:
            observations.append({"path": relative, "state": "ABSENT"})
            continue
        except OSError as exc:
            raise ExternalContractError("staging_observation_failed") from exc
        if not stat.S_ISREG(info.st_mode):
            raise ExternalContractError("staging_input_not_regular")
        try:
            content = path.read_bytes()
            after = path.stat()
        except OSError as exc:
            raise ExternalContractError("staging_observation_failed") from exc
        if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ):
            raise ExternalContractError("staging_changed_during_observation")
        observations.append(
            {
                "path": relative,
                "state": "FILE",
                "mode": stat.S_IMODE(info.st_mode),
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return hashlib.sha256(_canonical(observations)).hexdigest()


def executable_digest(path: Path) -> str:
    """Read only the executable bytes needed for provenance; no config/secret."""

    if not path.is_absolute():
        raise ExternalContractError("executable_path_invalid")
    _plain(path)
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ExternalContractError("executable_path_invalid")
        content = path.read_bytes()
    except OSError as exc:
        raise ExternalContractError("executable_unavailable") from exc
    return hashlib.sha256(content).hexdigest()


def _argument_tuple(arguments: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(arguments, tuple) or any(not isinstance(value, str) for value in arguments):
        raise ExternalContractError("arguments_invalid")
    if any(_SENSITIVE_ARGUMENT.search(value) for value in arguments):
        raise ExternalContractError("credential_argument_forbidden")
    return arguments


@dataclass(frozen=True)
class ExecutionEnvelope:
    """Immutable, run-scoped external dispatch envelope."""

    run_id: str
    task_id: str
    project_id: str
    staging_root: Path
    allowed_inputs: tuple[str, ...]
    allowed_outputs: tuple[str, ...]
    executable_path: Path
    executable_sha256: str
    executable_version: str
    arguments: tuple[str, ...]
    config_sources: tuple[str, ...]
    egress: Mapping[EgressChannel, EgressDisposition]
    input_manifest_sha256: str
    envelope_sha256: str = ""

    def __post_init__(self) -> None:
        for field, value in (
            ("run_id", self.run_id),
            ("task_id", self.task_id),
            ("project_id", self.project_id),
            ("executable_version", self.executable_version),
        ):
            _identifier(value, field)
        staging = _absolute_plain_directory(self.staging_root, "staging_root")
        inputs = tuple(sorted({relative_path(item) for item in self.allowed_inputs}))
        outputs = tuple(sorted({relative_path(item) for item in self.allowed_outputs}))
        if not set(inputs).issubset(set(outputs)):
            raise ExternalContractError("input_allowlist_not_output_scoped")
        executable = self.executable_path.resolve(strict=False)
        digest = self.executable_sha256
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ExternalContractError("executable_digest_invalid")
        if not isinstance(self.input_manifest_sha256, str) or not _SHA256.fullmatch(
            self.input_manifest_sha256
        ):
            raise ExternalContractError("input_manifest_invalid")
        arguments = _argument_tuple(self.arguments)
        sources = tuple(sorted(_identifier(value, "config_source") for value in self.config_sources))
        egress = dict(self.egress)
        if set(egress) != set(EgressChannel):
            raise ExternalContractError("egress_channels_incomplete")
        if any(not isinstance(key, EgressChannel) or not isinstance(value, EgressDisposition) for key, value in egress.items()):
            raise ExternalContractError("egress_policy_invalid")
        if not executable.is_absolute():
            raise ExternalContractError("executable_path_invalid")
        object.__setattr__(self, "staging_root", staging)
        object.__setattr__(self, "allowed_inputs", inputs)
        object.__setattr__(self, "allowed_outputs", outputs)
        object.__setattr__(self, "executable_path", executable)
        object.__setattr__(self, "arguments", arguments)
        object.__setattr__(self, "config_sources", sources)
        object.__setattr__(self, "egress", egress)
        expected = self._fingerprint_payload()
        fingerprint = hashlib.sha256(_canonical(expected)).hexdigest()
        if self.envelope_sha256 and self.envelope_sha256 != fingerprint:
            raise ExternalContractError("envelope_identity_mismatch")
        object.__setattr__(self, "envelope_sha256", fingerprint)

    def _fingerprint_payload(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "project_id": self.project_id,
            "staging_root": os.path.normcase(str(self.staging_root)),
            "allowed_inputs": self.allowed_inputs,
            "allowed_outputs": self.allowed_outputs,
            "executable_path": os.path.normcase(str(self.executable_path)),
            "executable_sha256": self.executable_sha256,
            "executable_version": self.executable_version,
            "arguments": self.arguments,
            "config_sources": self.config_sources,
            "egress": {key.value: value.value for key, value in self.egress.items()},
            "input_manifest_sha256": self.input_manifest_sha256,
        }

    def verify_staging(self) -> None:
        """Re-check the immutable boundary before importing any output."""

        current = _absolute_plain_directory(self.staging_root, "staging_root")
        if current != self.staging_root:
            raise ExternalContractError("staging_identity_changed")
        if executable_digest(self.executable_path) != self.executable_sha256:
            raise ExternalContractError("executable_identity_changed")

    def current_input_manifest(self) -> str:
        self.verify_staging()
        return _file_digest(self.staging_root, self.allowed_inputs)

    def assert_quiescent_input(self) -> None:
        """Reject a changed input observation rather than importing stale output."""

        if self.current_input_manifest() != self.input_manifest_sha256:
            raise ExternalContractError("input_manifest_changed")


def make_envelope(
    *,
    run_id: str,
    task_id: str,
    project_id: str,
    staging_root: Path,
    allowed_inputs: tuple[str, ...],
    allowed_outputs: tuple[str, ...],
    executable_path: Path,
    executable_version: str,
    arguments: tuple[str, ...],
    config_sources: tuple[str, ...],
    egress: Mapping[EgressChannel, EgressDisposition],
) -> ExecutionEnvelope:
    """Build and hash a new envelope after observing the staged inputs."""

    staging = _absolute_plain_directory(staging_root, "staging_root")
    normalized_inputs = tuple(sorted({relative_path(item) for item in allowed_inputs}))
    manifest = _file_digest(staging, normalized_inputs)
    executable = executable_path.resolve(strict=False)
    return ExecutionEnvelope(
        run_id=run_id,
        task_id=task_id,
        project_id=project_id,
        staging_root=staging,
        allowed_inputs=normalized_inputs,
        allowed_outputs=tuple(sorted({relative_path(item) for item in allowed_outputs})),
        executable_path=executable,
        executable_sha256=executable_digest(executable),
        executable_version=executable_version,
        arguments=arguments,
        config_sources=config_sources,
        egress=egress,
        input_manifest_sha256=manifest,
    )
