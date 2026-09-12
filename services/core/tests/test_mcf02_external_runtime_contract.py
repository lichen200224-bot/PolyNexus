"""MCF-02 vendor-neutral contract and controlled-envelope tests."""
from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from polynexus_core.domain.enums import AuthOwnership
from polynexus_core.domain.models import ContextPackage, Project
from polynexus_core.domain.runtime_binding import RuntimeBindingError
from polynexus_core.extensions import (
    ConformanceScope,
    HealthBoundary,
    ModuleManifest,
    ModuleRegistry,
    ModuleType,
    RuntimeModuleBridge,
)
from polynexus_core.runtime.external_contracts import (
    ControlledExecutionEnvelope,
    ExternalRuntimeDefinition,
    EgressChannel,
    EgressDeclaration,
    EgressDisposition,
    ExternalContractError,
    ExternalRuntimeDescriptor,
    LaunchMode,
    ProtocolKind,
    WorkspaceScopeMode,
    build_controlled_execution_envelope,
    create_projected_staging,
    external_descriptor_from_mapping,
    inspect_projected_staging,
    validate_current_envelope,
)
from polynexus_core.runtime.opencode_acp import (
    OpenCodeAcpRuntimeAdapter,
    build_opencode_acp_descriptor,
    build_opencode_acp_profile,
)
from polynexus_core.runtime.contracts import RuntimeCapabilities
from polynexus_core.runtime.doctor import _sanitize_capabilities
from polynexus_core.runtime.registry import RuntimeRegistry
from polynexus_core.runtime.routing_policy import PolicyDecision, evaluate_external_egress


def context() -> ContextPackage:
    project = Project(name="MCF02")
    return ContextPackage(
        project_id=project.id,
        version=1,
        instructions=("Review only the projected input",),
        constraints=("No external side effects",),
        source_refs=("fixture:mcf02",),
    )


def controlled(tmp_path: Path):
    root = create_projected_staging(tmp_path, context())
    executable = tmp_path / "opencode-test-bin"
    executable.write_bytes(b"deterministic opencode executable v1")
    envelope = build_controlled_execution_envelope(
        staging_root=root,
        executable_path=executable,
        observed_runtime_version="1.0.0",
    )
    return root, executable, envelope


def descriptor_mapping(descriptor: ExternalRuntimeDescriptor) -> dict[str, object]:
    return {
        "contract_version": descriptor.contract_version,
        "module_id": descriptor.module_id,
        "module_version": descriptor.module_version,
        "provider_id": descriptor.provider_id,
        "runtime_id": descriptor.runtime_id,
        "adapter_id": descriptor.adapter_id,
        "runtime_profile_ref": descriptor.runtime_profile_ref,
        "protocol_kind": descriptor.protocol_kind.value,
        "protocol_version": descriptor.protocol_version,
        "launch_mode": descriptor.launch_mode.value,
        "capabilities": list(descriptor.capabilities),
        "permissions": list(descriptor.permissions),
        "egress": [
            {
                "channel": item.channel.value,
                "disposition": item.disposition.value,
                **({"destination_ref": item.destination_ref} if item.destination_ref else {}),
            }
            for item in descriptor.egress
        ],
        "auth_ownership": descriptor.auth_ownership.value,
        "conformance_ref": descriptor.conformance_ref,
        "execution_envelope_ref": descriptor.execution_envelope_ref,
    }


def test_valid_descriptor_is_immutable_bounded_and_secret_free(tmp_path: Path) -> None:
    _, _, envelope = controlled(tmp_path)
    descriptor = build_opencode_acp_descriptor(envelope)
    parsed = external_descriptor_from_mapping(descriptor_mapping(descriptor))
    assert parsed == descriptor
    assert parsed.protocol_kind is ProtocolKind.ACP
    assert parsed.launch_mode is LaunchMode.LOCAL_CHILD
    assert parsed.execution_envelope_ref == envelope.execution_envelope_ref
    assert "secret" not in repr(asdict(parsed)).lower()
    with pytest.raises(FrozenInstanceError):
        parsed.runtime_id = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "field,value",
    [
        ("contract_version", 2),
        ("contract_version", True),
        ("protocol_version", 2),
        ("protocol_kind", "UNKNOWN"),
        ("launch_mode", "DIRECT_PROJECT_WORKSPACE"),
        ("provider_id", "bad/id"),
        ("unknown", "value"),
    ],
)
def test_unknown_contract_protocol_identity_or_field_fails_closed(
    tmp_path: Path, field: str, value: object
) -> None:
    _, _, envelope = controlled(tmp_path)
    mapping = descriptor_mapping(build_opencode_acp_descriptor(envelope))
    mapping[field] = value
    with pytest.raises(ExternalContractError):
        external_descriptor_from_mapping(mapping)


@pytest.mark.parametrize(
    "capabilities",
    [
        ["session_create", "unknown"],
        ["session_create", "session_create"],
        ["session_create"],
    ],
)
def test_unknown_duplicate_or_incomplete_capabilities_fail_closed(
    tmp_path: Path, capabilities: list[str]
) -> None:
    _, _, envelope = controlled(tmp_path)
    mapping = descriptor_mapping(build_opencode_acp_descriptor(envelope))
    mapping["capabilities"] = capabilities
    with pytest.raises(ExternalContractError):
        external_descriptor_from_mapping(mapping)


def test_clean_projected_staging_has_explicit_none_extension_sets(tmp_path: Path) -> None:
    root, _, envelope = controlled(tmp_path)
    assert envelope.workspace_scope_mode is WorkspaceScopeMode.PROJECTED_STAGING
    assert envelope.enabled_plugin_set == ()
    assert envelope.enabled_mcp_set == ()
    assert envelope.remote_skill_catalog_state == ()
    validate_current_envelope(envelope, root)


@pytest.mark.parametrize(
    "relative,payload",
    [
        ("opencode.json", '{"permission":"allow"}'),
        ("opencode.jsonc", "// permissive default allow"),
        (".opencode/plugins/evil.py", "side load"),
        ("package.json", '{"dependencies":{"@opencode-ai/plugin":"latest"}}'),
        ("mcp.json", '{"server":"local"}'),
        (".mcp.json", '{"url":"https://remote.invalid"}'),
    ],
)
def test_config_plugin_package_and_mcp_injection_fail_closed(
    tmp_path: Path, relative: str, payload: str
) -> None:
    root, executable, _ = controlled(tmp_path)
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")
    with pytest.raises(ExternalContractError):
        build_controlled_execution_envelope(
            staging_root=root,
            executable_path=executable,
            observed_runtime_version="1.0.0",
        )


def test_remote_skill_catalog_and_nonempty_plugin_mcp_sets_rejected(tmp_path: Path) -> None:
    _, _, envelope = controlled(tmp_path)
    for field, value in (
        ("enabled_plugin_set", ("plugin.remote",)),
        ("enabled_mcp_set", ("mcp.remote",)),
        ("remote_skill_catalog_state", ("catalog.remote",)),
    ):
        with pytest.raises(ExternalContractError):
            replace(envelope, **{field: value})


def test_effective_config_drift_after_binding_fails_closed(tmp_path: Path) -> None:
    root, _, envelope = controlled(tmp_path)
    (root / "context.json").write_text('{"changed":true}', encoding="utf-8")
    with pytest.raises(ExternalContractError, match="drift"):
        validate_current_envelope(envelope, root)


def test_same_executable_path_changed_hash_fails_closed(tmp_path: Path) -> None:
    root, executable, envelope = controlled(tmp_path)
    executable.write_bytes(b"replacement binary at same path")
    with pytest.raises(ExternalContractError, match="drift"):
        validate_current_envelope(envelope, root)


def test_workspace_path_substitution_fails_closed(tmp_path: Path) -> None:
    root, _, envelope = controlled(tmp_path)
    moved = tmp_path / "original-staging"
    root.rename(moved)
    root.mkdir()
    (root / ".polynexus-staging").write_text(
        '{"contract":1,"scope":"PROJECTED_STAGING"}', encoding="utf-8"
    )
    (root / "context.json").write_text("{}", encoding="utf-8")
    (root / "inputs").mkdir()
    with pytest.raises(ExternalContractError, match="drift"):
        validate_current_envelope(envelope, root)


def test_link_and_direct_project_workspace_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _, _ = controlled(tmp_path)
    linked = root / "linked"
    linked.write_text("outside", encoding="utf-8")
    original = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda self: self == linked or original(self),
    )
    with pytest.raises(ExternalContractError, match="links"):
        inspect_projected_staging(root)

    direct = tmp_path / "real-project"
    direct.mkdir()
    with pytest.raises(ExternalContractError, match="marker"):
        inspect_projected_staging(direct)


def test_provider_and_agent_egress_are_separate_and_human_gated(tmp_path: Path) -> None:
    _, _, envelope = controlled(tmp_path)
    descriptor = build_opencode_acp_descriptor(envelope)
    pending = evaluate_external_egress(descriptor)
    assert pending.provider_model_egress is PolicyDecision.APPROVAL_REQUIRED
    assert pending.agent_extension_egress is PolicyDecision.DENY
    assert pending.dispatch_allowed is False
    boolean = evaluate_external_egress(descriptor, authorization=True)
    assert boolean.dispatch_allowed is False
    declared = replace(descriptor, egress=(
        EgressDeclaration(EgressChannel.PROVIDER_MODEL_EGRESS, EgressDisposition.APPROVED),
        EgressDeclaration(EgressChannel.AGENT_EXTENSION_EGRESS, EgressDisposition.DENY),
    ))
    assert evaluate_external_egress(declared).dispatch_allowed is False


def test_agent_extension_egress_cannot_be_enabled(tmp_path: Path) -> None:
    _, _, envelope = controlled(tmp_path)
    with pytest.raises(ExternalContractError):
        EgressDeclaration(
            EgressChannel.AGENT_EXTENSION_EGRESS,
            EgressDisposition.APPROVED,
            "untrusted.remote",
        )


def test_static_registration_rejects_materialized_envelope(tmp_path):
    root, executable, envelope = controlled(tmp_path)
    descriptor = build_opencode_acp_descriptor(envelope)
    with pytest.raises(ExternalContractError):
        ExternalRuntimeDefinition(descriptor, envelope.executable_identity, tmp_path, "0" * 64)


def test_external_definition_registry_conflict_and_no_unscoped_execution(tmp_path):
    root, executable, envelope = controlled(tmp_path)
    descriptor = replace(build_opencode_acp_descriptor(envelope), execution_envelope_ref="0" * 64)
    definition = ExternalRuntimeDefinition(descriptor, envelope.executable_identity, tmp_path, "0" * 64)
    registry = RuntimeRegistry()
    profile = build_opencode_acp_profile()
    factory = lambda prepared: None
    with pytest.raises(RuntimeBindingError):
        registry.register_external(replace(profile, provider_id="wrong"), factory, definition)
    registry.register_external(profile, factory, definition)
    with pytest.raises(RuntimeBindingError):
        registry.register_external(profile, factory, definition)
    with pytest.raises(RuntimeBindingError):
        registry.create_adapter(profile)
    with pytest.raises(RuntimeBindingError):
        registry.bind(profile.runtime_profile_ref, "run-a", datetime.now(timezone.utc))
    with pytest.raises(RuntimeBindingError):
        registry.resolve("missing.external")


def test_bridge_static_external_definition_stays_disabled_at_factory(tmp_path):
    root, executable, envelope = controlled(tmp_path)
    descriptor = replace(build_opencode_acp_descriptor(envelope), execution_envelope_ref="0" * 64)
    definition = ExternalRuntimeDefinition(descriptor, envelope.executable_identity, tmp_path, "0" * 64)
    profile = build_opencode_acp_profile()
    bridge = RuntimeModuleBridge(ModuleRegistry(), RuntimeRegistry())
    manifest = ModuleManifest(module_id=descriptor.module_id, module_type=ModuleType.RUNTIME,
                              module_version=descriptor.module_version,
                              provider_id=descriptor.provider_id)
    bridge.register_external(manifest, profile, lambda prepared: None, definition)
    bridge.modules.set_enabled(manifest.module_id, False)
    with pytest.raises(RuntimeBindingError):
        bridge.runtimes.create_adapter(profile)


def test_binding_token_does_not_contain_raw_config_or_credential(tmp_path: Path) -> None:
    _, executable, envelope = controlled(tmp_path)
    token = build_opencode_acp_descriptor(envelope).binding_version_token
    assert envelope.execution_envelope_ref in token
    assert str(executable) not in token
    assert "credential" not in token.lower()
    assert hashlib.sha256(executable.read_bytes()).hexdigest() not in token


def test_doctor_preserves_external_declarations_without_promoting_maturity() -> None:
    declared = RuntimeCapabilities(
        external_sessions=True,
        event_stream=True,
        permission_requests=True,
        egress_declaration=True,
    )
    sanitized = _sanitize_capabilities(declared)
    assert sanitized == declared
