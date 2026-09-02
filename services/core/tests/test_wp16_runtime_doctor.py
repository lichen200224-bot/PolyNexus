"""WP-16 Core-only deterministic Runtime Doctor conformance tests."""
from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from polynexus_core.domain.enums import (
    AuthOwnership,
    ExecutionTarget,
    ResumeMode,
    TransportKind,
    UsageVisibility,
)
from polynexus_core.domain.runtime_binding import RuntimeBindingError
from polynexus_core.runtime.contracts import RuntimeCapabilities
from polynexus_core.runtime.doctor import (
    ADAPTER_DECLARATION,
    CURRENT_PROBE,
    DEFAULT_DOCTOR_RUNTIME_SPECS,
    DOCTOR_CONTRACT_VERSION,
    UNAVAILABLE,
    DoctorConformanceEvidence,
    DoctorErrorCategory,
    DoctorMaturity,
    DoctorReportStatus,
    DoctorRuntimeSpec,
    RuntimeDoctor,
    build_default_doctor,
)
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.registry import build_default_registry


FIXED_TIMESTAMP = datetime(2026, 8, 27, 12, 34, 56, tzinfo=timezone.utc)
SECRET_MARKER = "SECRET_MARKER_WP16_DOCTOR_TOKEN_COOKIE_SESSION_API_KEY"


def _evidence(scope: str = "TEST_ONLY") -> DoctorConformanceEvidence:
    return DoctorConformanceEvidence(
        source="TEST_EVIDENCE",
        outcome="UNVERIFIED",
        scope=scope,
        checkpoint="test-checkpoint",
        test_source="services/core/tests/test_wp16_runtime_doctor.py",
    )


def _spec(
    factory,
    *,
    ref: str = "test.doctor.local",
    runtime_id: str = "test-runtime",
    adapter_id: str = "test.doctor-adapter",
    maturity: DoctorMaturity = DoctorMaturity.EXPERIMENTAL,
    evidence: DoctorConformanceEvidence | None = None,
) -> DoctorRuntimeSpec:
    return DoctorRuntimeSpec(
        provider_id="test-provider",
        transport_kind=TransportKind.LOCAL,
        runtime_id=runtime_id,
        adapter_id=adapter_id,
        runtime_profile_ref=ref,
        factory=factory,
        maturity=maturity,
        evidence=evidence or _evidence(),
        execution_target=ExecutionTarget.LOCAL,
        profile_revision=1,
        auth_ownership=AuthOwnership.NONE,
        usage_visibility=UsageVisibility.UNAVAILABLE,
    )


class _ProbeAdapter(ReferenceRuntimeAdapter):
    def __init__(
        self,
        *,
        health_value: object = True,
        readiness_value: object = True,
        capabilities_value: object = None,
        version_value: object = "test-adapter/1.0",
        health_error: Exception | None = None,
        readiness_error: Exception | None = None,
        capabilities_error: Exception | None = None,
        version_error: Exception | None = None,
    ) -> None:
        super().__init__()
        self.health_value = health_value
        self.readiness_value = readiness_value
        self.capabilities_value = capabilities_value
        self.version_value = version_value
        self.health_error = health_error
        self.readiness_error = readiness_error
        self.capabilities_error = capabilities_error
        self.version_error = version_error

    async def health(self) -> bool:
        if self.health_error is not None:
            raise self.health_error
        return self.health_value  # type: ignore[return-value]

    async def readiness(self) -> bool:
        if self.readiness_error is not None:
            raise self.readiness_error
        return self.readiness_value  # type: ignore[return-value]

    def capabilities(self) -> RuntimeCapabilities:
        if self.capabilities_error is not None:
            raise self.capabilities_error
        if self.capabilities_value is None:
            return RuntimeCapabilities(
                cancel=True,
                resume=ResumeMode.NONE,
                artifacts=True,
                timeout_cleanup_verified=True,
                usage_visibility=UsageVisibility.UNAVAILABLE,
                auth_ownership=AuthOwnership.NONE,
            )
        return self.capabilities_value  # type: ignore[return-value]

    def version_info(self) -> str:
        if self.version_error is not None:
            raise self.version_error
        return self.version_value  # type: ignore[return-value]


def _factory(adapter: _ProbeAdapter):
    return lambda: adapter


def _collect(doctor: RuntimeDoctor):
    return asyncio.run(doctor.collect())


def _assert_marker_absent(report) -> None:  # type: ignore[no-untyped-def]
    assert SECRET_MARKER not in repr(report)
    assert SECRET_MARKER not in str(report)


def test_default_inventory_is_immutable_ordered_and_truthfully_labeled() -> None:
    assert isinstance(DEFAULT_DOCTOR_RUNTIME_SPECS, tuple)
    assert [spec.runtime_profile_ref for spec in DEFAULT_DOCTOR_RUNTIME_SPECS] == [
        "reference.local",
        "conformance.codex.local",
        "conformance.opencode.local",
    ]
    assert DEFAULT_DOCTOR_RUNTIME_SPECS[0].maturity is DoctorMaturity.SUPPORTED
    assert all(
        spec.maturity is DoctorMaturity.EXPERIMENTAL
        for spec in DEFAULT_DOCTOR_RUNTIME_SPECS[1:]
    )
    assert all(spec.evidence.scope != "PRODUCTION" for spec in DEFAULT_DOCTOR_RUNTIME_SPECS)


@pytest.mark.parametrize(
    "spec",
    [
        replace(DEFAULT_DOCTOR_RUNTIME_SPECS[0], runtime_id="spoofed-reference"),
        replace(
            DEFAULT_DOCTOR_RUNTIME_SPECS[1],
            maturity=DoctorMaturity.SUPPORTED,
        ),
        replace(
            DEFAULT_DOCTOR_RUNTIME_SPECS[1],
            evidence=replace(
                DEFAULT_DOCTOR_RUNTIME_SPECS[1].evidence,
                outcome="CERTIFIED",
            ),
        ),
        replace(
            DEFAULT_DOCTOR_RUNTIME_SPECS[1],
            evidence=replace(
                DEFAULT_DOCTOR_RUNTIME_SPECS[1].evidence,
                scope="PRODUCTION",
            ),
        ),
        replace(
            DEFAULT_DOCTOR_RUNTIME_SPECS[1],
            runtime_profile_ref="custom.codex.local",
            evidence=replace(
                DEFAULT_DOCTOR_RUNTIME_SPECS[1].evidence,
                outcome="CERTIFIED",
            ),
        ),
        replace(
            DEFAULT_DOCTOR_RUNTIME_SPECS[2],
            runtime_profile_ref="custom.opencode.local",
            evidence=replace(
                DEFAULT_DOCTOR_RUNTIME_SPECS[2].evidence,
                scope="PRODUCTION",
            ),
        ),
        replace(
            DEFAULT_DOCTOR_RUNTIME_SPECS[0],
            runtime_profile_ref="custom.reference.local",
        ),
        replace(
            DEFAULT_DOCTOR_RUNTIME_SPECS[1],
            provider_id="unrecognized-provider",
        ),
        replace(
            DEFAULT_DOCTOR_RUNTIME_SPECS[1],
            factory=lambda: _ProbeAdapter(),
        ),
    ],
    ids=[
        "reference-identity",
        "codex-supported",
        "certified-outcome",
        "production-scope",
        "codex-profile-alias",
        "opencode-profile-alias",
        "reference-profile-alias",
        "arbitrary-identity-with-canonical-pass",
        "canonical-identity-with-substituted-factory",
    ],
)
def test_prohibited_maturity_or_evidence_fails_closed(spec: DoctorRuntimeSpec) -> None:
    report = _collect(RuntimeDoctor((spec,), clock=lambda: FIXED_TIMESTAMP))

    assert report.status is DoctorReportStatus.FAILED
    assert report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert report.entries == ()


def test_generic_non_reference_supported_inventory_fails_closed() -> None:
    spec = _spec(lambda: _ProbeAdapter(), maturity=DoctorMaturity.SUPPORTED)

    report = _collect(RuntimeDoctor((spec,), clock=lambda: FIXED_TIMESTAMP))

    assert report.status is DoctorReportStatus.FAILED
    assert report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert report.entries == ()


@pytest.mark.parametrize(
    ("outcome", "scope"),
    (
        ("CERTIFIED", "DETERMINISTIC_LOCAL_CONFORMANCE"),
        ("COMPLETE", "DETERMINISTIC_LOCAL_CONFORMANCE"),
        ("PASS", "PRODUCTION"),
        ("PASS", "UNSUPPORTED_SCOPE"),
    ),
)
def test_custom_runtime_rejects_unsupported_evidence_labels(
    outcome: str,
    scope: str,
) -> None:
    evidence = replace(_evidence(), outcome=outcome, scope=scope)
    spec = _spec(
        _factory(_ProbeAdapter()),
        ref="custom.runtime",
        runtime_id="custom-runtime",
        adapter_id="custom.adapter",
        evidence=evidence,
    )

    report = _collect(RuntimeDoctor((spec,), clock=lambda: FIXED_TIMESTAMP))

    assert report.status is DoctorReportStatus.FAILED
    assert report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert report.entries == ()


def test_custom_test_evidence_is_explicitly_unverified_and_never_pass() -> None:
    report = _collect(
        RuntimeDoctor(
            (_spec(_factory(_ProbeAdapter())),),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )

    assert report.status is DoctorReportStatus.COMPLETE
    assert report.entries[0].conformance_evidence.outcome == "UNVERIFIED"
    assert report.entries[0].conformance_evidence.scope == "TEST_ONLY"


def test_default_doctor_reports_identity_probe_declarations_and_evidence() -> None:
    report = _collect(build_default_doctor(clock=lambda: FIXED_TIMESTAMP))

    assert report.contract_version == DOCTOR_CONTRACT_VERSION
    assert report.status is DoctorReportStatus.COMPLETE
    assert report.error_category is None
    assert report.timestamp == FIXED_TIMESTAMP
    assert report.timestamp.tzinfo is not None
    assert report.observed_at == FIXED_TIMESTAMP
    assert len(report.entries) == 3

    reference, codex, opencode = report.entries
    assert (reference.provider_id, reference.runtime_id, reference.adapter_id) == (
        "polynexus",
        "reference",
        "builtin.reference",
    )
    assert (codex.provider_id, codex.runtime_id, codex.adapter_id) == (
        "polynexus",
        "codex-conformance",
        "builtin.codex-conformance",
    )
    assert (opencode.provider_id, opencode.runtime_id, opencode.adapter_id) == (
        "polynexus",
        "opencode-conformance",
        "builtin.opencode-conformance",
    )
    for entry in report.entries:
        assert entry.transport_kind is TransportKind.LOCAL
        assert entry.execution_target is ExecutionTarget.LOCAL
        assert entry.health is True
        assert entry.health_source == CURRENT_PROBE
        assert entry.readiness is True
        assert entry.readiness_source == CURRENT_PROBE
        assert entry.capabilities_source == ADAPTER_DECLARATION
        assert entry.capabilities is not None
        assert entry.runtime_version is None
        assert entry.runtime_version_source == UNAVAILABLE
        assert entry.adapter_version is not None
        assert entry.adapter_version_source == ADAPTER_DECLARATION
        if entry is reference:
            assert entry.evidence_source == "DETERMINISTIC_REFERENCE_TESTS"
        else:
            assert entry.evidence_source == "INDEPENDENT_CONFORMANCE_REVIEW"
        assert entry.conformance_evidence.outcome == "PASS"
        assert entry.error_category is None

    assert reference.adapter_version == "reference-runtime/0.1"
    assert codex.adapter_version == "codex-local-adapter/0.1"
    assert opencode.adapter_version == "opencode-local-adapter/0.1"
    assert reference.conformance_evidence.scope == "DETERMINISTIC_REFERENCE_RUNTIME"
    assert codex.conformance_evidence.scope == "DETERMINISTIC_LOCAL_CONFORMANCE"
    assert opencode.conformance_evidence.scope == "DETERMINISTIC_LOCAL_CONFORMANCE"
    assert codex.maturity is DoctorMaturity.EXPERIMENTAL
    assert opencode.maturity is DoctorMaturity.EXPERIMENTAL


def test_capability_declaration_is_separate_from_conformance_evidence() -> None:
    report = _collect(build_default_doctor())
    for entry in report.entries:
        assert entry.capabilities_source == ADAPTER_DECLARATION
        assert entry.evidence_source != entry.capabilities_source
        assert entry.conformance_evidence.test_source
        assert entry.conformance_evidence.checkpoint == (
            "65c6582c70c4e724005adb983d65aba10ea3e8be"
        )


def test_doctor_does_not_change_execution_default_registry_or_add_fallback() -> None:
    _collect(build_default_doctor())
    registry = build_default_registry()
    with pytest.raises(RuntimeBindingError):
        registry.resolve("conformance.codex.local")
    with pytest.raises(RuntimeBindingError):
        registry.resolve("conformance.opencode.local")


def test_false_health_is_a_complete_report_but_not_a_healthy_claim() -> None:
    adapter = _ProbeAdapter(health_value=False, readiness_value=False)
    report = _collect(
        RuntimeDoctor(
            (_spec(_factory(adapter)),),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )

    entry = report.entries[0]
    assert report.status is DoctorReportStatus.COMPLETE
    assert report.error_category is None
    assert entry.health is False
    assert entry.readiness is False
    assert entry.error_category is None


def test_factory_failure_is_sanitized_partial_and_has_no_reference_fallback() -> None:
    def exploding_factory():
        raise RuntimeError(f"factory secret {SECRET_MARKER}")

    specs = (
        DEFAULT_DOCTOR_RUNTIME_SPECS[0],
        _spec(
            exploding_factory,
            ref="test.codex.failure",
            runtime_id="test-codex-failure",
            adapter_id="test.codex-failure-adapter",
        ),
        DEFAULT_DOCTOR_RUNTIME_SPECS[2],
    )
    report = _collect(RuntimeDoctor(specs, clock=lambda: FIXED_TIMESTAMP))

    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is DoctorErrorCategory.FACTORY_FAILURE
    assert len(report.entries) == 3
    assert report.entries[0].health is True
    assert report.entries[1].runtime_profile_ref == "test.codex.failure"
    assert report.entries[1].health is None
    assert report.entries[1].health_source == UNAVAILABLE
    assert report.entries[1].readiness is None
    assert report.entries[1].readiness_source == UNAVAILABLE
    assert report.entries[1].capabilities is None
    assert report.entries[1].capabilities_source == UNAVAILABLE
    assert report.entries[1].adapter_version is None
    assert report.entries[1].adapter_version_source == UNAVAILABLE
    assert report.entries[1].error_category is DoctorErrorCategory.FACTORY_FAILURE
    assert report.entries[2].health is True
    _assert_marker_absent(report)


@pytest.mark.parametrize(
    ("failure_field", "error_category"),
    (
        ("health_error", DoctorErrorCategory.HEALTH_FAILURE),
        ("readiness_error", DoctorErrorCategory.READINESS_FAILURE),
        ("capabilities_error", DoctorErrorCategory.CAPABILITIES_FAILURE),
        ("version_error", DoctorErrorCategory.VERSION_FAILURE),
    ),
)
def test_probe_exceptions_are_sanitized_and_reported_partial(
    failure_field: str,
    error_category: DoctorErrorCategory,
) -> None:
    adapter = _ProbeAdapter(
        **{failure_field: RuntimeError(f"probe secret {SECRET_MARKER}")}
    )
    report = _collect(
        RuntimeDoctor(
            (_spec(_factory(adapter)),),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )

    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is error_category
    entry = report.entries[0]
    assert entry.error_category is error_category
    assert entry.health is None if failure_field == "health_error" else True
    assert entry.readiness is None if failure_field == "readiness_error" else True
    if failure_field == "capabilities_error":
        assert entry.capabilities is None
    else:
        assert entry.capabilities is not None
    if failure_field == "version_error":
        assert entry.adapter_version is None
    else:
        assert entry.adapter_version == "test-adapter/1.0"
    _assert_marker_absent(report)


def test_invalid_declared_shapes_fail_closed_without_raw_error_material() -> None:
    adapter = _ProbeAdapter(capabilities_value=object(), version_value=object())
    report = _collect(
        RuntimeDoctor(
            (_spec(_factory(adapter)),),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )

    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is DoctorErrorCategory.CAPABILITIES_FAILURE
    assert report.entries[0].capabilities is None
    assert report.entries[0].adapter_version is None
    assert report.entries[0].error_category is DoctorErrorCategory.CAPABILITIES_FAILURE
    _assert_marker_absent(report)


@pytest.mark.parametrize(
    "field",
    (
        "cancel",
        "resume",
        "artifacts",
        "timeout_cleanup_verified",
        "usage_visibility",
        "auth_ownership",
    ),
)
def test_malformed_capability_fields_fail_closed_without_raw_values(
    field: str,
) -> None:
    capabilities = replace(
        RuntimeCapabilities(),
        **{field: SECRET_MARKER},
    )
    adapter = _ProbeAdapter(capabilities_value=capabilities)
    report = _collect(
        RuntimeDoctor(
            (_spec(_factory(adapter)),),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )

    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is DoctorErrorCategory.CAPABILITIES_FAILURE
    assert report.entries[0].capabilities is None
    assert report.entries[0].error_category is DoctorErrorCategory.CAPABILITIES_FAILURE
    _assert_marker_absent(report)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("source", "HUMAN_APPROVED"),
        ("outcome", "VERIFIED"),
        ("scope", "AUTHORIZED_SCOPE"),
        ("checkpoint", "accepted-by-human"),
        ("checkpoint", "opaque-7f3a9c2e"),
        ("checkpoint", SECRET_MARKER),
        ("test_source", "services/core/tests/production-token.txt"),
        ("test_source", "review/evidence-2026"),
    ),
)
def test_custom_evidence_metadata_requires_exact_allowlist(
    field: str,
    value: str,
) -> None:
    evidence = replace(_evidence(), **{field: value})
    spec = _spec(
        _factory(_ProbeAdapter()),
        ref="custom.runtime",
        runtime_id="custom-runtime",
        adapter_id="custom.adapter",
        evidence=evidence,
    )

    report = _collect(RuntimeDoctor((spec,), clock=lambda: FIXED_TIMESTAMP))

    assert report.status is DoctorReportStatus.FAILED
    assert report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert report.entries == ()
    _assert_marker_absent(report)


@pytest.mark.parametrize(
    "unsafe_version",
    (
        SECRET_MARKER,
        "Bearer sk-test-secret",
        "v1.0\nleak",
        "x" * 129,
    ),
)
def test_unsafe_adapter_versions_are_rejected_without_leaking_values(
    unsafe_version: str,
) -> None:
    adapter = _ProbeAdapter(version_value=unsafe_version)
    report = _collect(
        RuntimeDoctor(
            (_spec(_factory(adapter)),),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )

    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is DoctorErrorCategory.VERSION_FAILURE
    entry = report.entries[0]
    assert entry.adapter_version is None
    assert entry.adapter_version_source == ADAPTER_DECLARATION
    assert entry.error_category is DoctorErrorCategory.VERSION_FAILURE
    _assert_marker_absent(report)


class _TimeoutAdapter(ReferenceRuntimeAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.cancelled = False

    async def health(self) -> bool:
        try:
            await asyncio.sleep(60)
        finally:
            self.cancelled = True
        return True


class _ExternallyCancelledAdapter(ReferenceRuntimeAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.started = asyncio.Event()
        self.cancelled = False

    async def health(self) -> bool:
        self.started.set()
        try:
            await asyncio.sleep(60)
        finally:
            self.cancelled = True
        return True


def test_probe_timeout_cancels_probe_and_returns_partial_report() -> None:
    adapter = _TimeoutAdapter()
    report = _collect(
        RuntimeDoctor(
            (_spec(lambda: adapter),),
            clock=lambda: FIXED_TIMESTAMP,
            probe_timeout=0.01,
        )
    )

    assert adapter.cancelled is True
    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is DoctorErrorCategory.PROBE_TIMEOUT
    assert report.entries[0].health is None
    assert report.entries[0].readiness is True
    assert report.entries[0].error_category is DoctorErrorCategory.PROBE_TIMEOUT
    _assert_marker_absent(report)


def test_external_collection_cancellation_cleans_up_inflight_probe() -> None:
    async def scenario() -> _ExternallyCancelledAdapter:
        adapter = _ExternallyCancelledAdapter()
        task = asyncio.create_task(
            RuntimeDoctor(
                (_spec(lambda: adapter),),
                clock=lambda: FIXED_TIMESTAMP,
            ).collect()
        )
        await adapter.started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return adapter

    adapter = asyncio.run(scenario())
    assert adapter.cancelled is True


def test_invalid_or_duplicate_inventory_fails_closed_with_empty_entries() -> None:
    duplicate = replace(
        DEFAULT_DOCTOR_RUNTIME_SPECS[0],
        factory=lambda: ReferenceRuntimeAdapter(),
    )
    duplicate_report = _collect(
        RuntimeDoctor(
            (DEFAULT_DOCTOR_RUNTIME_SPECS[0], duplicate),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )
    assert duplicate_report.status is DoctorReportStatus.FAILED
    assert duplicate_report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert duplicate_report.entries == ()

    invalid = replace(
        DEFAULT_DOCTOR_RUNTIME_SPECS[0],
        runtime_profile_ref=f"bad ref {SECRET_MARKER}",
    )
    invalid_report = _collect(
        RuntimeDoctor((invalid,), clock=lambda: FIXED_TIMESTAMP)
    )
    assert invalid_report.status is DoctorReportStatus.FAILED
    assert invalid_report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert invalid_report.entries == ()
    _assert_marker_absent(duplicate_report)
    _assert_marker_absent(invalid_report)

    non_callable = replace(
        DEFAULT_DOCTOR_RUNTIME_SPECS[0],
        factory=object(),
    )
    non_callable_report = _collect(
        RuntimeDoctor((non_callable,), clock=lambda: FIXED_TIMESTAMP)
    )
    assert non_callable_report.status is DoctorReportStatus.FAILED
    assert non_callable_report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert non_callable_report.entries == ()
    _assert_marker_absent(non_callable_report)


def test_malformed_unhashable_inventory_fails_closed() -> None:
    # BLOCKER regression: unhashable runtime_profile_ref must not leak TypeError
    unhashable_spec = DoctorRuntimeSpec(
        provider_id="test-provider",
        transport_kind=TransportKind.LOCAL,
        runtime_id="test-runtime",
        adapter_id="test.doctor-adapter",
        runtime_profile_ref=[],  # type: ignore[arg-type]  # unhashable
        factory=lambda: ReferenceRuntimeAdapter(),
        maturity=DoctorMaturity.EXPERIMENTAL,
        evidence=_evidence(),
    )
    report = _collect(RuntimeDoctor((unhashable_spec,), clock=lambda: FIXED_TIMESTAMP))
    assert report.status is DoctorReportStatus.FAILED
    assert report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert report.entries == ()
    _assert_marker_absent(report)

    # empty adapter_id also fail-closed
    empty_adapter_spec = replace(DEFAULT_DOCTOR_RUNTIME_SPECS[0], adapter_id="")
    empty_report = _collect(RuntimeDoctor((empty_adapter_spec,), clock=lambda: FIXED_TIMESTAMP))
    assert empty_report.status is DoctorReportStatus.FAILED
    assert empty_report.error_category is DoctorErrorCategory.INVENTORY_INVALID


def test_factory_failure_sources_are_unavailable() -> None:
    def exploding_factory():
        raise RuntimeError(f"factory secret {SECRET_MARKER}")

    spec = _spec(
        exploding_factory,
        ref="test.codex.failure",
        runtime_id="test-codex-failure",
        adapter_id="test.codex-failure-adapter",
    )
    report = _collect(RuntimeDoctor((spec,), clock=lambda: FIXED_TIMESTAMP))
    assert report.status is DoctorReportStatus.PARTIAL
    entry = report.entries[0]
    assert entry.error_category is DoctorErrorCategory.FACTORY_FAILURE
    assert entry.health is None
    assert entry.health_source == UNAVAILABLE
    assert entry.readiness is None
    assert entry.readiness_source == UNAVAILABLE
    assert entry.capabilities is None
    assert entry.capabilities_source == UNAVAILABLE
    assert entry.adapter_version is None
    assert entry.adapter_version_source == UNAVAILABLE
    assert entry.runtime_version is None
    assert entry.runtime_version_source == UNAVAILABLE
    _assert_marker_absent(report)


def test_factory_cancellation_is_sanitized_without_leaking_marker() -> None:
    def cancelling_factory():
        raise asyncio.CancelledError(f"factory secret {SECRET_MARKER}")

    report = _collect(
        RuntimeDoctor(
            (_spec(cancelling_factory),),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )

    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is DoctorErrorCategory.FACTORY_FAILURE
    assert report.entries[0].error_category is DoctorErrorCategory.FACTORY_FAILURE
    assert report.entries[0].health is None
    _assert_marker_absent(report)


@pytest.mark.parametrize(
    ("failure_field", "error_category"),
    (
        ("capabilities_error", DoctorErrorCategory.CAPABILITIES_FAILURE),
        ("version_error", DoctorErrorCategory.VERSION_FAILURE),
    ),
)
def test_synchronous_declaration_cancellation_is_sanitized(
    failure_field: str,
    error_category: DoctorErrorCategory,
) -> None:
    adapter = _ProbeAdapter(
        **{
            failure_field: asyncio.CancelledError(
                f"declaration secret {SECRET_MARKER}"
            )
        }
    )
    report = _collect(
        RuntimeDoctor(
            (_spec(_factory(adapter)),),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )

    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is error_category
    assert report.entries[0].error_category is error_category
    _assert_marker_absent(report)


def test_clock_cancellation_is_sanitized_without_leaking_marker() -> None:
    def cancelling_clock():
        raise asyncio.CancelledError(f"clock secret {SECRET_MARKER}")

    report = _collect(
        RuntimeDoctor(
            (DEFAULT_DOCTOR_RUNTIME_SPECS[0],),
            clock=cancelling_clock,
        )
    )

    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is DoctorErrorCategory.TIMESTAMP_FAILURE
    assert report.entries[0].health is True
    _assert_marker_absent(report)


def test_inventory_materialization_cancellation_is_sanitized() -> None:
    class _CancellingInventory:
        def __iter__(self):
            raise asyncio.CancelledError(f"inventory secret {SECRET_MARKER}")

    report = _collect(
        RuntimeDoctor(
            _CancellingInventory(),  # type: ignore[arg-type]
            clock=lambda: FIXED_TIMESTAMP,
        )
    )

    assert report.status is DoctorReportStatus.FAILED
    assert report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert report.entries == ()
    _assert_marker_absent(report)


def test_profile_construction_cancellation_is_sanitized() -> None:
    base_spec = _spec(_factory(_ProbeAdapter()))

    class _CancellingProfileSpec(DoctorRuntimeSpec):
        def to_profile(self):  # type: ignore[no-untyped-def]
            raise asyncio.CancelledError(f"profile secret {SECRET_MARKER}")

    spec = _CancellingProfileSpec(
        provider_id=base_spec.provider_id,
        transport_kind=base_spec.transport_kind,
        runtime_id=base_spec.runtime_id,
        adapter_id=base_spec.adapter_id,
        runtime_profile_ref=base_spec.runtime_profile_ref,
        factory=base_spec.factory,
        maturity=base_spec.maturity,
        evidence=base_spec.evidence,
        execution_target=base_spec.execution_target,
        profile_revision=base_spec.profile_revision,
        auth_ownership=base_spec.auth_ownership,
        usage_visibility=base_spec.usage_visibility,
    )
    report = _collect(
        RuntimeDoctor((spec,), clock=lambda: FIXED_TIMESTAMP)
    )

    assert report.status is DoctorReportStatus.FAILED
    assert report.error_category is DoctorErrorCategory.INVENTORY_INVALID
    assert report.entries == ()
    _assert_marker_absent(report)


def test_timestamp_failure_is_sanitized_and_keeps_partial_probe_results() -> None:
    def broken_clock():
        raise RuntimeError(f"clock secret {SECRET_MARKER}")

    report = _collect(
        RuntimeDoctor(
            (DEFAULT_DOCTOR_RUNTIME_SPECS[0],),
            clock=broken_clock,
        )
    )
    assert report.status is DoctorReportStatus.PARTIAL
    assert report.error_category is DoctorErrorCategory.TIMESTAMP_FAILURE
    assert report.entries[0].health is True
    assert report.timestamp.tzinfo is not None
    _assert_marker_absent(report)


def test_doctor_only_calls_probe_and_declaration_surfaces() -> None:
    adapter = _ProbeAdapter()
    forbidden_calls: list[str] = []

    def forbidden(name: str):
        def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
            forbidden_calls.append(name)
            raise AssertionError(f"Doctor called lifecycle method {name}")

        return _raise

    for method_name in (
        "create_run",
        "submit",
        "status",
        "result",
        "cancel",
        "resume",
        "artifacts",
        "cleanup",
    ):
        setattr(adapter, method_name, forbidden(method_name))

    report = _collect(
        RuntimeDoctor(
            (_spec(_factory(adapter)),),
            clock=lambda: FIXED_TIMESTAMP,
        )
    )
    assert report.status is DoctorReportStatus.COMPLETE
    assert forbidden_calls == []


def test_custom_inventory_is_exposed_as_tuple_and_timestamp_is_utc() -> None:
    adapter = _ProbeAdapter()
    doctor = RuntimeDoctor(
        (_spec(_factory(adapter)),),
        clock=lambda: datetime(2026, 8, 27, 20, 34, 56, tzinfo=timezone.utc),
    )
    assert isinstance(doctor.specs, tuple)
    report = _collect(doctor)
    assert report.timestamp.utcoffset() == timezone.utc.utcoffset(report.timestamp)
    assert report.timestamp.hour == 20
