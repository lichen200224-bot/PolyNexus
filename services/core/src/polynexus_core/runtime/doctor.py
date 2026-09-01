"""Bounded, source-bound runtime Doctor evidence (G18).

Doctor is an internal diagnostic boundary in V1.  It does not create a
public API, persist evidence, or infer maturity from historical documents.
Every claim carries a safe provenance record containing the exact source
commit, UTC timestamp, command label, exit code, and freshness state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any, Mapping

from polynexus_core.persistence.database import schema_head_status
from polynexus_core.runtime.registry import RuntimeRegistry

MAX_CLAIMS = 32
MAX_NAME_LENGTH = 64
MAX_VALUE_LENGTH = 128
MAX_SOURCE_LENGTH = 64
MAX_COMMAND_LENGTH = 64
DEFAULT_FRESHNESS_WINDOW = timedelta(minutes=15)
DOCTOR_COMMAND = "runtime-doctor"
SCHEMA_COMMAND = "alembic-schema-head"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SAFE_LABEL_PATTERN = re.compile(r"^[a-z][a-z0-9._/-]{0,63}$")
SAFE_VALUE_PATTERN = re.compile(r"^[A-Za-z0-9_.:/-]{1,128}$")


class EvidenceFreshness(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    HISTORICAL = "HISTORICAL"
    UNVERIFIED = "UNVERIFIED"
    NOT_PRESENT = "NOT_PRESENT"


class MaturityState(StrEnum):
    CERTIFIED = "CERTIFIED"
    SUPPORTED = "SUPPORTED"
    PREVIEW = "PREVIEW"
    EXPERIMENTAL = "EXPERIMENTAL"
    DETECTED = "DETECTED"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNVERIFIED = "UNVERIFIED"
    NOT_PRESENT = "NOT_PRESENT"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def _safe_label(value: object, *, maximum: int) -> str | None:
    if not isinstance(value, str) or not value or len(value) > maximum:
        return None
    if (
        SAFE_LABEL_PATTERN.fullmatch(value) is None
        or value.startswith("/")
        or "//" in value
        or ".." in value
    ):
        return None
    return value


def _safe_commit(value: object) -> str | None:
    if not isinstance(value, str) or COMMIT_PATTERN.fullmatch(value) is None:
        return None
    return value


def _safe_value(value: object) -> bool | int | str | None:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and 0 <= value <= 255:
        return value
    if isinstance(value, str) and 0 < len(value) <= MAX_VALUE_LENGTH:
        # Values are deliberately restricted to opaque/version-like labels.
        # This excludes paths, URLs, key/value payloads, and free-form errors.
        lowered = value.lower()
        forbidden_markers = (
            "authorization",
            "bearer",
            "cookie",
            "password",
            "secret",
            "token",
        )
        if (
            SAFE_VALUE_PATTERN.fullmatch(value) is not None
            and not value.startswith(("/", "\\"))
            and "://" not in value
            and "=" not in value
            and not any(marker in lowered for marker in forbidden_markers)
        ):
            return value
    return None


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    """Safe, bounded provenance attached to every Doctor claim."""
    source: str
    exact_commit: str | None
    generated_at: datetime
    command: str
    exit_code: int | None
    freshness: EvidenceFreshness

    def __post_init__(self) -> None:
        safe_source = _safe_label(self.source, maximum=MAX_SOURCE_LENGTH)
        safe_command = _safe_label(self.command, maximum=MAX_COMMAND_LENGTH)
        if safe_source is None or safe_command is None:
            raise ValueError("unsafe evidence provenance label")
        if self.exit_code is not None and (
            not isinstance(self.exit_code, int)
            or isinstance(self.exit_code, bool)
            or not 0 <= self.exit_code <= 255
        ):
            raise ValueError("invalid evidence exit code")
        if not isinstance(self.freshness, EvidenceFreshness):
            raise ValueError("invalid evidence freshness")
        object.__setattr__(self, "source", safe_source)
        object.__setattr__(self, "exact_commit", _safe_commit(self.exact_commit))
        object.__setattr__(self, "generated_at", _utc(self.generated_at))
        object.__setattr__(self, "command", safe_command)

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "exact_commit": self.exact_commit,
            "generated_at": self.generated_at.isoformat().replace("+00:00", "Z"),
            "command": self.command,
            "exit_code": self.exit_code,
            "freshness": self.freshness.value,
        }


@dataclass(frozen=True)
class DoctorClaim:
    name: str
    value: bool | int | str | None
    maturity: MaturityState
    evidence: EvidenceProvenance

    def __post_init__(self) -> None:
        if _safe_label(self.name, maximum=MAX_NAME_LENGTH) is None:
            raise ValueError("unsafe Doctor claim name")
        if not isinstance(self.maturity, MaturityState):
            raise ValueError("invalid Doctor claim maturity")
        safe = _safe_value(self.value)
        if safe != self.value:
            raise ValueError("unsafe Doctor claim value")
        if self.maturity in {MaturityState.CERTIFIED, MaturityState.SUPPORTED}:
            raise ValueError("Doctor cannot self-assert certified maturity")

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "maturity": self.maturity.value,
            "evidence": self.evidence.as_dict(),
        }


@dataclass(frozen=True)
class DoctorReport:
    generated_at: datetime
    freshness: EvidenceFreshness
    maturity: MaturityState
    claims: tuple[DoctorClaim, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _utc(self.generated_at))
        if len(self.claims) > MAX_CLAIMS:
            raise ValueError("Doctor report exceeds bounded claim count")
        if not isinstance(self.freshness, EvidenceFreshness):
            raise ValueError("invalid Doctor report freshness")
        if not isinstance(self.maturity, MaturityState):
            raise ValueError("invalid Doctor report maturity")
        if self.maturity in {MaturityState.CERTIFIED, MaturityState.SUPPORTED}:
            raise ValueError("Doctor cannot self-assert certified maturity")

    def as_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat().replace("+00:00", "Z"),
            "freshness": self.freshness.value,
            "maturity": self.maturity.value,
            "claims": [claim.as_dict() for claim in self.claims],
        }


def _classify_freshness(
    *,
    exact_commit: str | None,
    generated_at: datetime,
    now: datetime,
    exit_code: int | None,
    historical: bool,
    current_commit: str | None,
    freshness_window: timedelta,
) -> EvidenceFreshness:
    if _safe_commit(exact_commit) is None or exit_code is None or exit_code != 0:
        return EvidenceFreshness.UNVERIFIED
    if historical:
        return EvidenceFreshness.HISTORICAL
    if current_commit is not None:
        safe_current_commit = _safe_commit(current_commit)
        if safe_current_commit is None:
            return EvidenceFreshness.UNVERIFIED
        if exact_commit != safe_current_commit:
            return EvidenceFreshness.HISTORICAL
    age = _utc(now) - _utc(generated_at)
    if age < timedelta(0) or age > freshness_window:
        return EvidenceFreshness.STALE
    return EvidenceFreshness.CURRENT


def _claim_maturity(
    freshness: EvidenceFreshness,
    *,
    observed: bool,
    compatible: bool = True,
) -> MaturityState:
    if freshness is EvidenceFreshness.NOT_PRESENT:
        return MaturityState.NOT_PRESENT
    if freshness is not EvidenceFreshness.CURRENT:
        return MaturityState.UNVERIFIED
    if not observed:
        return MaturityState.UNVERIFIED
    if not compatible:
        return MaturityState.INCOMPATIBLE
    return MaturityState.PREVIEW


def _base_provenance(
    *,
    source: str,
    exact_commit: str | None,
    generated_at: datetime,
    command: str,
    exit_code: int | None,
    freshness: EvidenceFreshness,
) -> EvidenceProvenance:
    safe_commit = _safe_commit(exact_commit)
    safe_command = _safe_label(command, maximum=MAX_COMMAND_LENGTH) or DOCTOR_COMMAND
    safe_exit = (
        exit_code
        if isinstance(exit_code, int)
        and not isinstance(exit_code, bool)
        and 0 <= exit_code <= 255
        else None
    )
    return EvidenceProvenance(
        source=source,
        exact_commit=safe_commit,
        generated_at=generated_at,
        command=safe_command,
        exit_code=safe_exit,
        freshness=freshness,
    )


async def collect_doctor_report(
    registry: RuntimeRegistry,
    *,
    exact_commit: str | None,
    generated_at: datetime | None = None,
    now: datetime | None = None,
    current_commit: str | None = None,
    historical: bool = False,
    exit_code: int | None = 0,
    freshness_window: timedelta = DEFAULT_FRESHNESS_WINDOW,
    explicit_request: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> DoctorReport:
    """Collect a bounded Doctor report without persisting or exporting secrets.

    Missing/invalid provenance or a failed probe is represented as
    ``UNVERIFIED``.  The function never includes exception text or caller
    supplied identifiers in the report.
    """
    observed_at = _utc(generated_at or datetime.now(timezone.utc))
    observed_now = _utc(now or datetime.now(timezone.utc))
    freshness = _classify_freshness(
        exact_commit=exact_commit,
        generated_at=observed_at,
        now=observed_now,
        exit_code=exit_code,
        historical=historical,
        current_commit=current_commit,
        freshness_window=freshness_window,
    )
    claims: list[DoctorClaim] = []
    profile = None
    adapter = None
    compatible = False
    health_checks_passed = False
    try:
        profile, adapter = registry.inspect_selected_profile(
            explicit_request=explicit_request,
            environment=environment,
        )
        compatible = True
    except Exception:
        # The public report intentionally contains no exception or input data.
        claims.append(
            DoctorClaim(
                name="runtime_profile",
                value=None,
                maturity=(
                    MaturityState.INCOMPATIBLE
                    if freshness is EvidenceFreshness.CURRENT
                    else MaturityState.UNVERIFIED
                ),
                evidence=_base_provenance(
                    source="runtime.registry",
                    exact_commit=exact_commit,
                    generated_at=observed_at,
                    command=DOCTOR_COMMAND,
                    exit_code=1,
                    freshness=EvidenceFreshness.UNVERIFIED,
                ),
            )
        )

    if profile is not None and adapter is not None:
        health_checks_passed = True
        profile_values = {
            "provider": profile.provider_id,
            "transport": profile.transport_kind.value,
            "runtime": profile.runtime_id,
            "adapter": profile.adapter_id,
            "execution_target": profile.execution_target.value,
            "profile_ref": profile.runtime_profile_ref,
            "profile_revision": profile.profile_revision,
            "auth_ownership": profile.auth_ownership.value,
            "usage_visibility": profile.usage_visibility.value,
        }
        for name, value in profile_values.items():
            claims.append(
                DoctorClaim(
                    name=name,
                    value=_safe_value(value),
                    maturity=_claim_maturity(freshness, observed=True, compatible=compatible),
                    evidence=_base_provenance(
                        source="runtime.registry",
                        exact_commit=exact_commit,
                        generated_at=observed_at,
                        command=DOCTOR_COMMAND,
                        exit_code=exit_code,
                        freshness=freshness,
                    ),
                )
            )
        try:
            capabilities = adapter.capabilities()
            capability_values: dict[str, Any] = {
                "cancel": capabilities.cancel,
                "resume": capabilities.resume.value,
                "artifacts": capabilities.artifacts,
                "timeout_cleanup_verified": capabilities.timeout_cleanup_verified,
                "usage_visibility": capabilities.usage_visibility.value,
                "auth_ownership": capabilities.auth_ownership.value,
            }
            for name, value in capability_values.items():
                claims.append(
                    DoctorClaim(
                        name=f"capability.{name}",
                        value=_safe_value(value),
                        maturity=_claim_maturity(freshness, observed=True, compatible=True),
                        evidence=_base_provenance(
                            source="runtime.adapter",
                            exact_commit=exact_commit,
                            generated_at=observed_at,
                            command=DOCTOR_COMMAND,
                            exit_code=exit_code,
                            freshness=freshness,
                        ),
                    )
                )
        except Exception:
            for name in (
                "capability.cancel",
                "capability.resume",
                "capability.artifacts",
                "capability.timeout_cleanup_verified",
                "capability.usage_visibility",
                "capability.auth_ownership",
            ):
                claims.append(
                    DoctorClaim(
                        name=name,
                        value=None,
                        maturity=MaturityState.UNVERIFIED,
                        evidence=_base_provenance(
                            source="runtime.adapter",
                            exact_commit=exact_commit,
                            generated_at=observed_at,
                            command=DOCTOR_COMMAND,
                            exit_code=1,
                            freshness=EvidenceFreshness.UNVERIFIED,
                        ),
                    )
                )
        try:
            version = adapter.version_info()
            safe_version = _safe_value(version)
            claims.append(
                DoctorClaim(
                    name="adapter_version",
                    value=safe_version,
                    maturity=_claim_maturity(
                        freshness,
                        observed=safe_version is not None,
                        compatible=True,
                    ),
                    evidence=_base_provenance(
                        source="runtime.adapter",
                        exact_commit=exact_commit,
                        generated_at=observed_at,
                        command=DOCTOR_COMMAND,
                        exit_code=exit_code,
                        freshness=freshness,
                    ),
                )
            )
        except Exception:
            claims.append(
                DoctorClaim(
                    name="adapter_version",
                    value=None,
                    maturity=MaturityState.UNVERIFIED,
                    evidence=_base_provenance(
                        source="runtime.adapter",
                        exact_commit=exact_commit,
                        generated_at=observed_at,
                        command=DOCTOR_COMMAND,
                        exit_code=1,
                        freshness=EvidenceFreshness.UNVERIFIED,
                    ),
                )
            )
        try:
            route_probe = getattr(adapter, "route_evidence", None)
            if not callable(route_probe):
                route_probe = None
            if route_probe is None:
                raise LookupError
            route_evidence = route_probe()
            timeout_seconds = float(route_evidence.timeout_seconds)
            timeout_value: int | str | None = (
                int(timeout_seconds)
                if timeout_seconds.is_integer()
                else format(timeout_seconds, ".3f").rstrip("0").rstrip(".")
            )
            route_values = {
                "route.endpoint": route_evidence.endpoint_identity,
                "route.model": route_evidence.model_identity,
                "route.policy": route_evidence.route,
                "route.timeout_seconds": timeout_value,
                "route.safe_error": route_evidence.safe_error or None,
            }
            for name, value in route_values.items():
                claims.append(
                    DoctorClaim(
                        name=name,
                        value=_safe_value(value),
                        maturity=_claim_maturity(
                            freshness,
                            observed=True,
                            compatible=True,
                        ),
                        evidence=_base_provenance(
                            source="runtime.routing",
                            exact_commit=exact_commit,
                            generated_at=observed_at,
                            command=DOCTOR_COMMAND,
                            exit_code=exit_code,
                            freshness=freshness,
                        ),
                    )
                )
        except LookupError:
            pass
        except Exception:
            claims.append(
                DoctorClaim(
                    name="route.policy",
                    value=None,
                    maturity=MaturityState.UNVERIFIED,
                    evidence=_base_provenance(
                        source="runtime.routing",
                        exact_commit=exact_commit,
                        generated_at=observed_at,
                        command=DOCTOR_COMMAND,
                        exit_code=1,
                        freshness=EvidenceFreshness.UNVERIFIED,
                    ),
                )
            )
        for name, probe in (("health", adapter.health), ("readiness", adapter.readiness)):
            try:
                value = await probe()
                if value is not True:
                    health_checks_passed = False
                claims.append(
                    DoctorClaim(
                        name=name,
                        value=value is True,
                        maturity=_claim_maturity(
                            freshness,
                            observed=True,
                            compatible=value is True,
                        ),
                        evidence=_base_provenance(
                            source="runtime.adapter",
                            exact_commit=exact_commit,
                            generated_at=observed_at,
                            command=DOCTOR_COMMAND,
                            exit_code=exit_code,
                            freshness=freshness,
                        ),
                    )
                )
            except Exception:
                health_checks_passed = False
                claims.append(
                    DoctorClaim(
                        name=name,
                        value=None,
                        maturity=MaturityState.UNVERIFIED,
                        evidence=_base_provenance(
                            source="runtime.adapter",
                            exact_commit=exact_commit,
                            generated_at=observed_at,
                            command=DOCTOR_COMMAND,
                            exit_code=1,
                            freshness=EvidenceFreshness.UNVERIFIED,
                        ),
                    )
                )

    schema_ok = schema_head_status()
    claims.append(
        DoctorClaim(
            name="schema_head",
            value=schema_ok,
            maturity=_claim_maturity(
                freshness,
                observed=True,
                compatible=schema_ok,
            ),
            evidence=_base_provenance(
                source="persistence.schema",
                exact_commit=exact_commit,
                generated_at=observed_at,
                command=SCHEMA_COMMAND,
                exit_code=exit_code if schema_ok else 1,
                freshness=(freshness if schema_ok else EvidenceFreshness.UNVERIFIED),
            ),
        )
    )

    claims = claims[:MAX_CLAIMS]
    if not claims:
        report_freshness = EvidenceFreshness.NOT_PRESENT
    elif any(claim.evidence.freshness is not EvidenceFreshness.CURRENT for claim in claims):
        report_freshness = EvidenceFreshness.UNVERIFIED
    else:
        report_freshness = EvidenceFreshness.CURRENT
    if report_freshness is not EvidenceFreshness.CURRENT:
        report_maturity = MaturityState.UNVERIFIED
    elif not compatible:
        report_maturity = MaturityState.INCOMPATIBLE
    elif (
        not schema_ok
        or not health_checks_passed
        or any(claim.maturity is MaturityState.UNVERIFIED for claim in claims)
    ):
        report_maturity = MaturityState.UNVERIFIED
    else:
        # Current evidence is sufficient for PREVIEW only.  Certification is
        # owned by the independent conformance/acceptance gate, not Doctor.
        report_maturity = MaturityState.PREVIEW
    return DoctorReport(
        generated_at=observed_at,
        freshness=report_freshness,
        maturity=report_maturity,
        claims=tuple(claims),
    )
