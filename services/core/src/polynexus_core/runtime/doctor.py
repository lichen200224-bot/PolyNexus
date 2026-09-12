"""Deterministic Core-only Runtime Doctor (WP-16).

The Doctor is a read-only composition root for runtime inventory reporting. It
owns a fixed, ordered inventory and a fresh in-memory ``RuntimeRegistry``;
the product's default registry and ``ExecutionService`` remain unchanged.

Only the non-lifecycle RuntimeAdapter surfaces are observed here:
``health()``, ``readiness()``, ``capabilities()``, and ``version_info()``.
Health and readiness are current asynchronous probes. Capabilities and
versions are adapter declarations. Conformance evidence is static metadata
kept separate from both kinds of observation.

This module deliberately has no API, UI, persistence, migration, network,
credential, supervisor, or vendor-branch behavior. It is not a production
runtime detector and never invokes a real vendor CLI.
"""
from __future__ import annotations

import asyncio
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from polynexus_core.persistence.database import schema_head_status
from polynexus_core.domain.enums import (
    AuthOwnership,
    ExecutionTarget,
    ResumeMode,
    TransportKind,
    UsageVisibility,
)
from polynexus_core.domain.runtime_binding import RuntimeProfile
from polynexus_core.runtime.codex import CodexRuntimeAdapter
from polynexus_core.runtime.contracts import RuntimeAdapter, RuntimeCapabilities
from polynexus_core.runtime.opencode import OpenCodeRuntimeAdapter
from polynexus_core.runtime.reference import ReferenceRuntimeAdapter
from polynexus_core.runtime.registry import AdapterFactory, RuntimeRegistry


DOCTOR_CONTRACT_VERSION = "runtime-adapter/v1"
DEFAULT_PROBE_TIMEOUT_SECONDS = 1.0

CURRENT_PROBE = "CURRENT_PROBE"
ADAPTER_DECLARATION = "ADAPTER_DECLARATION"
UNAVAILABLE = "UNAVAILABLE"


class DoctorReportStatus(StrEnum):
    """Whether the report itself was complete, partial, or failed."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class DoctorMaturity(StrEnum):
    """Truthful maturity labels available to the Doctor MVP."""

    SUPPORTED = "SUPPORTED"
    EXPERIMENTAL = "EXPERIMENTAL"


class DoctorErrorCategory(StrEnum):
    """Fixed, public-safe error categories; raw exception text is excluded."""

    INVENTORY_INVALID = "INVENTORY_INVALID"
    FACTORY_FAILURE = "FACTORY_FAILURE"
    HEALTH_FAILURE = "HEALTH_FAILURE"
    READINESS_FAILURE = "READINESS_FAILURE"
    CAPABILITIES_FAILURE = "CAPABILITIES_FAILURE"
    VERSION_FAILURE = "VERSION_FAILURE"
    PROBE_TIMEOUT = "PROBE_TIMEOUT"
    TIMESTAMP_FAILURE = "TIMESTAMP_FAILURE"


@dataclass(frozen=True)
class DoctorConformanceEvidence:
    """Static evidence for a runtime's declared conformance maturity.

    This is deliberately separate from current health/readiness observations
    and from the adapter's capability declaration.
    """

    source: str
    outcome: str
    scope: str
    checkpoint: str
    test_source: str


@dataclass(frozen=True)
class DoctorRuntimeSpec:
    """One immutable inventory row and its composition-root factory."""

    provider_id: str
    transport_kind: TransportKind
    runtime_id: str
    adapter_id: str
    runtime_profile_ref: str
    factory: AdapterFactory
    maturity: DoctorMaturity
    evidence: DoctorConformanceEvidence
    execution_target: ExecutionTarget = ExecutionTarget.LOCAL
    profile_revision: int = 1
    auth_ownership: AuthOwnership = AuthOwnership.NONE
    usage_visibility: UsageVisibility = UsageVisibility.UNAVAILABLE

    def to_profile(self) -> RuntimeProfile:
        """Create the in-memory profile used only by this Doctor registry."""

        return RuntimeProfile(
            provider_id=self.provider_id,
            transport_kind=self.transport_kind,
            runtime_id=self.runtime_id,
            adapter_id=self.adapter_id,
            execution_target=self.execution_target,
            runtime_profile_ref=self.runtime_profile_ref,
            profile_revision=self.profile_revision,
            auth_ownership=self.auth_ownership,
            secret_ref_id=None,
            usage_visibility=self.usage_visibility,
        )


@dataclass(frozen=True)
class DoctorRuntimeEntry:
    """A sanitized report row for one inventoried runtime."""

    provider_id: str
    transport_kind: TransportKind
    runtime_id: str
    adapter_id: str
    execution_target: ExecutionTarget
    runtime_profile_ref: str
    profile_revision: int
    health: bool | None
    health_source: str
    readiness: bool | None
    readiness_source: str
    runtime_version: str | None
    runtime_version_source: str
    adapter_version: str | None
    adapter_version_source: str
    capabilities: RuntimeCapabilities | None
    capabilities_source: str
    maturity: DoctorMaturity
    evidence_source: str
    conformance_evidence: DoctorConformanceEvidence
    error_category: DoctorErrorCategory | None


@dataclass(frozen=True)
class RuntimeDoctorReport:
    """Immutable Doctor output with no raw exception or traceback material."""

    contract_version: str
    status: DoctorReportStatus
    timestamp: datetime
    entries: tuple[DoctorRuntimeEntry, ...]
    error_category: DoctorErrorCategory | None

    @property
    def observed_at(self) -> datetime:
        """Compatibility alias for consumers that call the timestamp observed_at."""

        return self.timestamp


_REFERENCE_IDENTITY = (
    "polynexus",
    TransportKind.LOCAL,
    "reference",
    "builtin.reference",
    ExecutionTarget.LOCAL,
)
_CANONICAL_POLICIES_BY_PROFILE = {
    "reference.local": (
        _REFERENCE_IDENTITY,
        DoctorMaturity.SUPPORTED,
        "DETERMINISTIC_REFERENCE_RUNTIME",
        ReferenceRuntimeAdapter,
    ),
    "conformance.codex.local": (
        (
            "polynexus",
            TransportKind.LOCAL,
            "codex-conformance",
            "builtin.codex-conformance",
            ExecutionTarget.LOCAL,
        ),
        DoctorMaturity.EXPERIMENTAL,
        "DETERMINISTIC_LOCAL_CONFORMANCE",
        CodexRuntimeAdapter,
    ),
    "conformance.opencode.local": (
        (
            "polynexus",
            TransportKind.LOCAL,
            "opencode-conformance",
            "builtin.opencode-conformance",
            ExecutionTarget.LOCAL,
        ),
        DoctorMaturity.EXPERIMENTAL,
        "DETERMINISTIC_LOCAL_CONFORMANCE",
        OpenCodeRuntimeAdapter,
    ),
}
_CANONICAL_POLICIES_BY_IDENTITY = {
    identity: (profile_ref, maturity, scope, factory)
    for profile_ref, (identity, maturity, scope, factory) in _CANONICAL_POLICIES_BY_PROFILE.items()
}
_ALLOWED_EVIDENCE_OUTCOMES = frozenset({"PASS", "UNVERIFIED"})
_ALLOWED_EVIDENCE_SCOPES = frozenset(
    {
        "DETERMINISTIC_REFERENCE_RUNTIME",
        "DETERMINISTIC_LOCAL_CONFORMANCE",
        "TEST_ONLY",
    }
)
_PUBLIC_VERSION_MAX_LENGTH = 128
_PUBLIC_EVIDENCE_MAX_LENGTH = 256
_FORBIDDEN_PUBLIC_MARKERS = (
    "secret",
    "token",
    "cookie",
    "session",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "certified",
    "production",
    "supported",
    "preview",
)
_CREDENTIAL_PUBLIC_PREFIXES = (
    "sk-",
    "ghp_",
    "github_pat_",
    "xoxb-",
    "xoxp-",
    "aiza",
    "akia",
)
_ACCEPTED_INTEGRATION_CHECKPOINT = "65c6582c70c4e724005adb983d65aba10ea3e8be"
_CUSTOM_TEST_EVIDENCE = DoctorConformanceEvidence(
    source="TEST_EVIDENCE",
    outcome="UNVERIFIED",
    scope="TEST_ONLY",
    checkpoint="test-checkpoint",
    test_source="services/core/tests/test_wp16_runtime_doctor.py",
)
_CANONICAL_EVIDENCE_BY_PROFILE = {
    "reference.local": DoctorConformanceEvidence(
        source="DETERMINISTIC_REFERENCE_TESTS",
        outcome="PASS",
        scope="DETERMINISTIC_REFERENCE_RUNTIME",
        checkpoint=_ACCEPTED_INTEGRATION_CHECKPOINT,
        test_source="services/core/tests/test_runtime_skeleton.py",
    ),
    "conformance.codex.local": DoctorConformanceEvidence(
        source="INDEPENDENT_CONFORMANCE_REVIEW",
        outcome="PASS",
        scope="DETERMINISTIC_LOCAL_CONFORMANCE",
        checkpoint=_ACCEPTED_INTEGRATION_CHECKPOINT,
        test_source="services/core/tests/test_wp14_codex_runtime.py",
    ),
    "conformance.opencode.local": DoctorConformanceEvidence(
        source="INDEPENDENT_CONFORMANCE_REVIEW",
        outcome="PASS",
        scope="DETERMINISTIC_LOCAL_CONFORMANCE",
        checkpoint=_ACCEPTED_INTEGRATION_CHECKPOINT,
        test_source="services/core/tests/test_wp15_opencode_runtime.py",
    ),
}


def _truthful_maturity_and_evidence(
    spec: DoctorRuntimeSpec,
    maturity: DoctorMaturity,
) -> bool:
    """Reject support or certification claims outside their approved scope."""

    if (
        spec.evidence.outcome not in _ALLOWED_EVIDENCE_OUTCOMES
        or spec.evidence.scope not in _ALLOWED_EVIDENCE_SCOPES
    ):
        return False

    identity = (
        spec.provider_id,
        spec.transport_kind,
        spec.runtime_id,
        spec.adapter_id,
        spec.execution_target,
    )
    identity_policy = _CANONICAL_POLICIES_BY_IDENTITY.get(identity)
    if identity_policy is not None:
        expected_profile_ref, expected_maturity, expected_scope, expected_factory = identity_policy
        return (
            spec.runtime_profile_ref == expected_profile_ref
            and maturity is expected_maturity
            and spec.factory is expected_factory
            and spec.evidence == _CANONICAL_EVIDENCE_BY_PROFILE[expected_profile_ref]
            and spec.evidence.scope == expected_scope
        )

    profile_policy = _CANONICAL_POLICIES_BY_PROFILE.get(spec.runtime_profile_ref)
    if profile_policy is not None:
        expected_identity, expected_maturity, expected_scope, expected_factory = profile_policy
        return (
            identity == expected_identity
            and maturity is expected_maturity
            and spec.factory is expected_factory
            and spec.evidence == _CANONICAL_EVIDENCE_BY_PROFILE[spec.runtime_profile_ref]
            and spec.evidence.scope == expected_scope
        )

    # Custom inventories are a test seam only. Their explicit UNVERIFIED /
    # TEST_ONLY tuple can exercise probe and failure paths, but can never
    # publish a conformance PASS for an unrecognized runtime.
    return maturity is DoctorMaturity.EXPERIMENTAL and spec.evidence == _CUSTOM_TEST_EVIDENCE


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_metadata(value: object) -> bool:
    """Accept bounded static evidence without ever rendering it on failure."""

    try:
        if not isinstance(value, str) or not value or len(value) > 256:
            return False
        return all(
            ord(character) >= 0x20 and character != "\x7f"
            for character in value
        )
    except Exception:
        return False


def _safe_public_version(value: object) -> bool:
    """Accept only a bounded, public-looking adapter version declaration."""

    return _safe_public_token(value, max_length=_PUBLIC_VERSION_MAX_LENGTH)


def _safe_public_token(value: object, *, max_length: int) -> bool:
    """Accept bounded public metadata without credential-shaped material."""

    try:
        if (
            not isinstance(value, str)
            or len(value) > max_length
            or not _safe_metadata(value)
            or not value[0].isalnum()
        ):
            return False
        normalized = value.casefold()
        if any(marker in normalized for marker in _FORBIDDEN_PUBLIC_MARKERS):
            return False
        if normalized.startswith(_CREDENTIAL_PUBLIC_PREFIXES):
            return False
        return all(character.isalnum() or character in "._+:/-" for character in value)
    except Exception:
        return False


def _prepare_inventory(
    specs: tuple[DoctorRuntimeSpec, ...],
    unreadable: bool,
) -> tuple[tuple[DoctorRuntimeSpec, RuntimeProfile, DoctorMaturity], ...] | None:
    """Validate the complete inventory before registering any row."""

    if unreadable or not specs:
        return None

    seen_profile_refs: set[str] = set()
    seen_adapter_ids: set[str] = set()
    prepared: list[tuple[DoctorRuntimeSpec, RuntimeProfile, DoctorMaturity]] = []

    for spec in specs:
        if not isinstance(spec, DoctorRuntimeSpec):
            return None
        if not callable(spec.factory):
            return None
        if not isinstance(spec.runtime_profile_ref, str) or not spec.runtime_profile_ref or len(spec.runtime_profile_ref) > 256 or not _safe_metadata(spec.runtime_profile_ref):
            return None
        if not isinstance(spec.adapter_id, str) or not spec.adapter_id or len(spec.adapter_id) > 256 or not _safe_metadata(spec.adapter_id):
            return None
        try:
            if spec.runtime_profile_ref in seen_profile_refs:
                return None
            if spec.adapter_id in seen_adapter_ids:
                return None
        except Exception:
            return None
        if not isinstance(spec.transport_kind, TransportKind):
            return None
        if not isinstance(spec.execution_target, ExecutionTarget):
            return None
        if not isinstance(spec.auth_ownership, AuthOwnership):
            return None
        if not isinstance(spec.usage_visibility, UsageVisibility):
            return None
        if not isinstance(spec.profile_revision, int) or spec.profile_revision < 1:
            return None
        if not isinstance(spec.evidence, DoctorConformanceEvidence):
            return None
        if not all(
            _safe_public_token(value, max_length=_PUBLIC_EVIDENCE_MAX_LENGTH)
            for value in (
                spec.evidence.source,
                spec.evidence.outcome,
                spec.evidence.scope,
                spec.evidence.checkpoint,
                spec.evidence.test_source,
            )
        ):
            return None

        try:
            maturity = DoctorMaturity(spec.maturity)
            if not _truthful_maturity_and_evidence(spec, maturity):
                return None
            profile = spec.to_profile()
        except asyncio.CancelledError:
            return None
        except Exception:
            return None

        try:
            seen_profile_refs.add(spec.runtime_profile_ref)
            seen_adapter_ids.add(spec.adapter_id)
        except Exception:
            return None
        prepared.append((spec, profile, maturity))

    return tuple(prepared)


def _sanitize_capabilities(value: object) -> RuntimeCapabilities | None:
    """Rebuild only validated capability fields for the public report."""

    try:
        if type(value) is not RuntimeCapabilities:
            return None
        if not all(
            isinstance(field, bool)
            for field in (
                value.cancel,
                value.artifacts,
                value.timeout_cleanup_verified,
                value.external_sessions,
                value.event_stream,
                value.permission_requests,
                value.egress_declaration,
            )
        ):
            return None
        if not isinstance(value.resume, ResumeMode):
            return None
        if not isinstance(value.usage_visibility, UsageVisibility):
            return None
        if not isinstance(value.auth_ownership, AuthOwnership):
            return None
        return RuntimeCapabilities(
            cancel=value.cancel,
            resume=value.resume,
            artifacts=value.artifacts,
            timeout_cleanup_verified=value.timeout_cleanup_verified,
            usage_visibility=value.usage_visibility,
            auth_ownership=value.auth_ownership,
            external_sessions=value.external_sessions,
            event_stream=value.event_stream,
            permission_requests=value.permission_requests,
            egress_declaration=value.egress_declaration,
        )
    except Exception:
        return None


async def _probe_bool(
    adapter: RuntimeAdapter,
    method_name: str,
    failure_category: DoctorErrorCategory,
    timeout_seconds: float,
) -> tuple[bool | None, DoctorErrorCategory | None]:
    """Run one asynchronous boolean probe with cancellation-aware timeout."""

    try:
        method = getattr(adapter, method_name)
        operation = method()
        result = await asyncio.wait_for(operation, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return None, DoctorErrorCategory.PROBE_TIMEOUT
    except asyncio.CancelledError:
        raise
    except Exception:
        return None, failure_category

    if not isinstance(result, bool):
        return None, failure_category
    return result, None


DEFAULT_DOCTOR_RUNTIME_SPECS: tuple[DoctorRuntimeSpec, ...] = (
    DoctorRuntimeSpec(
        provider_id="polynexus",
        transport_kind=TransportKind.LOCAL,
        runtime_id="reference",
        adapter_id="builtin.reference",
        runtime_profile_ref="reference.local",
        factory=ReferenceRuntimeAdapter,
        maturity=DoctorMaturity.SUPPORTED,
        evidence=DoctorConformanceEvidence(
            source="DETERMINISTIC_REFERENCE_TESTS",
            outcome="PASS",
            scope="DETERMINISTIC_REFERENCE_RUNTIME",
            checkpoint=_ACCEPTED_INTEGRATION_CHECKPOINT,
            test_source="services/core/tests/test_runtime_skeleton.py",
        ),
    ),
    DoctorRuntimeSpec(
        provider_id="polynexus",
        transport_kind=TransportKind.LOCAL,
        runtime_id="codex-conformance",
        adapter_id="builtin.codex-conformance",
        runtime_profile_ref="conformance.codex.local",
        factory=CodexRuntimeAdapter,
        maturity=DoctorMaturity.EXPERIMENTAL,
        evidence=DoctorConformanceEvidence(
            source="INDEPENDENT_CONFORMANCE_REVIEW",
            outcome="PASS",
            scope="DETERMINISTIC_LOCAL_CONFORMANCE",
            checkpoint=_ACCEPTED_INTEGRATION_CHECKPOINT,
            test_source="services/core/tests/test_wp14_codex_runtime.py",
        ),
    ),
    DoctorRuntimeSpec(
        provider_id="polynexus",
        transport_kind=TransportKind.LOCAL,
        runtime_id="opencode-conformance",
        adapter_id="builtin.opencode-conformance",
        runtime_profile_ref="conformance.opencode.local",
        factory=OpenCodeRuntimeAdapter,
        maturity=DoctorMaturity.EXPERIMENTAL,
        evidence=DoctorConformanceEvidence(
            source="INDEPENDENT_CONFORMANCE_REVIEW",
            outcome="PASS",
            scope="DETERMINISTIC_LOCAL_CONFORMANCE",
            checkpoint=_ACCEPTED_INTEGRATION_CHECKPOINT,
            test_source="services/core/tests/test_wp15_opencode_runtime.py",
        ),
    ),
)


class RuntimeDoctor:
    """Collect a deterministic report from a private Doctor registry."""

    def __init__(
        self,
        specs: Sequence[DoctorRuntimeSpec] = DEFAULT_DOCTOR_RUNTIME_SPECS,
        *,
        clock: Callable[[], datetime] = _utc_now,
        probe_timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
    ) -> None:
        try:
            self._specs = tuple(specs)
            self._inventory_unreadable = False
        except asyncio.CancelledError:
            self._specs = ()
            self._inventory_unreadable = True
        except Exception:
            self._specs = ()
            self._inventory_unreadable = True
        if not isinstance(probe_timeout, (int, float)) or isinstance(probe_timeout, bool):
            raise ValueError("probe_timeout must be a finite positive number")
        if not math.isfinite(float(probe_timeout)) or probe_timeout <= 0:
            raise ValueError("probe_timeout must be a finite positive number")
        self._clock = clock
        self._probe_timeout = float(probe_timeout)

    @property
    def specs(self) -> tuple[DoctorRuntimeSpec, ...]:
        """Return the immutable ordered inventory owned by this Doctor."""

        return self._specs

    async def collect(self) -> RuntimeDoctorReport:
        """Collect one report without exposing raw failures to the caller."""

        timestamp, timestamp_error = self._timestamp()
        inventory = _prepare_inventory(self._specs, self._inventory_unreadable)
        if inventory is None:
            return RuntimeDoctorReport(
                contract_version=DOCTOR_CONTRACT_VERSION,
                status=DoctorReportStatus.FAILED,
                timestamp=timestamp,
                entries=(),
                error_category=DoctorErrorCategory.INVENTORY_INVALID,
            )

        registry = RuntimeRegistry()
        for spec, profile, _ in inventory:
            try:
                registry.register(profile, spec.factory)
            except asyncio.CancelledError:
                return RuntimeDoctorReport(
                    contract_version=DOCTOR_CONTRACT_VERSION,
                    status=DoctorReportStatus.FAILED,
                    timestamp=timestamp,
                    entries=(),
                    error_category=DoctorErrorCategory.INVENTORY_INVALID,
                )
            except Exception:
                return RuntimeDoctorReport(
                    contract_version=DOCTOR_CONTRACT_VERSION,
                    status=DoctorReportStatus.FAILED,
                    timestamp=timestamp,
                    entries=(),
                    error_category=DoctorErrorCategory.INVENTORY_INVALID,
                )

        collected_entries: list[DoctorRuntimeEntry] = []
        for spec, profile, maturity in inventory:
            collected_entries.append(
                await self._collect_entry(registry, spec, profile, maturity)
            )
        entries = tuple(collected_entries)
        report_error = timestamp_error
        if report_error is None:
            report_error = next(
                (entry.error_category for entry in entries if entry.error_category is not None),
                None,
            )
        status = (
            DoctorReportStatus.PARTIAL
            if report_error is not None
            else DoctorReportStatus.COMPLETE
        )
        return RuntimeDoctorReport(
            contract_version=DOCTOR_CONTRACT_VERSION,
            status=status,
            timestamp=timestamp,
            entries=entries,
            error_category=report_error,
        )

    def _timestamp(self) -> tuple[datetime, DoctorErrorCategory | None]:
        try:
            value = self._clock()
            if not isinstance(value, datetime) or value.tzinfo is None:
                raise ValueError
            return value.astimezone(timezone.utc), None
        except asyncio.CancelledError:
            return _utc_now(), DoctorErrorCategory.TIMESTAMP_FAILURE
        except Exception:
            return _utc_now(), DoctorErrorCategory.TIMESTAMP_FAILURE

    async def _collect_entry(
        self,
        registry: RuntimeRegistry,
        spec: DoctorRuntimeSpec,
        profile: RuntimeProfile,
        maturity: DoctorMaturity,
    ) -> DoctorRuntimeEntry:
        adapter: RuntimeAdapter | None = None
        try:
            adapter = registry._create_adapter_for_observation(profile)
        except asyncio.CancelledError:
            return DoctorRuntimeEntry(
                provider_id=spec.provider_id,
                transport_kind=spec.transport_kind,
                runtime_id=spec.runtime_id,
                adapter_id=spec.adapter_id,
                execution_target=spec.execution_target,
                runtime_profile_ref=spec.runtime_profile_ref,
                profile_revision=spec.profile_revision,
                health=None,
                health_source=UNAVAILABLE,
                readiness=None,
                readiness_source=UNAVAILABLE,
                runtime_version=None,
                runtime_version_source=UNAVAILABLE,
                adapter_version=None,
                adapter_version_source=UNAVAILABLE,
                capabilities=None,
                capabilities_source=UNAVAILABLE,
                maturity=maturity,
                evidence_source=spec.evidence.source,
                conformance_evidence=spec.evidence,
                error_category=DoctorErrorCategory.FACTORY_FAILURE,
            )
        except Exception:
            return DoctorRuntimeEntry(
                provider_id=spec.provider_id,
                transport_kind=spec.transport_kind,
                runtime_id=spec.runtime_id,
                adapter_id=spec.adapter_id,
                execution_target=spec.execution_target,
                runtime_profile_ref=spec.runtime_profile_ref,
                profile_revision=spec.profile_revision,
                health=None,
                health_source=UNAVAILABLE,
                readiness=None,
                readiness_source=UNAVAILABLE,
                runtime_version=None,
                runtime_version_source=UNAVAILABLE,
                adapter_version=None,
                adapter_version_source=UNAVAILABLE,
                capabilities=None,
                capabilities_source=UNAVAILABLE,
                maturity=maturity,
                evidence_source=spec.evidence.source,
                conformance_evidence=spec.evidence,
                error_category=DoctorErrorCategory.FACTORY_FAILURE,
            )

        health, health_error = await _probe_bool(
            adapter,
            "health",
            DoctorErrorCategory.HEALTH_FAILURE,
            self._probe_timeout,
        )
        readiness, readiness_error = await _probe_bool(
            adapter,
            "readiness",
            DoctorErrorCategory.READINESS_FAILURE,
            self._probe_timeout,
        )

        capabilities: RuntimeCapabilities | None = None
        try:
            value = getattr(adapter, "capabilities")()
            capabilities = _sanitize_capabilities(value)
            if capabilities is None:
                raise TypeError
        except asyncio.CancelledError:
            capabilities_error = DoctorErrorCategory.CAPABILITIES_FAILURE
        except Exception:
            capabilities_error = DoctorErrorCategory.CAPABILITIES_FAILURE
        else:
            capabilities_error = None

        adapter_version: str | None = None
        try:
            value = getattr(adapter, "version_info")()
            if _safe_public_version(value):
                adapter_version = value
            else:
                raise TypeError
        except asyncio.CancelledError:
            version_error = DoctorErrorCategory.VERSION_FAILURE
        except Exception:
            version_error = DoctorErrorCategory.VERSION_FAILURE
        else:
            version_error = None

        error_category = next(
            (
                category
                for category in (
                    health_error,
                    readiness_error,
                    capabilities_error,
                    version_error,
                )
                if category is not None
            ),
            None,
        )
        return self._entry(
            spec,
            maturity,
            health=health,
            readiness=readiness,
            capabilities=capabilities,
            adapter_version=adapter_version,
            error_category=error_category,
        )

    @staticmethod
    def _entry(
        spec: DoctorRuntimeSpec,
        maturity: DoctorMaturity,
        *,
        health: bool | None,
        readiness: bool | None,
        capabilities: RuntimeCapabilities | None,
        adapter_version: str | None,
        error_category: DoctorErrorCategory | None,
    ) -> DoctorRuntimeEntry:
        return DoctorRuntimeEntry(
            provider_id=spec.provider_id,
            transport_kind=spec.transport_kind,
            runtime_id=spec.runtime_id,
            adapter_id=spec.adapter_id,
            execution_target=spec.execution_target,
            runtime_profile_ref=spec.runtime_profile_ref,
            profile_revision=spec.profile_revision,
            health=health,
            health_source=CURRENT_PROBE,
            readiness=readiness,
            readiness_source=CURRENT_PROBE,
            runtime_version=None,
            runtime_version_source=UNAVAILABLE,
            adapter_version=adapter_version,
            adapter_version_source=ADAPTER_DECLARATION,
            capabilities=capabilities,
            capabilities_source=ADAPTER_DECLARATION,
            maturity=maturity,
            evidence_source=spec.evidence.source,
            conformance_evidence=spec.evidence,
            error_category=error_category,
        )


def build_default_doctor(
    *,
    clock: Callable[[], datetime] = _utc_now,
    probe_timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
) -> RuntimeDoctor:
    """Build the dedicated Doctor composition root."""

    return RuntimeDoctor(
        DEFAULT_DOCTOR_RUNTIME_SPECS,
        clock=clock,
        probe_timeout=probe_timeout,
    )


# G18 compatibility boundary.  The older source-bound freshness report remains
# available to existing Core consumers while WP-16 exposes RuntimeDoctor's
# separate inventory report.  The wrapper forwards the current module's safe
# schema probe so tests and callers can replace that probe without reaching
# through this module boundary.
from polynexus_core.runtime import doctor_legacy as _doctor_legacy

DoctorClaim = _doctor_legacy.DoctorClaim
DoctorReport = _doctor_legacy.DoctorReport
EvidenceFreshness = _doctor_legacy.EvidenceFreshness
EvidenceProvenance = _doctor_legacy.EvidenceProvenance
MaturityState = _doctor_legacy.MaturityState
MAX_CLAIMS = _doctor_legacy.MAX_CLAIMS
DOCTOR_COMMAND = _doctor_legacy.DOCTOR_COMMAND
SCHEMA_COMMAND = _doctor_legacy.SCHEMA_COMMAND


async def collect_doctor_report(*args, **kwargs):  # type: ignore[no-untyped-def]
    _doctor_legacy.schema_head_status = schema_head_status
    return await _doctor_legacy.collect_doctor_report(*args, **kwargs)


__all__ = [
    "ADAPTER_DECLARATION",
    "CURRENT_PROBE",
    "DEFAULT_DOCTOR_RUNTIME_SPECS",
    "DEFAULT_PROBE_TIMEOUT_SECONDS",
    "DOCTOR_CONTRACT_VERSION",
    "DoctorConformanceEvidence",
    "DoctorClaim",
    "DoctorErrorCategory",
    "DoctorMaturity",
    "DoctorReport",
    "DoctorReportStatus",
    "DoctorRuntimeEntry",
    "DoctorRuntimeSpec",
    "EvidenceFreshness",
    "EvidenceProvenance",
    "MaturityState",
    "RuntimeDoctor",
    "RuntimeDoctorReport",
    "UNAVAILABLE",
    "build_default_doctor",
    "collect_doctor_report",
]
