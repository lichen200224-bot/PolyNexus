"""G16 runtime selection policy contract tests.

These tests cover only the approved V1 policy: reference.local, LOCAL
execution, no credential ownership, bounded selection inputs, and fail-closed
capability/auth compatibility.  They do not introduce a public API or schema.
"""
from __future__ import annotations

import pytest

from polynexus_core.domain.enums import (
    AuthOwnership,
    ExecutionTarget,
    ResumeMode,
    TransportKind,
    UsageVisibility,
)
from polynexus_core.domain.runtime_binding import RuntimeBindingError, RuntimeProfile
from polynexus_core.runtime.contracts import RuntimeCapabilities
from polynexus_core.runtime.registry import (
    REFERENCE_PROFILE_REF,
    RUNTIME_PROFILE_ENV,
    RuntimeRegistry,
    _select_profile_ref,
)


def test_selection_precedence_is_explicit_then_environment_then_default() -> None:
    environment = {RUNTIME_PROFILE_ENV: REFERENCE_PROFILE_REF}

    assert _select_profile_ref(
        explicit_request=REFERENCE_PROFILE_REF,
        environment={RUNTIME_PROFILE_ENV: "ignored.profile"},
    ) == REFERENCE_PROFILE_REF
    assert _select_profile_ref(environment=environment) == REFERENCE_PROFILE_REF
    assert _select_profile_ref(environment={}) == REFERENCE_PROFILE_REF


@pytest.mark.parametrize(
    "kwargs",
    [
        {"explicit_request": "not a profile", "environment": {}},
        {"environment": {RUNTIME_PROFILE_ENV: "not a profile"}},
        {"environment": {RUNTIME_PROFILE_ENV: ""}},
    ],
)
def test_invalid_higher_precedence_selection_fails_without_fallback(kwargs) -> None:
    with pytest.raises(RuntimeBindingError) as exc_info:
        _select_profile_ref(**kwargs)

    assert str(exc_info.value) == "Runtime profile selection is invalid"


def test_selected_profile_is_v1_reference_local_only() -> None:
    registry = RuntimeRegistry()
    registry.register(
        RuntimeProfile(
            provider_id="remote-provider",
            transport_kind=TransportKind.OFFICIAL_API,
            runtime_id="remote-runtime",
            adapter_id="builtin.remote",
            execution_target=ExecutionTarget.LOCAL,
            runtime_profile_ref="remote.default",
            auth_ownership=AuthOwnership.SECRET_REF,
            secret_ref_id="credential-ref-1",
        ),
        lambda: object(),  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeBindingError) as exc_info:
        registry._resolve_selected_profile(explicit_request="remote.default")

    assert str(exc_info.value) == (
        "Runtime profile is not allowed by V1 local-only policy"
    )


def test_unknown_selected_profile_fails_closed_without_echo() -> None:
    marker = "unknown.secret-profile"
    registry = RuntimeRegistry()

    with pytest.raises(RuntimeBindingError) as exc_info:
        registry._resolve_selected_profile(explicit_request=marker)

    assert marker not in str(exc_info.value)
    assert str(exc_info.value) == "Unknown or unavailable runtime profile"


class _CapabilitiesAdapter:
    def __init__(self, capabilities: RuntimeCapabilities) -> None:
        self._capabilities = capabilities

    def capabilities(self) -> RuntimeCapabilities:
        return self._capabilities


def test_adapter_auth_ownership_must_match_profile() -> None:
    registry = RuntimeRegistry()
    registry.register(
        _reference_profile(),
        lambda: _CapabilitiesAdapter(
            RuntimeCapabilities(auth_ownership=AuthOwnership.RUNTIME_MANAGED)
        ),
    )

    with pytest.raises(RuntimeBindingError) as exc_info:
        registry.create_adapter(registry.resolve(REFERENCE_PROFILE_REF))

    assert str(exc_info.value) == "Runtime authentication ownership is incompatible"


def test_required_capabilities_fail_closed_and_never_downgrade() -> None:
    registry = RuntimeRegistry()
    registry.register(
        _reference_profile(),
        lambda: _CapabilitiesAdapter(
            RuntimeCapabilities(
                cancel=True,
                resume=ResumeMode.NONE,
                artifacts=True,
                timeout_cleanup_verified=False,
                usage_visibility=UsageVisibility.UNAVAILABLE,
                auth_ownership=AuthOwnership.NONE,
            )
        ),
    )
    profile = registry.resolve(REFERENCE_PROFILE_REF)

    with pytest.raises(RuntimeBindingError) as exc_info:
        registry.create_adapter(
            profile,
            required_capabilities=("timeout_cleanup_verified",),
        )
    assert str(exc_info.value) == "Runtime capability compatibility check failed"

    with pytest.raises(RuntimeBindingError) as exc_info:
        registry.create_adapter(profile, required_capabilities=("unknown",))
    assert str(exc_info.value) == "Runtime capability compatibility check failed"


def test_reference_profile_and_adapter_pass_compatible_selection() -> None:
    from polynexus_core.runtime.reference import ReferenceRuntimeAdapter

    registry = RuntimeRegistry()
    registry.register(_reference_profile(), ReferenceRuntimeAdapter)
    profile = registry._resolve_selected_profile(
        explicit_request=REFERENCE_PROFILE_REF,
        environment={RUNTIME_PROFILE_ENV: REFERENCE_PROFILE_REF},
    )
    adapter = registry.create_adapter(
        profile,
        required_capabilities=("cancel", "artifacts", "timeout_cleanup_verified"),
    )

    assert isinstance(adapter, ReferenceRuntimeAdapter)


def _reference_profile() -> RuntimeProfile:
    from polynexus_core.runtime.registry import build_reference_profile

    return build_reference_profile()
