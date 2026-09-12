"""Bounded, vendor-neutral contracts for external runtime modules (MCF-02).

The values in this module are configuration identities and policy decisions;
they never contain credentials or raw runtime configuration.  V1 deliberately
supports only Core-created projected staging workspaces and a preinstalled,
explicitly configured local executable.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from polynexus_core.domain.enums import AuthOwnership
from polynexus_core.domain.models import ContextPackage, Task
from polynexus_core.domain.runtime_binding import (
    RuntimeBindingError,
    RuntimeBindingSnapshot,
    validate_opaque_identifier,
)
from polynexus_core.runtime.contracts import RuntimeAdapter


EXTERNAL_CONTRACT_VERSION = 1
ACP_PROTOCOL_VERSION = 1
MAX_FRAME_BYTES = 1_048_576
MAX_STAGING_FILES = 256
MAX_STAGING_FILE_BYTES = 8 * 1024 * 1024
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+:-]{0,127}$")
_SENSITIVE = re.compile(
    r"(?:secret|token|password|credential|cookie|authorization|bearer|api[_-]?key)",
    re.IGNORECASE,
)
_FORBIDDEN_CONFIG_NAMES = frozenset(
    {"opencode.json", "opencode.jsonc", "mcp.json", ".mcp.json"}
)
_ALLOWED_CAPABILITIES = frozenset(
    {
        "session_create",
        "session_attach",
        "input_dispatch",
        "event_stream",
        "result_capture",
        "artifact_import",
        "artifact_export",
        "cancel",
        "cleanup",
        "health",
        "readiness",
        "permission_requests",
        "egress_declaration",
        "version_probe",
    }
)
_ALLOWED_PERMISSIONS = frozenset(
    {
        "workspace_read",
        "workspace_write",
        "process_execute",
        "provider_model_egress",
    }
)


class ExternalContractError(RuntimeBindingError):
    """Public-safe fail-closed external contract rejection."""


class ProtocolKind(StrEnum):
    ACP = "ACP"


class LaunchMode(StrEnum):
    LOCAL_CHILD = "LOCAL_CHILD"


class WorkspaceScopeMode(StrEnum):
    PROJECTED_STAGING = "PROJECTED_STAGING"


class EgressChannel(StrEnum):
    PROVIDER_MODEL_EGRESS = "PROVIDER_MODEL_EGRESS"
    AGENT_EXTENSION_EGRESS = "AGENT_EXTENSION_EGRESS"


class EgressDisposition(StrEnum):
    DENY = "DENY"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    APPROVED = "APPROVED"


def _safe_digest(value: object, field: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ExternalContractError(f"Invalid {field}")
    return value


def _safe_version(value: object, field: str) -> str:
    if not isinstance(value, str) or _PUBLIC_VERSION.fullmatch(value) is None:
        raise ExternalContractError(f"Invalid {field}")
    return value


def _canonical_digest(value: object) -> str:
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    except Exception:
        raise ExternalContractError("Configuration cannot be canonicalized") from None
    return hashlib.sha256(payload).hexdigest()


def _normalized_identifiers(values: Iterable[str], *, allowed: frozenset[str]) -> tuple[str, ...]:
    try:
        items = tuple(values)
    except Exception:
        raise ExternalContractError("Invalid external declaration") from None
    if any(type(item) is not str or item not in allowed for item in items):
        raise ExternalContractError("Invalid external declaration")
    if len(items) != len(set(items)):
        raise ExternalContractError("Duplicate external declaration")
    return tuple(sorted(items))


@dataclass(frozen=True, slots=True)
class EgressDeclaration:
    channel: EgressChannel
    disposition: EgressDisposition
    destination_ref: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.channel, EgressChannel) or not isinstance(
            self.disposition, EgressDisposition
        ):
            raise ExternalContractError("Invalid egress declaration")
        if self.channel is EgressChannel.AGENT_EXTENSION_EGRESS:
            if self.disposition is not EgressDisposition.DENY or self.destination_ref is not None:
                raise ExternalContractError("Agent extension egress must be denied")
        elif self.destination_ref is not None:
            validate_opaque_identifier(self.destination_ref, "destination_ref")


@dataclass(frozen=True, slots=True)
class ExecutableIdentity:
    resolved_path: str
    content_sha256: str
    observed_runtime_version: str

    def __post_init__(self) -> None:
        if not isinstance(self.resolved_path, str) or not os.path.isabs(self.resolved_path):
            raise ExternalContractError("Executable path must be canonical and absolute")
        _safe_digest(self.content_sha256, "executable content digest")
        _safe_version(self.observed_runtime_version, "observed runtime version")


@dataclass(frozen=True, slots=True)
class ControlledExecutionEnvelope:
    workspace_scope_mode: WorkspaceScopeMode
    workspace_identity: str
    workspace_content_fingerprint: str
    effective_runtime_configuration_fingerprint: str
    permission_policy_fingerprint: str
    enabled_plugin_set: tuple[str, ...]
    enabled_mcp_set: tuple[str, ...]
    remote_skill_catalog_state: tuple[str, ...]
    executable_identity: ExecutableIdentity
    execution_envelope_ref: str

    def __post_init__(self) -> None:
        if self.workspace_scope_mode is not WorkspaceScopeMode.PROJECTED_STAGING:
            raise ExternalContractError("Direct project workspace is not authorized")
        for name in (
            "workspace_identity",
            "workspace_content_fingerprint",
            "effective_runtime_configuration_fingerprint",
            "permission_policy_fingerprint",
            "execution_envelope_ref",
        ):
            _safe_digest(getattr(self, name), name)
        if type(self.enabled_plugin_set) is not tuple or self.enabled_plugin_set:
            raise ExternalContractError("V1 plugin set must be explicit NONE")
        if type(self.enabled_mcp_set) is not tuple or self.enabled_mcp_set:
            raise ExternalContractError("V1 MCP set must be explicit NONE")
        if type(self.remote_skill_catalog_state) is not tuple or self.remote_skill_catalog_state:
            raise ExternalContractError("V1 remote skill catalog must be explicit NONE")
        if not isinstance(self.executable_identity, ExecutableIdentity):
            raise ExternalContractError("Invalid executable identity")


@dataclass(frozen=True, slots=True)
class ExternalRuntimeDescriptor:
    contract_version: int
    module_id: str
    module_version: str
    provider_id: str
    runtime_id: str
    adapter_id: str
    runtime_profile_ref: str
    protocol_kind: ProtocolKind
    protocol_version: int
    launch_mode: LaunchMode
    capabilities: tuple[str, ...]
    permissions: tuple[str, ...]
    egress: tuple[EgressDeclaration, ...]
    auth_ownership: AuthOwnership
    conformance_ref: str
    execution_envelope_ref: str

    def __post_init__(self) -> None:
        if type(self.contract_version) is not int or self.contract_version != EXTERNAL_CONTRACT_VERSION:
            raise ExternalContractError("Unsupported external contract version")
        if self.protocol_kind is not ProtocolKind.ACP:
            raise ExternalContractError("Unsupported external protocol")
        if type(self.protocol_version) is not int or self.protocol_version != ACP_PROTOCOL_VERSION:
            raise ExternalContractError("Unsupported external protocol version")
        if self.launch_mode is not LaunchMode.LOCAL_CHILD:
            raise ExternalContractError("Unsupported external launch mode")
        for field in (
            "module_id",
            "provider_id",
            "runtime_id",
            "adapter_id",
            "runtime_profile_ref",
            "conformance_ref",
        ):
            validate_opaque_identifier(getattr(self, field), field)
        _safe_version(self.module_version, "module version")
        object.__setattr__(
            self,
            "capabilities",
            _normalized_identifiers(self.capabilities, allowed=_ALLOWED_CAPABILITIES),
        )
        object.__setattr__(
            self,
            "permissions",
            _normalized_identifiers(self.permissions, allowed=_ALLOWED_PERMISSIONS),
        )
        required = {"session_create", "input_dispatch", "result_capture", "cleanup", "health", "readiness"}
        if not required.issubset(self.capabilities):
            raise ExternalContractError("External capability declaration is incomplete")
        if type(self.egress) is not tuple or len(self.egress) != 2:
            raise ExternalContractError("Both external egress channels must be declared")
        channels = {item.channel for item in self.egress if isinstance(item, EgressDeclaration)}
        if channels != set(EgressChannel):
            raise ExternalContractError("Both external egress channels must be declared")
        if self.auth_ownership not in {
            AuthOwnership.NONE,
            AuthOwnership.RUNTIME_MANAGED,
            AuthOwnership.SECRET_REF,
        }:
            raise ExternalContractError("Unsupported external authentication ownership")
        _safe_digest(self.execution_envelope_ref, "execution envelope reference")

    @property
    def binding_version_token(self) -> str:
        """Existing snapshot field token; no schema or migration is introduced."""
        return f"{self.module_version}+env.{self.execution_envelope_ref}"


@dataclass(frozen=True, slots=True)
class ExternalSessionHandle:
    external_session_id: str
    project_scope_digest: str
    binding_fingerprint: str
    execution_envelope_fingerprint: str
    created_by_run_id: str
    attach_generation: int = 1

    def __post_init__(self) -> None:
        validate_opaque_identifier(self.external_session_id, "external_session_id")
        for name in (
            "project_scope_digest",
            "binding_fingerprint",
            "execution_envelope_fingerprint",
        ):
            _safe_digest(getattr(self, name), name)
        if type(self.created_by_run_id) is not str or not self.created_by_run_id:
            raise ExternalContractError("Invalid Core Run identity")
        if type(self.attach_generation) is not int or self.attach_generation < 1:
            raise ExternalContractError("Invalid attach generation")
        if _SENSITIVE.search(self.external_session_id):
            raise ExternalContractError("Unsafe external session identity")


class ExternalRuntimeAdapter(RuntimeAdapter, Protocol):
    descriptor: ExternalRuntimeDescriptor
    envelope: ControlledExecutionEnvelope

    def bind_core_run(self, snapshot: RuntimeBindingSnapshot) -> None: ...


@dataclass(frozen=True)
class ExternalRuntimeDefinition:
    """Static operator policy only; never contains a materialized workspace.

    The descriptor's envelope reference is a template sentinel, not a binding.
    ExecutionService materializes a fresh run before committing its snapshot.
    """

    descriptor: ExternalRuntimeDescriptor
    executable: ExecutableIdentity
    staging_parent: Path
    effective_config_digest: str

    def __post_init__(self) -> None:
        if self.descriptor.execution_envelope_ref != "0" * 64:
            raise ExternalContractError("Static definition must not contain a Run envelope")
        _safe_digest(self.effective_config_digest, "expected effective config digest")

    def prepare(self, run_id: str, task: Task, context: ContextPackage) -> PreparedExternalRun:
        if task.project_id != context.project_id or task.context_package_id != context.id:
            raise ExternalContractError("External Run scope mismatch")
        root = create_projected_staging(self.staging_parent, context)
        (root / ".polynexus-run").write_text(run_id, encoding="utf-8")
        envelope = build_controlled_execution_envelope(
            staging_root=root,
            executable_path=Path(self.executable.resolved_path),
            observed_runtime_version=self.executable.observed_runtime_version,
            effective_config_digest=self.effective_config_digest,
        )
        if envelope.executable_identity != self.executable:
            raise ExternalContractError("Executable identity drift")
        return PreparedExternalRun(
            run_id, task.id, context.project_id, context.id, root, envelope,
            replace(self.descriptor, execution_envelope_ref=envelope.execution_envelope_ref),
        )


@dataclass(frozen=True)
class PreparedExternalRun:
    """Transient Core preparation, held by ExecutionService, not static registry."""

    run_id: str
    task_id: str
    project_id: str
    context_id: str
    staging_root: Path
    envelope: ControlledExecutionEnvelope
    descriptor: ExternalRuntimeDescriptor

    def validate(self, snapshot: RuntimeBindingSnapshot) -> None:
        if snapshot.run_id != self.run_id or snapshot.adapter_version != self.descriptor.binding_version_token:
            raise ExternalContractError("External Run binding mismatch")
        if (self.staging_root / ".polynexus-run").read_text(encoding="utf-8") != self.run_id:
            raise ExternalContractError("External Run staging mismatch")
        value = json.loads((self.staging_root / "context.json").read_text(encoding="utf-8"))
        if (value.get("project_id"), value.get("context_id")) != (self.project_id, self.context_id):
            raise ExternalContractError("External context scope mismatch")
        validate_current_envelope(self.envelope, self.staging_root)


def is_link_or_junction(path: Path) -> bool:
    """Reject both ordinary links and Windows junction/reparse escapes."""
    try:
        return path.is_symlink() or (
            hasattr(path, "is_junction") and path.is_junction()
        )
    except OSError:
        return True


def create_projected_staging(
    base_dir: Path,
    context: ContextPackage,
    approved_files: Iterable[Path] = (),
) -> Path:
    """Create a Core-owned staging root containing only approved projections."""
    base = Path(base_dir).resolve(strict=True)
    if not base.is_dir() or base.is_symlink():
        raise ExternalContractError("Invalid staging parent")
    root = Path(tempfile.mkdtemp(prefix="polynexus-mcf02-", dir=base)).resolve(strict=True)
    try:
        marker = {"contract": EXTERNAL_CONTRACT_VERSION, "scope": WorkspaceScopeMode.PROJECTED_STAGING.value}
        (root / ".polynexus-staging").write_text(
            json.dumps(marker, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )
        projected = {
            "project_id": context.project_id,
            "context_id": context.id,
            "version": context.version,
            "instructions": list(context.instructions),
            "constraints": list(context.constraints),
            "project_facts": dict(context.project_facts),
            "artifact_refs": list(context.artifact_refs),
            "prior_decision_refs": list(context.prior_decision_refs),
            "memory_refs": list(context.memory_refs),
            "source_refs": list(context.source_refs),
        }
        (root / "context.json").write_text(
            json.dumps(projected, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
            encoding="utf-8",
        )
        inputs = root / "inputs"
        inputs.mkdir()
        for index, source_value in enumerate(tuple(approved_files)):
            source = Path(source_value)
            if is_link_or_junction(source) or not source.is_file():
                raise ExternalContractError("Approved input file is invalid")
            before = source.stat()
            if before.st_size > MAX_STAGING_FILE_BYTES:
                raise ExternalContractError("Approved input file exceeds size limit")
            destination = inputs / f"{index:04d}-{source.name}"
            shutil.copyfile(source, destination, follow_symlinks=False)
            after = source.stat()
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                raise ExternalContractError("Approved input changed during projection")
        inspect_projected_staging(root)
        return root
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise


def _contained(root: Path, candidate: Path) -> Path:
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        return resolved
    except Exception:
        raise ExternalContractError("Workspace path escapes projected staging") from None


def inspect_projected_staging(root_value: Path) -> tuple[str, str]:
    """Return (workspace identity, content fingerprint), rejecting config injection."""
    root_path = Path(root_value)
    if is_link_or_junction(root_path):
        raise ExternalContractError("Projected staging root must not be a link")
    root = root_path.resolve(strict=True)
    if not root.is_dir():
        raise ExternalContractError("Projected staging root is invalid")
    marker = root / ".polynexus-staging"
    if not marker.is_file() or is_link_or_junction(marker):
        raise ExternalContractError("Projected staging marker is missing")
    try:
        marker_value = json.loads(marker.read_text(encoding="utf-8"))
    except Exception:
        raise ExternalContractError("Projected staging marker is invalid") from None
    if marker_value != {"contract": 1, "scope": "PROJECTED_STAGING"}:
        raise ExternalContractError("Projected staging marker is invalid")

    inventory: list[tuple[str, int, str]] = []
    paths = sorted(root.rglob("*"), key=lambda item: item.as_posix())
    if len(paths) > MAX_STAGING_FILES:
        raise ExternalContractError("Projected staging file count exceeds limit")
    for candidate in paths:
        if is_link_or_junction(candidate):
            raise ExternalContractError("Projected staging links are not allowed")
        resolved = _contained(root, candidate)
        relative = resolved.relative_to(root).as_posix()
        parts = {part.lower() for part in resolved.relative_to(root).parts}
        if ".opencode" in parts or resolved.name.lower() in _FORBIDDEN_CONFIG_NAMES:
            raise ExternalContractError("External runtime configuration is not approved")
        if resolved.is_dir():
            continue
        if not resolved.is_file():
            raise ExternalContractError("Projected staging entry is invalid")
        size = resolved.stat().st_size
        if size > MAX_STAGING_FILE_BYTES:
            raise ExternalContractError("Projected staging file exceeds size limit")
        data = resolved.read_bytes()
        if resolved.name.lower() == "package.json" and b"opencode" in data.lower():
            raise ExternalContractError("External runtime package plugin is not approved")
        inventory.append((relative, len(data), hashlib.sha256(data).hexdigest()))
    stat = root.stat()
    workspace_identity = _canonical_digest(
        {"path": str(root), "device": stat.st_dev, "inode": stat.st_ino, "marker": marker_value}
    )
    return workspace_identity, _canonical_digest(inventory)


def build_executable_identity(path_value: Path, observed_version: str) -> ExecutableIdentity:
    path = Path(path_value)
    if is_link_or_junction(path):
        raise ExternalContractError("Executable link is not allowed")
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ExternalContractError("Configured executable is unavailable")
    data = resolved.read_bytes()
    return ExecutableIdentity(
        resolved_path=str(resolved),
        content_sha256=hashlib.sha256(data).hexdigest(),
        observed_runtime_version=_safe_version(observed_version, "observed runtime version"),
    )


def build_controlled_execution_envelope(
    *,
    staging_root: Path,
    executable_path: Path,
    observed_runtime_version: str,
    effective_config_digest: str = "0" * 64,
) -> ControlledExecutionEnvelope:
    workspace_identity, content_fingerprint = inspect_projected_staging(staging_root)
    executable = build_executable_identity(executable_path, observed_runtime_version)
    permission_policy = {
        "external_side_effect": "APPROVAL_REQUIRED",
        "agent_extension_egress": "DENY",
        "auto_approve": False,
        "plugin_set": "NONE",
        "mcp_set": "NONE",
        "remote_skill_catalog": "NONE",
        "workspace_scope": "PROJECTED_STAGING",
    }
    effective_config = {
        "workspace_identity": workspace_identity,
        "workspace_content": content_fingerprint,
        "permission_policy": permission_policy,
        "config_precedence": ["CORE_CONTROLLED_ONLY"],
    }
    # This is a pinned expected resolved-config digest. Readiness must obtain
    # and compare actual resolver output; a template alone is never evidence.
    effective_fingerprint = _safe_digest(effective_config_digest, "effective config digest")
    permission_fingerprint = _canonical_digest(permission_policy)
    reference = _canonical_digest(
        {
            "workspace_scope_mode": WorkspaceScopeMode.PROJECTED_STAGING.value,
            "workspace_identity": workspace_identity,
            "workspace_content_fingerprint": content_fingerprint,
            "effective_runtime_configuration_fingerprint": effective_fingerprint,
            "permission_policy_fingerprint": permission_fingerprint,
            "enabled_plugin_set": [],
            "enabled_mcp_set": [],
            "remote_skill_catalog_state": [],
            "executable": {
                "path": executable.resolved_path,
                "sha256": executable.content_sha256,
                "version": executable.observed_runtime_version,
            },
        }
    )
    return ControlledExecutionEnvelope(
        workspace_scope_mode=WorkspaceScopeMode.PROJECTED_STAGING,
        workspace_identity=workspace_identity,
        workspace_content_fingerprint=content_fingerprint,
        effective_runtime_configuration_fingerprint=effective_fingerprint,
        permission_policy_fingerprint=permission_fingerprint,
        enabled_plugin_set=(),
        enabled_mcp_set=(),
        remote_skill_catalog_state=(),
        executable_identity=executable,
        execution_envelope_ref=reference,
    )


def validate_current_envelope(envelope: ControlledExecutionEnvelope, staging_root: Path) -> None:
    rebuilt = build_controlled_execution_envelope(
        staging_root=staging_root,
        executable_path=Path(envelope.executable_identity.resolved_path),
        observed_runtime_version=envelope.executable_identity.observed_runtime_version,
        effective_config_digest=envelope.effective_runtime_configuration_fingerprint,
    )
    if rebuilt != envelope:
        raise ExternalContractError("External execution envelope drift detected")


def binding_fingerprint(snapshot: RuntimeBindingSnapshot) -> str:
    if not isinstance(snapshot, RuntimeBindingSnapshot):
        raise ExternalContractError("Invalid immutable runtime binding")
    return _canonical_digest(
        {
            "run_id": snapshot.run_id,
            "provider_id": snapshot.provider_id,
            "transport_kind": snapshot.transport_kind.value,
            "runtime_id": snapshot.runtime_id,
            "adapter_id": snapshot.adapter_id,
            "execution_target": snapshot.execution_target.value,
            "runtime_profile_ref": snapshot.runtime_profile_ref,
            "profile_revision": snapshot.profile_revision,
            "adapter_version": snapshot.adapter_version,
            "auth_ownership": snapshot.auth_ownership.value,
        }
    )


def project_scope_digest(context: ContextPackage) -> str:
    return _canonical_digest({"project_id": context.project_id, "context_id": context.id})


def external_descriptor_from_mapping(value: Mapping[str, object]) -> ExternalRuntimeDescriptor:
    """Strict parser: unknown keys and malformed enum/capability values fail closed."""
    expected = {
        "contract_version",
        "module_id",
        "module_version",
        "provider_id",
        "runtime_id",
        "adapter_id",
        "runtime_profile_ref",
        "protocol_kind",
        "protocol_version",
        "launch_mode",
        "capabilities",
        "permissions",
        "egress",
        "auth_ownership",
        "conformance_ref",
        "execution_envelope_ref",
    }
    if type(value) is not dict or set(value) != expected:
        raise ExternalContractError("Invalid external descriptor fields")
    try:
        egress_value = value["egress"]
        if type(egress_value) is not list:
            raise TypeError
        egress = tuple(
            EgressDeclaration(
                channel=EgressChannel(item["channel"]),
                disposition=EgressDisposition(item["disposition"]),
                destination_ref=item.get("destination_ref"),
            )
            for item in egress_value
            if type(item) is dict and set(item).issubset({"channel", "disposition", "destination_ref"})
        )
        if len(egress) != len(egress_value):
            raise TypeError
        return ExternalRuntimeDescriptor(
            contract_version=value["contract_version"],  # type: ignore[arg-type]
            module_id=value["module_id"],  # type: ignore[arg-type]
            module_version=value["module_version"],  # type: ignore[arg-type]
            provider_id=value["provider_id"],  # type: ignore[arg-type]
            runtime_id=value["runtime_id"],  # type: ignore[arg-type]
            adapter_id=value["adapter_id"],  # type: ignore[arg-type]
            runtime_profile_ref=value["runtime_profile_ref"],  # type: ignore[arg-type]
            protocol_kind=ProtocolKind(value["protocol_kind"]),  # type: ignore[arg-type]
            protocol_version=value["protocol_version"],  # type: ignore[arg-type]
            launch_mode=LaunchMode(value["launch_mode"]),  # type: ignore[arg-type]
            capabilities=tuple(value["capabilities"]),  # type: ignore[arg-type]
            permissions=tuple(value["permissions"]),  # type: ignore[arg-type]
            egress=egress,
            auth_ownership=AuthOwnership(value["auth_ownership"]),  # type: ignore[arg-type]
            conformance_ref=value["conformance_ref"],  # type: ignore[arg-type]
            execution_envelope_ref=value["execution_envelope_ref"],  # type: ignore[arg-type]
        )
    except ExternalContractError:
        raise
    except Exception:
        raise ExternalContractError("Invalid external descriptor") from None
