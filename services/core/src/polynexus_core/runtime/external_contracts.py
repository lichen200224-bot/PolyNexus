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
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Mapping
from types import MappingProxyType


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


def _safe_relative(root: Path, value: str) -> Path:
    """Resolve one relative path while rejecting every reparse ancestor."""

    relative = relative_path(value)
    base = root.resolve(strict=False)
    candidate = base / relative
    try:
        canonical = candidate.resolve(strict=False)
    except OSError as exc:
        raise ExternalContractError("path_unavailable") from exc
    if not canonical.is_relative_to(base):
        raise ExternalContractError("path_escape")
    current = candidate
    while current != base and current != current.parent:
        try:
            current.lstat()
            exists = True
        except FileNotFoundError:
            exists = False
        except OSError as exc:
            raise ExternalContractError("path_unavailable") from exc
        if exists:
            _plain(current)
        current = current.parent
    if current != base:
        raise ExternalContractError("path_escape")
    return candidate


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
        path = _safe_relative(root, relative)
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


def _projection_git(staging_root: Path, *arguments: str) -> None:
    """Run the bounded Core-owned Git setup for a projected staging root."""

    safe_names = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "PATH": os.environ.get("PATH", ""),
    }
    for name in ("COMSPEC", "PATHEXT", "SYSTEMROOT", "TEMP", "TMP", "WINDIR"):
        if name in os.environ:
            safe_names[name] = os.environ[name]
    result = subprocess.run(
        [
            "git",
            "-c",
            "user.name=PolyNexus projected staging",
            "-c",
            "user.email=runtime@invalid",
            *arguments,
        ],
        cwd=staging_root,
        env=safe_names,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise ExternalContractError("projected_staging_git_failed")


def create_projected_staging(
    *,
    source_root: Path,
    staging_root: Path,
    allowed_inputs: tuple[str, ...],
    allowed_outputs: tuple[str, ...],
) -> Path:
    """Create a new per-Run PROJECTED_STAGING Git workspace.

    Only the explicitly selected input files are copied.  The projection gets
    its own empty Git history so an external process cannot address the source
    repository, its parent, or an unselected baseline path.  The source tree is
    never modified.
    """

    source = _absolute_plain_directory(source_root, "source_root")
    inputs = tuple(sorted({relative_path(item) for item in allowed_inputs}))
    outputs = tuple(sorted({relative_path(item) for item in allowed_outputs}))
    if not outputs:
        raise ExternalContractError("output_allowlist_empty")
    if not isinstance(staging_root, Path) or not staging_root.is_absolute():
        raise ExternalContractError("projected_staging_invalid")
    staging = staging_root.resolve(strict=False)
    if staging.exists():
        raise ExternalContractError("projected_staging_already_exists")
    parent = _absolute_plain_directory(staging.parent, "projected_staging_parent")
    if staging == source or not staging.is_relative_to(parent):
        raise ExternalContractError("projected_staging_invalid")
    staging.mkdir()
    try:
        # Inputs are readable projection material.  Outputs are an independent
        # write allowlist: an existing output is not copied unless it is also
        # explicitly allowlisted as input.
        for relative in inputs:
            source_path = _safe_relative(source, relative)
            if not source_path.exists():
                continue
            _plain(source_path)
            before = source_path.stat()
            if not stat.S_ISREG(before.st_mode):
                raise ExternalContractError("projected_input_not_regular")
            content = source_path.read_bytes()
            after = source_path.stat()
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                raise ExternalContractError("projected_input_changed")
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write(content)
        # Keep output-only paths observable by Git without exposing their
        # source bytes.  The executor sees a Core-created empty placeholder;
        # it must replace it to produce an importable diff.
        for relative in outputs:
            if relative in inputs:
                continue
            source_path = _safe_relative(source, relative)
            if source_path.exists() and not stat.S_ISREG(source_path.stat().st_mode):
                raise ExternalContractError("projected_output_not_regular")
            destination = staging / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb"):
                pass
        _projection_git(staging, "init", "--quiet")
        _projection_git(staging, "add", "--all")
        _projection_git(staging, "commit", "--quiet", "--allow-empty", "-m", "Core projected baseline")
    except Exception:
        # Keep the exact partial staging for bounded recovery diagnostics.  It
        # is a new Core-owned path and is never confused with source state.
        raise
    return staging


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
    workspace_scope_mode: str = "PROJECTED_STAGING"
    effective_runtime_configuration_fingerprint: str = ""
    permission_policy_fingerprint: str = ""
    route_policy_evidence_sha256: str = ""
    enabled_plugin_set: tuple[str, ...] = ("NONE",)
    enabled_mcp_set: tuple[str, ...] = ("NONE",)
    remote_skill_catalog_state: str = "NONE"
    input_quiescence_manifest_sha256: str = ""
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
        if not outputs:
            raise ExternalContractError("output_allowlist_empty")
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
        if self.workspace_scope_mode != "PROJECTED_STAGING":
            raise ExternalContractError("workspace_scope_mode_invalid")
        plugins = tuple(sorted(str(value) for value in self.enabled_plugin_set))
        mcps = tuple(sorted(str(value) for value in self.enabled_mcp_set))
        if not plugins or not mcps or any(not value for value in (*plugins, *mcps)):
            raise ExternalContractError("runtime_configuration_set_invalid")
        if self.remote_skill_catalog_state != "NONE" and not _SHA256.fullmatch(
            self.remote_skill_catalog_state
        ):
            raise ExternalContractError("runtime_skill_catalog_invalid")
        egress = dict(self.egress)
        if set(egress) != set(EgressChannel):
            raise ExternalContractError("egress_channels_incomplete")
        if any(not isinstance(key, EgressChannel) or not isinstance(value, EgressDisposition) for key, value in egress.items()):
            raise ExternalContractError("egress_policy_invalid")
        if not executable.is_absolute():
            raise ExternalContractError("executable_path_invalid")
        config_fingerprint = self.effective_runtime_configuration_fingerprint or hashlib.sha256(
            _canonical(
                {
                    "arguments": arguments,
                    "config_sources": sources,
                    "enabled_mcp_set": mcps,
                    "enabled_plugin_set": plugins,
                    "remote_skill_catalog_state": self.remote_skill_catalog_state,
                    "workspace_scope_mode": self.workspace_scope_mode,
                }
            )
        ).hexdigest()
        permission_fingerprint = self.permission_policy_fingerprint or hashlib.sha256(
            _canonical(
                {
                    "allowed_inputs": inputs,
                    "allowed_outputs": outputs,
                    "egress": {key.value: value.value for key, value in egress.items()},
                    "route_policy_evidence_sha256": self.route_policy_evidence_sha256,
                }
            )
        ).hexdigest()
        for field, value in (
            ("effective_runtime_configuration_fingerprint", config_fingerprint),
            ("permission_policy_fingerprint", permission_fingerprint),
        ):
            if not _SHA256.fullmatch(value):
                raise ExternalContractError(f"{field}_invalid")
        if self.route_policy_evidence_sha256 and not _SHA256.fullmatch(
            self.route_policy_evidence_sha256
        ):
            raise ExternalContractError("route_policy_evidence_invalid")
        quiescence_manifest = self.input_quiescence_manifest_sha256 or _file_digest(
            staging, tuple(path for path in inputs if path not in outputs)
        )
        if not _SHA256.fullmatch(quiescence_manifest):
            raise ExternalContractError("input_quiescence_manifest_invalid")
        object.__setattr__(self, "staging_root", staging)
        object.__setattr__(self, "allowed_inputs", inputs)
        object.__setattr__(self, "allowed_outputs", outputs)
        object.__setattr__(self, "executable_path", executable)
        object.__setattr__(self, "arguments", arguments)
        object.__setattr__(self, "config_sources", sources)
        object.__setattr__(self, "egress", MappingProxyType(egress))
        object.__setattr__(self, "enabled_plugin_set", plugins)
        object.__setattr__(self, "enabled_mcp_set", mcps)
        object.__setattr__(self, "effective_runtime_configuration_fingerprint", config_fingerprint)
        object.__setattr__(self, "permission_policy_fingerprint", permission_fingerprint)
        object.__setattr__(self, "input_quiescence_manifest_sha256", quiescence_manifest)
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
            "workspace_scope_mode": self.workspace_scope_mode,
            "effective_runtime_configuration_fingerprint": self.effective_runtime_configuration_fingerprint,
            "permission_policy_fingerprint": self.permission_policy_fingerprint,
            "route_policy_evidence_sha256": self.route_policy_evidence_sha256,
            "enabled_plugin_set": self.enabled_plugin_set,
            "enabled_mcp_set": self.enabled_mcp_set,
            "remote_skill_catalog_state": self.remote_skill_catalog_state,
            "input_manifest_sha256": self.input_manifest_sha256,
            "input_quiescence_manifest_sha256": self.input_quiescence_manifest_sha256,
        }

    def verify_staging(self) -> None:
        """Re-check the immutable boundary before importing any output."""

        current = _absolute_plain_directory(self.staging_root, "staging_root")
        if current != self.staging_root:
            raise ExternalContractError("staging_identity_changed")
        if self.workspace_scope_mode != "PROJECTED_STAGING" or not (self.staging_root / ".git").exists():
            raise ExternalContractError("projected_staging_required")
        if executable_digest(self.executable_path) != self.executable_sha256:
            raise ExternalContractError("executable_identity_changed")
        for relative in (*self.allowed_inputs, *self.allowed_outputs):
            _safe_relative(self.staging_root, relative)
        expected = hashlib.sha256(_canonical(self._fingerprint_payload())).hexdigest()
        if expected != self.envelope_sha256:
            raise ExternalContractError("envelope_identity_changed")

    def current_input_manifest(self) -> str:
        self.verify_staging()
        return _file_digest(self.staging_root, self.allowed_inputs)

    def assert_quiescent_input(self) -> None:
        """Reject a changed input observation rather than importing stale output."""

        current = _file_digest(
            self.staging_root,
            tuple(path for path in self.allowed_inputs if path not in self.allowed_outputs),
        )
        if current != self.input_quiescence_manifest_sha256:
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
    effective_runtime_configuration_fingerprint: str = "",
    permission_policy_fingerprint: str = "",
    enabled_plugin_set: tuple[str, ...] = ("NONE",),
    enabled_mcp_set: tuple[str, ...] = ("NONE",),
    remote_skill_catalog_state: str = "NONE",
    route_policy_evidence_sha256: str = "",
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
        effective_runtime_configuration_fingerprint=effective_runtime_configuration_fingerprint,
        permission_policy_fingerprint=permission_policy_fingerprint,
        enabled_plugin_set=enabled_plugin_set,
        enabled_mcp_set=enabled_mcp_set,
        remote_skill_catalog_state=remote_skill_catalog_state,
        route_policy_evidence_sha256=route_policy_evidence_sha256,
    )
