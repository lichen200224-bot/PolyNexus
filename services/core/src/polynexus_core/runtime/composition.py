"""Static runtime/module composition root.

Provider-specific identity is declared here beside its adapter factory. The
RuntimeRegistry remains the sole profile resolver and this module exposes no
dynamic install, download, or alternate resolution path.
"""
from __future__ import annotations

from polynexus_core.domain.enums import (
    AuthOwnership,
    ExecutionTarget,
    TransportKind,
    UsageVisibility,
)
from polynexus_core.domain.runtime_binding import RuntimeProfile
from polynexus_core.extensions.manifest import (
    ConformanceScope,
    HealthBoundary,
    ModuleManifest,
    ModuleType,
)
from polynexus_core.extensions.registry import ModuleRegistry
from polynexus_core.extensions.runtime_bridge import RuntimeModuleBridge
from polynexus_core.runtime.codex_exec import (
    CODEX_ADAPTER_ID,
    CODEX_PROFILE_REF,
    CodexExecRuntimeAdapter,
)
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.registry import (
    RuntimeRegistry,
    build_reference_profile,
)


def build_codex_profile() -> RuntimeProfile:
    """Declare the installed Codex target with runtime-managed auth."""

    return RuntimeProfile(
        provider_id="openai",
        transport_kind=TransportKind.LOCAL,
        runtime_id="codex",
        adapter_id=CODEX_ADAPTER_ID,
        execution_target=ExecutionTarget.LOCAL,
        runtime_profile_ref=CODEX_PROFILE_REF,
        profile_revision=1,
        auth_ownership=AuthOwnership.RUNTIME_MANAGED,
        secret_ref_id=None,
        usage_visibility=UsageVisibility.UNAVAILABLE,
    )


def build_default_registry() -> RuntimeRegistry:
    """Compose static modules into one existing RuntimeRegistry."""

    registry = RuntimeRegistry()
    modules = ModuleRegistry()
    bridge = RuntimeModuleBridge(modules, registry)
    bridge.register(
        ModuleManifest(
            module_id="module.reference",
            module_type=ModuleType.RUNTIME,
            module_version="1.0.0",
            provider_id="polynexus",
            capabilities=(
                "cancel",
                "artifacts",
                "timeout_cleanup_verified",
                "auth_ownership",
            ),
            health=HealthBoundary.RUNTIME_PROBE,
            conformance_scope=ConformanceScope.DETERMINISTIC_LOCAL_CONFORMANCE,
        ),
        ((build_reference_profile(), ReferenceRuntimeAdapter),),
    )
    # Static registration is lazy: no executable probe, launch, download, or
    # credential-store read occurs during composition.
    bridge.register(
        ModuleManifest(
            module_id="module.codex",
            module_type=ModuleType.RUNTIME,
            module_version="1.0.0",
            provider_id="openai",
            capabilities=("cancel", "artifacts", "auth_ownership"),
            health=HealthBoundary.RUNTIME_PROBE,
            conformance_scope=ConformanceScope.UNVERIFIED,
        ),
        ((build_codex_profile(), CodexExecRuntimeAdapter),),
    )
    registry.static_module_registry = modules  # type: ignore[attr-defined]
    registry.static_module_bridge = bridge  # type: ignore[attr-defined]
    return registry
