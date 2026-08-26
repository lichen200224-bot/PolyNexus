"""Run-owned immutable Runtime Binding contracts (ADR-011 / PRE-WP14-B).

Boundary:
  - ``RuntimeProfile`` is a mutable resolution intention. It lives only in
    memory / the Runtime Registry — no table, no CRUD, no public API.
  - ``RuntimeBindingSnapshot`` is the immutable, Run-owned resolved execution
    fact persisted before real execution.

Invariants:
  - ``Task != Run``: exactly one snapshot per Run; Tasks never own bindings.
  - A persisted snapshot can never be updated or rebound (repository and ORM
    level both reject mutation).
  - No raw credential value is ever stored: ``secret_ref_id`` is an opaque
    reference only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

from polynexus_core.domain.enums import (
    AuthOwnership,
    ExecutionTarget,
    TransportKind,
    UsageVisibility,
)

# Opaque identifier grammar (ADR-011 §2): lower-case ASCII segments separated
# by single dots, underscores or hyphens. Format-validated, never vendor-enumerated.
OPAQUE_IDENTIFIER_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")
OPAQUE_IDENTIFIER_MAX_LENGTH = 64

# Snapshot schema evolution gate: unknown versions fail closed on reload.
SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS = frozenset({1})
DEFAULT_SNAPSHOT_SCHEMA_VERSION = 1


class RuntimeBindingError(Exception):
    """Raised for any runtime-binding contract violation (fail closed).

    Messages are fixed public-safe constants: they NEVER echo the rejected
    input value, because identifiers and references may contain sensitive
    material. Callers needing the rejected value already hold it.
    """


def validate_opaque_identifier(value: object, field_name: str) -> str:
    """Validate an opaque identifier against the ADR-011 grammar.

    The grammar itself already rejects uppercase, spaces, leading/trailing
    separators, repeated separators, credential-style values such as
    ``"Bearer abc"`` or cookie/session strings, and anything longer than the
    bounded maximum length. Rejection messages never include ``value``.
    """
    if not isinstance(value, str):
        raise RuntimeBindingError(f"{field_name} must be a string")
    if len(value) > OPAQUE_IDENTIFIER_MAX_LENGTH:
        raise RuntimeBindingError(
            f"{field_name} exceeds the maximum identifier length"
        )
    if not OPAQUE_IDENTIFIER_PATTERN.match(value):
        raise RuntimeBindingError(
            f"{field_name} is not a valid opaque identifier"
        )
    return value


def _validate_optional_identifier(value: str | None, field_name: str) -> None:
    if value is None:
        return
    validate_opaque_identifier(value, field_name)


@dataclass(frozen=True)
class RuntimeBindingSnapshot:
    """Immutable, Run-owned resolved execution fact (ADR-011 §4).

    Persisted before real adapter execution; 1:1 with the existing Run;
    never updated after persistence; never rebound on repeated commands.
    """

    run_id: str
    provider_id: str
    transport_kind: TransportKind
    runtime_id: str
    adapter_id: str
    execution_target: ExecutionTarget
    runtime_profile_ref: str | None
    profile_revision: int | None
    adapter_version: str | None
    resolved_at: datetime
    legacy_backfill: bool = False
    snapshot_schema_version: int = DEFAULT_SNAPSHOT_SCHEMA_VERSION
    auth_ownership: AuthOwnership = AuthOwnership.NONE
    secret_ref_id: str | None = None
    usage_visibility: UsageVisibility = UsageVisibility.UNAVAILABLE

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id:
            raise RuntimeBindingError("snapshot run_id must be a non-empty Run identity")

        validate_opaque_identifier(self.provider_id, "provider_id")
        validate_opaque_identifier(self.runtime_id, "runtime_id")
        validate_opaque_identifier(self.adapter_id, "adapter_id")
        _validate_optional_identifier(self.runtime_profile_ref, "runtime_profile_ref")

        # secret_ref_id is an opaque reference only — the identifier grammar
        # rejects tokens, cookies, sessions and any credential-shaped value.
        _validate_optional_identifier(self.secret_ref_id, "secret_ref_id")

        if self.snapshot_schema_version not in SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS:
            raise RuntimeBindingError(
                "Unsupported snapshot_schema_version "
                f"(supported: {sorted(SUPPORTED_SNAPSHOT_SCHEMA_VERSIONS)})"
            )

        if self.profile_revision is not None and self.profile_revision < 1:
            raise RuntimeBindingError("profile_revision must be >= 1 when present")

        # Auth ownership / secret reference invariant (ADR-011 §6):
        # only SECRET_REF may carry an opaque secret_ref_id; every other
        # ownership must carry none.
        if self.auth_ownership is AuthOwnership.SECRET_REF:
            if not self.secret_ref_id:
                raise RuntimeBindingError(
                    "SECRET_REF auth ownership requires an opaque secret_ref_id"
                )
            _validate_optional_identifier(self.secret_ref_id, "secret_ref_id")
        elif self.secret_ref_id is not None:
            raise RuntimeBindingError(
                f"{self.auth_ownership.value} auth ownership must not carry a secret_ref_id"
            )

        if self.legacy_backfill:
            if self.runtime_profile_ref is not None or self.profile_revision is not None:
                raise RuntimeBindingError(
                    "legacy backfill snapshots must have NULL runtime_profile_ref "
                    "and NULL profile_revision"
                )
        else:
            if self.runtime_profile_ref is None or self.profile_revision is None:
                raise RuntimeBindingError(
                    "non-legacy snapshots require runtime_profile_ref and profile_revision"
                )

        resolved_at = self.resolved_at
        if not isinstance(resolved_at, datetime):
            raise RuntimeBindingError("resolved_at must be a datetime")
        if resolved_at.tzinfo is None:
            raise RuntimeBindingError(
                "resolved_at must be timezone-aware UTC (deterministic representation)"
            )
        # Normalize to UTC deterministically (frozen dataclass → object.__setattr__).
        object.__setattr__(self, "resolved_at", resolved_at.astimezone(timezone.utc))


@dataclass
class RuntimeProfile:
    """Mutable resolution intention (ADR-011 §3).

    In-memory / Registry only: no database table, no CRUD, no public API,
    no Workflow selection schema in this gate.
    """

    provider_id: str
    transport_kind: TransportKind
    runtime_id: str
    adapter_id: str
    execution_target: ExecutionTarget = ExecutionTarget.LOCAL
    runtime_profile_ref: str = ""
    profile_revision: int = 1
    auth_ownership: AuthOwnership = AuthOwnership.NONE
    secret_ref_id: str | None = None
    usage_visibility: UsageVisibility = UsageVisibility.UNAVAILABLE

    def __post_init__(self) -> None:
        validate_opaque_identifier(self.provider_id, "provider_id")
        validate_opaque_identifier(self.runtime_id, "runtime_id")
        validate_opaque_identifier(self.adapter_id, "adapter_id")
        validate_opaque_identifier(self.runtime_profile_ref, "runtime_profile_ref")
        if self.profile_revision < 1:
            raise RuntimeBindingError("profile_revision must be >= 1")

        # Auth ownership / secret reference invariant (ADR-011 §6).
        if self.auth_ownership is AuthOwnership.SECRET_REF:
            if not self.secret_ref_id:
                raise RuntimeBindingError(
                    "SECRET_REF auth ownership requires an opaque secret_ref_id"
                )
            _validate_optional_identifier(self.secret_ref_id, "secret_ref_id")
        elif self.secret_ref_id is not None:
            raise RuntimeBindingError(
                f"{self.auth_ownership.value} auth ownership must not carry a secret_ref_id"
            )

    def bind(
        self,
        run_id: str,
        resolved_at: datetime,
        adapter_version: str | None = None,
    ) -> RuntimeBindingSnapshot:
        """Resolve this profile into an immutable Run-owned snapshot."""
        return RuntimeBindingSnapshot(
            run_id=run_id,
            provider_id=self.provider_id,
            transport_kind=self.transport_kind,
            runtime_id=self.runtime_id,
            adapter_id=self.adapter_id,
            execution_target=self.execution_target,
            runtime_profile_ref=self.runtime_profile_ref,
            profile_revision=self.profile_revision,
            adapter_version=adapter_version,
            resolved_at=resolved_at,
            legacy_backfill=False,
            snapshot_schema_version=DEFAULT_SNAPSHOT_SCHEMA_VERSION,
            auth_ownership=self.auth_ownership,
            secret_ref_id=self.secret_ref_id,
            usage_visibility=self.usage_visibility,
        )


def legacy_backfill_snapshot(
    run_id: str,
    execution_target: ExecutionTarget,
    resolved_at: datetime,
) -> RuntimeBindingSnapshot:
    """Deterministic legacy/reference binding for pre-0002 Runs.

    These identities record that a Run predates runtime binding; they are NOT
    claims about what was actually resolved at execution time.
    """
    return RuntimeBindingSnapshot(
        run_id=run_id,
        provider_id="polynexus",
        transport_kind=TransportKind.LOCAL,
        runtime_id="reference",
        adapter_id="builtin.reference",
        execution_target=execution_target,
        runtime_profile_ref=None,
        profile_revision=None,
        adapter_version=None,
        resolved_at=resolved_at,
        legacy_backfill=True,
        snapshot_schema_version=DEFAULT_SNAPSHOT_SCHEMA_VERSION,
        auth_ownership=AuthOwnership.NONE,
        secret_ref_id=None,
        usage_visibility=UsageVisibility.UNAVAILABLE,
    )
