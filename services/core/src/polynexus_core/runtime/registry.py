"""Runtime Registry / Adapter Factory (ADR-011 §5, PRE-WP14-B).

Resolution path:
    RuntimeProfile -> RuntimeRegistry / AdapterFactory
        -> RuntimeBindingSnapshot -> RuntimeAdapter -> RunSupervisor

Rules:
  - Profiles resolve by validated opaque reference; unknown/unavailable
    profiles fail closed. There is NO implicit fallback to the reference
    profile.
  - Adapter factories are registered per ``adapter_id``; an unregistered
    factory fails closed.
  - Core contains no vendor-specific equality branches on provider/runtime
    identifiers: vendor knowledge lives inside adapters and their
    registration calls only.
"""
from __future__ import annotations

from datetime import datetime
from typing import Callable

from polynexus_core.domain.runtime_binding import (
    RuntimeBindingError,
    RuntimeBindingSnapshot,
    RuntimeProfile,
)
from polynexus_core.domain.enums import (
    AuthOwnership,
    ExecutionTarget,
    TransportKind,
    UsageVisibility,
)
from polynexus_core.runtime.contracts import RuntimeAdapter
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter

# The only built-in profile in this gate.
REFERENCE_PROFILE_REF = "reference.local"

AdapterFactory = Callable[[], RuntimeAdapter]


def build_reference_profile() -> RuntimeProfile:
    """The single approved built-in profile: deterministic local reference runtime."""
    return RuntimeProfile(
        provider_id="polynexus",
        transport_kind=TransportKind.LOCAL,
        runtime_id="reference",
        adapter_id="builtin.reference",
        execution_target=ExecutionTarget.LOCAL,
        runtime_profile_ref=REFERENCE_PROFILE_REF,
        profile_revision=1,
        auth_ownership=AuthOwnership.NONE,
        secret_ref_id=None,
        usage_visibility=UsageVisibility.UNAVAILABLE,
    )


class RuntimeRegistry:
    """In-memory profile/factory registry with fail-closed resolution."""

    def __init__(self) -> None:
        self._profiles: dict[str, RuntimeProfile] = {}
        self._factories: dict[str, AdapterFactory] = {}

    def register(self, profile: RuntimeProfile, factory: AdapterFactory) -> None:
        """Register a profile and its adapter factory (composition-root wiring)."""
        if not callable(factory):
            raise RuntimeBindingError(
                "Adapter factory must be callable"
            )
        existing = self._profiles.get(profile.runtime_profile_ref)
        if existing is not None and existing != profile:
            raise RuntimeBindingError(
                "Conflicting profile registration for an already-registered reference"
            )
        registered_factory = self._factories.get(profile.adapter_id)
        if registered_factory is not None and registered_factory is not factory:
            raise RuntimeBindingError(
                "Conflicting adapter factory registration for an already-registered adapter"
            )
        self._profiles[profile.runtime_profile_ref] = profile
        self._factories[profile.adapter_id] = factory

    def resolve(self, profile_ref: str) -> RuntimeProfile:
        """Resolve a profile reference; unknown references fail closed.

        The rejection message never echoes the caller-supplied reference.
        """
        profile = self._profiles.get(profile_ref)
        if profile is None:
            raise RuntimeBindingError(
                "Unknown or unavailable runtime profile"
            )
        return profile

    def create_adapter(self, profile: RuntimeProfile) -> RuntimeAdapter:
        """Create the adapter for a resolved profile; unregistered fails closed."""
        factory = self._factories.get(profile.adapter_id)
        if factory is None:
            raise RuntimeBindingError(
                "No adapter factory registered for the resolved profile"
            )
        return factory()

    def bind(
        self,
        profile_ref: str,
        run_id: str,
        resolved_at: datetime,
    ) -> RuntimeBindingSnapshot:
        """Resolve a profile reference into an immutable Run-owned snapshot."""
        profile = self.resolve(profile_ref)
        return profile.bind(run_id=run_id, resolved_at=resolved_at)


def build_default_registry() -> RuntimeRegistry:
    """Composition root for the built-in reference binding (LOCAL/NONE)."""
    registry = RuntimeRegistry()
    registry.register(build_reference_profile(), ReferenceRuntimeAdapter)
    return registry
