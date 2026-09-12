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

import os
from collections.abc import Iterable, Mapping
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
from polynexus_core.runtime.external_contracts import (
    ExternalRuntimeDefinition,
    PreparedExternalRun,
    ExternalRuntimeDescriptor,
    LaunchMode,
    ProtocolKind,
)
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter

# The deterministic local reference remains the default. Statically registered
# external profiles may be selected explicitly, but the environment variable is
# still limited to an opaque profile reference and never carries credentials,
# executable paths, or endpoints.
REFERENCE_PROFILE_REF = "reference.local"
DEFAULT_RUNTIME_PROFILE_REF = REFERENCE_PROFILE_REF
RUNTIME_PROFILE_ENV = "POLYNEXUS_RUNTIME_PROFILE_REF"

_UNKNOWN_PROFILE_REASON = "Unknown or unavailable runtime profile"
_INVALID_SELECTION_REASON = "Runtime profile selection is invalid"
_V1_PROFILE_POLICY_REASON = "Runtime profile is not allowed by V1 local-only policy"
_CAPABILITY_POLICY_REASON = "Runtime capability compatibility check failed"
_AUTH_POLICY_REASON = "Runtime authentication ownership is incompatible"
_CAPABILITY_NAMES = frozenset(
    {
        "cancel",
        "resume",
        "artifacts",
        "timeout_cleanup_verified",
        "usage_visibility",
        "auth_ownership",
        "external_sessions",
        "event_stream",
        "permission_requests",
        "egress_declaration",
    }
)

AdapterFactory = Callable[[], RuntimeAdapter]


def _select_profile_ref(
    *,
    explicit_request: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> str:
    """Apply the G16 precedence without introducing a public API or schema.

    Precedence is explicit request, then the allowlisted environment source,
    then the deterministic local default.  A present but invalid higher-
    precedence value fails closed instead of falling through to a default.
    """
    if explicit_request is not None:
        candidate = explicit_request
    else:
        source = os.environ if environment is None else environment
        try:
            has_environment_value = RUNTIME_PROFILE_ENV in source
            candidate = source.get(RUNTIME_PROFILE_ENV) if has_environment_value else None
        except Exception:
            raise RuntimeBindingError(_INVALID_SELECTION_REASON) from None
        if not has_environment_value:
            return DEFAULT_RUNTIME_PROFILE_REF

    if not isinstance(candidate, str) or not candidate:
        raise RuntimeBindingError(_INVALID_SELECTION_REASON)
    # Validate shape without echoing the selected value in any rejection.
    try:
        from polynexus_core.domain.runtime_binding import validate_opaque_identifier

        return validate_opaque_identifier(candidate, "runtime_profile_ref")
    except RuntimeBindingError:
        raise RuntimeBindingError(_INVALID_SELECTION_REASON) from None


def _validate_v1_profile(profile: RuntimeProfile) -> None:
    """Enforce the V1 local-only policy for reference and opt-in profiles."""
    try:
        observed = (
            profile.provider_id,
            profile.transport_kind,
            profile.runtime_id,
            profile.adapter_id,
            profile.execution_target,
            profile.runtime_profile_ref,
            profile.profile_revision,
            profile.auth_ownership,
            profile.secret_ref_id,
            profile.usage_visibility,
        ) if isinstance(profile, RuntimeProfile) else None
        reference_allowed = observed == (
            "polynexus",
            TransportKind.LOCAL,
            "reference",
            "builtin.reference",
            ExecutionTarget.LOCAL,
            REFERENCE_PROFILE_REF,
            1,
            AuthOwnership.NONE,
            None,
            UsageVisibility.UNAVAILABLE,
        )
        # CP-04 adds explicitly registered in-memory local endpoint profiles.
        # The profile still carries no endpoint or credential and remains
        # LOCAL/NONE; endpoint loopback validation belongs to the adapter.
        local_endpoint_allowed = (
            profile.transport_kind is TransportKind.LOCAL
            and profile.execution_target is ExecutionTarget.LOCAL
            and profile.auth_ownership is AuthOwnership.NONE
            and profile.secret_ref_id is None
            and profile.usage_visibility is UsageVisibility.UNAVAILABLE
        )
        allowed = reference_allowed or local_endpoint_allowed
    except Exception:
        allowed = False
    if not allowed:
        raise RuntimeBindingError(_V1_PROFILE_POLICY_REASON)


def _capability_satisfied(capabilities: object, name: str) -> bool:
    """Return whether a named normalized capability is actually available."""
    try:
        value = getattr(capabilities, name)
        if name in {
            "cancel",
            "artifacts",
            "timeout_cleanup_verified",
            "external_sessions",
            "event_stream",
            "permission_requests",
            "egress_declaration",
        }:
            return value is True
        if name == "resume":
            from polynexus_core.domain.enums import ResumeMode

            return isinstance(value, ResumeMode) and value is not ResumeMode.NONE
        if name == "usage_visibility":
            return (
                isinstance(value, UsageVisibility)
                and value is not UsageVisibility.UNAVAILABLE
            )
        if name == "auth_ownership":
            return isinstance(value, AuthOwnership)
    except Exception:
        return False
    return False


def _validate_adapter_compatibility(
    profile: RuntimeProfile,
    adapter: RuntimeAdapter,
    required_capabilities: Iterable[str] = (),
) -> None:
    """Check auth ownership and requested capabilities without fallback."""
    try:
        capabilities = adapter.capabilities()
        if capabilities.auth_ownership is not profile.auth_ownership:
            raise RuntimeBindingError(_AUTH_POLICY_REASON)
        required = tuple(required_capabilities)
    except RuntimeBindingError:
        raise
    except Exception:
        raise RuntimeBindingError(_CAPABILITY_POLICY_REASON) from None

    if any(not isinstance(name, str) or name not in _CAPABILITY_NAMES for name in required):
        raise RuntimeBindingError(_CAPABILITY_POLICY_REASON)
    if not all(_capability_satisfied(capabilities, name) for name in required):
        raise RuntimeBindingError(_CAPABILITY_POLICY_REASON)


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
        self._external_definitions: dict[str, ExternalRuntimeDefinition] = {}
        self._external_factories: dict[str, Callable] = {}

    def register(self, profile: RuntimeProfile, factory: AdapterFactory) -> None:
        """Register a profile and its adapter factory (composition-root wiring)."""
        self.register_many(((profile, factory),))

    def register_many(
        self, registrations: Iterable[tuple[RuntimeProfile, AdapterFactory]]
    ) -> None:
        """Atomically publish static composition registrations or leave unchanged.

        This is the existing registry's conflict policy applied to a whole
        batch; no factories are invoked and no parallel runtime registry exists.
        Composition remains single-threaded, before Run execution starts.
        """
        profiles = self._profiles.copy()
        factories = self._factories.copy()
        for profile, factory in registrations:
            if not callable(factory):
                raise RuntimeBindingError("Adapter factory must be callable")
            existing = profiles.get(profile.runtime_profile_ref)
            if existing is not None and existing != profile:
                raise RuntimeBindingError(
                    "Conflicting profile registration for an already-registered reference"
                )
            registered_factory = factories.get(profile.adapter_id)
            if registered_factory is not None and registered_factory is not factory:
                raise RuntimeBindingError(
                    "Conflicting adapter factory registration for an already-registered adapter"
                )
            profiles[profile.runtime_profile_ref] = profile
            factories[profile.adapter_id] = factory
        self._profiles = profiles
        self._factories = factories

    def register_external(
        self, profile: RuntimeProfile, factory: Callable,
        definition: ExternalRuntimeDefinition,
    ) -> None:
        """Register static policy and a factory taking one PreparedExternalRun."""
        if type(definition) is not ExternalRuntimeDefinition or not callable(factory):
            raise RuntimeBindingError("Invalid external definition")
        descriptor = definition.descriptor
        identity = (profile.provider_id, profile.runtime_id, profile.adapter_id, profile.runtime_profile_ref)
        declared = (descriptor.provider_id, descriptor.runtime_id, descriptor.adapter_id, descriptor.runtime_profile_ref)
        if identity != declared or profile.auth_ownership is not descriptor.auth_ownership:
            raise RuntimeBindingError("External runtime identity mismatch")
        if profile.transport_kind is not TransportKind.LOCAL or profile.execution_target is not ExecutionTarget.LOCAL:
            raise RuntimeBindingError("External runtime transport mismatch")
        if profile.runtime_profile_ref in self._profiles or profile.adapter_id in self._factories:
            raise RuntimeBindingError("Conflicting external runtime registration")
        if profile.adapter_id in {p.adapter_id for p in self._profiles.values()}:
            raise RuntimeBindingError("Conflicting external adapter registration")
        from dataclasses import replace
        self._profiles[profile.runtime_profile_ref] = replace(profile)
        self._external_definitions[profile.runtime_profile_ref] = definition
        self._external_factories[profile.runtime_profile_ref] = factory

    def prepare_external(self, profile: RuntimeProfile, run_id: str, task, context):
        definition = self._external_definitions.get(profile.runtime_profile_ref)
        if definition is None:
            return None
        self._validate_external_profile(profile)
        return definition.prepare(run_id, task, context)

    def create_external_adapter(self, profile: RuntimeProfile, prepared: PreparedExternalRun, snapshot):
        self._validate_external_profile(profile)
        definition = self._external_definitions[profile.runtime_profile_ref]
        from dataclasses import replace
        if replace(prepared.descriptor, execution_envelope_ref="0" * 64) != definition.descriptor:
            raise RuntimeBindingError("External descriptor identity mismatch")
        if prepared.envelope.executable_identity != definition.executable:
            raise RuntimeBindingError("External executable identity mismatch")
        if prepared.envelope.effective_runtime_configuration_fingerprint != definition.effective_config_digest:
            raise RuntimeBindingError("External config policy mismatch")
        prepared.validate(snapshot)
        adapter = self._external_factories[profile.runtime_profile_ref](prepared)
        _validate_adapter_compatibility(profile, adapter, ())
        if adapter.envelope != prepared.envelope or adapter.descriptor != prepared.descriptor:
            raise RuntimeBindingError("External factory scope mismatch")
        adapter.bind_core_run(snapshot)
        return adapter

    def resolve(self, profile_ref: str) -> RuntimeProfile:
        """Resolve a profile reference; unknown references fail closed.

        The rejection message never echoes the caller-supplied reference.
        """
        try:
            profile = self._profiles.get(profile_ref) if isinstance(profile_ref, str) else None
        except Exception:
            profile = None
        if profile is None:
            raise RuntimeBindingError(_UNKNOWN_PROFILE_REASON)
        return profile

    def _resolve_selected_profile(
        self,
        *,
        explicit_request: str | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> RuntimeProfile:
        """Resolve the effective V1 selection and enforce its policy."""
        profile_ref = _select_profile_ref(
            explicit_request=explicit_request,
            environment=environment,
        )
        profile = self.resolve(profile_ref)
        if profile.runtime_profile_ref in self._external_definitions:
            self._validate_external_profile(profile)
        else:
            _validate_v1_profile(profile)
        return profile

    def _validate_external_profile(self, profile: RuntimeProfile) -> None:
        definition = self._external_definitions.get(profile.runtime_profile_ref)
        if definition is None:
            raise RuntimeBindingError("Missing external definition")
        descriptor = definition.descriptor
        if (
            descriptor.provider_id != profile.provider_id
            or descriptor.runtime_id != profile.runtime_id
            or descriptor.adapter_id != profile.adapter_id
            or descriptor.auth_ownership is not profile.auth_ownership
        ):
            raise RuntimeBindingError("External profile identity mismatch")

    def create_adapter(
        self,
        profile: RuntimeProfile,
        *,
        required_capabilities: Iterable[str] = (),
    ) -> RuntimeAdapter:
        """Create the adapter for a resolved profile; unregistered fails closed."""
        factory = self._factories.get(profile.adapter_id)
        if factory is None:
            raise RuntimeBindingError(
                "No adapter factory registered for the resolved profile"
            )
        adapter = factory()
        _validate_adapter_compatibility(profile, adapter, required_capabilities)
        return adapter

    def _create_adapter_for_observation(self, profile: RuntimeProfile) -> RuntimeAdapter:
        """Construct a registered adapter without execution compatibility checks.

        Doctor must observe capability/version declaration failures separately
        from factory failures.  Execution callers continue to use
        ``create_adapter()``, which retains auth and required-capability
        validation.  This private observation seam still uses the Registry's
        registered factory and never falls back to the reference adapter.
        """
        try:
            factory = self._factories.get(profile.adapter_id)
        except Exception:
            factory = None
        if factory is None:
            raise RuntimeBindingError(
                "No adapter factory registered for the resolved profile"
            ) from None
        return factory()

    def inspect_selected_profile(
        self,
        *,
        explicit_request: str | None = None,
        environment: Mapping[str, str] | None = None,
        required_capabilities: Iterable[str] = (),
    ) -> tuple[RuntimeProfile, RuntimeAdapter]:
        """Return a policy-validated profile and adapter for internal Doctor use.

        This deliberately reuses the normal G16 selection and compatibility
        path.  Doctor must never inspect an unvalidated profile or silently
        replace an unavailable runtime with the reference adapter.
        """
        profile = self._resolve_selected_profile(
            explicit_request=explicit_request,
            environment=environment,
        )
        adapter = self.create_adapter(
            profile,
            required_capabilities=required_capabilities,
        )
        return profile, adapter

    def bind(
        self,
        profile_ref: str,
        run_id: str,
        resolved_at: datetime,
    ) -> RuntimeBindingSnapshot:
        """Resolve a profile reference into an immutable Run-owned snapshot."""
        profile = self.resolve(profile_ref)
        if profile_ref in self._external_definitions:
            raise RuntimeBindingError("External binding requires Run-scoped preparation")
        return profile.bind(run_id=run_id, resolved_at=resolved_at)



def build_default_registry() -> RuntimeRegistry:
    """Composition root for the built-in reference binding (LOCAL/NONE)."""
    registry = RuntimeRegistry()
    registry.register(build_reference_profile(), ReferenceRuntimeAdapter)
    return registry


def register_local_endpoint_profile(
    registry: RuntimeRegistry,
    profile: RuntimeProfile,
    factory: AdapterFactory,
) -> None:
    """Register a caller-selected LOCAL/NONE endpoint profile explicitly.

    This composition helper does not inspect or persist an endpoint URL.  The
    factory must construct an adapter that enforces the loopback policy.
    """

    try:
        allowed = (
            profile.transport_kind is TransportKind.LOCAL
            and profile.execution_target is ExecutionTarget.LOCAL
            and profile.auth_ownership is AuthOwnership.NONE
            and profile.secret_ref_id is None
            and profile.usage_visibility is UsageVisibility.UNAVAILABLE
        )
    except Exception:
        allowed = False
    if not allowed:
        raise RuntimeBindingError(_V1_PROFILE_POLICY_REASON)
    registry.register(profile, factory)
