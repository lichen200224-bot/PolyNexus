"""Static composition bridge. RuntimeRegistry remains the execution authority."""
from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass, replace

from polynexus_core.domain.enums import AuthOwnership, ExecutionTarget, ResumeMode, TransportKind, UsageVisibility
from polynexus_core.domain.runtime_binding import RuntimeProfile
from polynexus_core.extensions.manifest import HealthBoundary, ModuleError, ModuleManifest, ModuleType
from polynexus_core.extensions.registry import ModuleRegistry
from polynexus_core.runtime.contracts import RuntimeAdapter, RuntimeCapabilities
from polynexus_core.runtime.external_contracts import (
    ExternalRuntimeDefinition,
    ExternalRuntimeDescriptor,
)
from polynexus_core.runtime.registry import AdapterFactory, RuntimeRegistry

_RUNTIME_CAPABILITIES = frozenset({
    "cancel", "resume", "artifacts", "timeout_cleanup_verified", "usage_visibility", "auth_ownership",
    "external_sessions", "event_stream", "permission_requests", "egress_declaration",
})


def _check_capabilities(adapter: RuntimeAdapter, declared: tuple[str, ...]) -> None:
    caps = adapter.capabilities()
    if (
        type(caps) is not RuntimeCapabilities
        or any(type(getattr(caps, key)) is not bool for key in (
            "cancel", "artifacts", "timeout_cleanup_verified", "external_sessions",
            "event_stream", "permission_requests", "egress_declaration",
        ))
        or not isinstance(caps.resume, ResumeMode)
        or not isinstance(caps.usage_visibility, UsageVisibility)
        or not isinstance(caps.auth_ownership, AuthOwnership)
    ):
        raise ModuleError("Invalid runtime capability declaration")
    available = {
        "cancel": caps.cancel,
        "artifacts": caps.artifacts,
        "timeout_cleanup_verified": caps.timeout_cleanup_verified,
        "resume": caps.resume is not ResumeMode.NONE,
        "usage_visibility": caps.usage_visibility is not UsageVisibility.UNAVAILABLE,
        "auth_ownership": True,
        "external_sessions": caps.external_sessions,
        "event_stream": caps.event_stream,
        "permission_requests": caps.permission_requests,
        "egress_declaration": caps.egress_declaration,
    }
    if not all(available[name] for name in declared):
        raise ModuleError("Runtime does not satisfy module capabilities")


@dataclass(frozen=True)
class ModuleHealth:
    """Current probe only; never a conformance verdict or vendor detection."""
    healthy: bool | None
    ready: bool | None
    error_category: str | None = None


class RuntimeModuleBridge:
    """Registers lazy guarded factories in the supplied existing registry.

    No factory is called during registration. ExecutionService retains the
    binding-first transaction and RunSupervisor retains lifecycle ownership.
    Duplicate bridge registration is rejected, including identical retries;
    metadata-only ModuleRegistry registration is idempotent.
    """

    def __init__(self, modules: ModuleRegistry, runtimes: RuntimeRegistry) -> None:
        self.modules = modules
        self.runtimes = runtimes
        self._profile_refs: dict[str, tuple[str, ...]] = {}

    def register(
        self,
        manifest: ModuleManifest,
        registrations: tuple[tuple[RuntimeProfile, AdapterFactory], ...],
    ) -> None:
        if type(manifest) is not ModuleManifest:
            raise ModuleError("Invalid module manifest")
        manifest.__post_init__()
        if manifest.module_type is not ModuleType.RUNTIME:
            raise ModuleError("Runtime bridge requires a runtime module")
        if not set(manifest.capabilities).issubset(_RUNTIME_CAPABILITIES):
            raise ModuleError("Invalid runtime module capability declaration")
        if self.modules.contains(manifest.module_id):
            raise ModuleError("Runtime module is already registered")
        if not isinstance(registrations, tuple) or not registrations:
            raise ModuleError("Runtime module requires profile registrations")

        # Retain composition expectations, not a second resolver. All profile
        # lookup, factory ownership, binding and creation use RuntimeRegistry.
        prepared: list[tuple[RuntimeProfile, AdapterFactory]] = []
        try:
            for profile, factory in registrations:
                if type(profile) is not RuntimeProfile or not callable(factory):
                    raise ValueError
                profile = replace(profile)
                if (
                    not isinstance(profile.transport_kind, TransportKind)
                    or not isinstance(profile.execution_target, ExecutionTarget)
                    or not isinstance(profile.auth_ownership, AuthOwnership)
                    or not isinstance(profile.usage_visibility, UsageVisibility)
                    or type(profile.profile_revision) is not int
                    or (manifest.provider_id is not None and manifest.provider_id != profile.provider_id)
                ):
                    raise ValueError
                prepared.append((profile, factory))
        except Exception:
            raise ModuleError("Invalid runtime module registration") from None

        wrappers: dict[str, tuple[AdapterFactory, AdapterFactory]] = {}
        entries: list[tuple[RuntimeProfile, AdapterFactory]] = []
        for profile, factory in prepared:
            previous = wrappers.get(profile.adapter_id)
            if previous is not None:
                if previous[0] is not factory:
                    raise ModuleError("Conflicting module adapter factories")
                wrapper = previous[1]
            else:
                wrapper = self._guarded_factory(manifest, factory, tuple(prepared))
                wrappers[profile.adapter_id] = (factory, wrapper)
            entries.append((replace(profile), wrapper))

        # register_many validates the entire batch before publishing it. The
        # metadata commit below cannot fail after validation in static composition.
        self.runtimes.register_many(tuple(entries))
        self.modules.register(manifest)
        self._profile_refs[manifest.module_id] = tuple(profile.runtime_profile_ref for profile, _ in prepared)

    def _guarded_factory(
        self,
        manifest: ModuleManifest,
        factory: AdapterFactory,
        expectations: tuple[tuple[RuntimeProfile, AdapterFactory], ...],
    ) -> AdapterFactory:
        def create() -> RuntimeAdapter:
            self.modules.resolve(manifest.module_id)
            try:
                for expected, _ in expectations:
                    if self.runtimes.resolve(expected.runtime_profile_ref) != expected:
                        raise ValueError
                adapter = factory()
                _check_capabilities(adapter, manifest.capabilities)
                return adapter
            except Exception:
                raise ModuleError("Runtime module factory or capability check failed") from None
        return create

    def register_external(
        self,
        manifest: ModuleManifest,
        profile: RuntimeProfile,
        factory: AdapterFactory,
        definition: ExternalRuntimeDefinition,
    ) -> None:
        """Register one statically composed external runtime module.

        MCF-02 intentionally permits one profile per external module and keeps
        executable discovery/install outside this bridge.
        """
        if type(definition) is not ExternalRuntimeDefinition:
            raise ModuleError("Invalid external runtime definition")
        descriptor = definition.descriptor
        if (
            type(manifest) is not ModuleManifest
            or manifest.module_type is not ModuleType.RUNTIME
            or type(profile) is not RuntimeProfile
            or not callable(factory)
            or self.modules.contains(manifest.module_id)
            or descriptor.module_id != manifest.module_id
            or descriptor.module_version != manifest.module_version
            or descriptor.provider_id != profile.provider_id
            or not set(manifest.capabilities).issubset(_RUNTIME_CAPABILITIES)
        ):
            raise ModuleError("Invalid external runtime module registration")
        manifest.__post_init__()
        copied = replace(profile)
        def wrapper(prepared):
            self.modules.resolve(manifest.module_id)
            adapter = factory(prepared)
            _check_capabilities(adapter, manifest.capabilities)
            return adapter
        try:
            self.runtimes.register_external(copied, wrapper, definition)
            self.modules.register(manifest)
        except Exception:
            raise ModuleError("Invalid external runtime module registration") from None
        self._profile_refs[manifest.module_id] = (copied.runtime_profile_ref,)

    async def probe(self, module_id: str, profile_ref: str, *, timeout: float = 1.0) -> ModuleHealth:
        """Observe readiness without allocating a Run; never an execution route."""
        manifest = self.modules.resolve(module_id)
        if manifest.health is not HealthBoundary.RUNTIME_PROBE:
            raise ModuleError("Module health probe is not implemented")
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise ModuleError("Invalid module probe timeout")
        if profile_ref not in self._profile_refs.get(module_id, ()):
            raise ModuleError("Runtime profile does not belong to module")
        # Ownership references are metadata; resolution remains in RuntimeRegistry.
        # A profile must belong to this module, not merely exist in the registry.
        try:
            profile = self.runtimes.resolve(profile_ref)
            adapter = self.runtimes.create_adapter(profile)
        except Exception:
            return ModuleHealth(None, None, "FACTORY_FAILURE")
        try:
            healthy = await asyncio.wait_for(adapter.health(), timeout)
            if type(healthy) is not bool:
                return ModuleHealth(None, None, "INVALID_PROBE")
            ready = await asyncio.wait_for(adapter.readiness(), timeout)
            if type(ready) is not bool:
                return ModuleHealth(healthy, None, "INVALID_PROBE")
            return ModuleHealth(healthy, ready)
        except asyncio.TimeoutError:
            return ModuleHealth(None, None, "PROBE_TIMEOUT")
        except Exception:
            return ModuleHealth(None, None, "PROBE_FAILURE")
