"""Exact-Run, single-use authority to dispatch a policy-approval-required runtime.

This is independent of Candidate/Human acceptance and never changes D05's
original APPROVAL_REQUIRED disposition.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from uuid import uuid4

from polynexus_core.domain.models import Run
from polynexus_core.domain.runtime_binding import RuntimeProfile
from polynexus_core.runtime.routing_policy import EgressPolicyDecision, PolicyDecision


class DispatchAuthorizationError(ValueError):
    pass


class DispatchAuthorizationState(StrEnum):
    ISSUED = "ISSUED"
    CONSUMED = "CONSUMED"
    REVOKED = "REVOKED"


class DispatchIssuerClass(StrEnum):
    HUMAN_ALP = "HUMAN_ALP"
    TEST_ONLY = "TEST_ONLY"


MAX_AUTHORIZATION_TTL = timedelta(minutes=15)
_HASH = re.compile(r"^[0-9a-f]{64}$")


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise DispatchAuthorizationError("authorization_time_invalid")
    return value.astimezone(timezone.utc)


def policy_authorization_digest(
    run: Run, profile: RuntimeProfile, decision: EgressPolicyDecision,
    policy_metadata: dict[str, str],
) -> str:
    """Bind normalized effective D05 facts, exact identity and profile."""
    payload = {
        "run_id": run.id, "task_id": run.task_id,
        "generation_revision": run.generation_revision,
        "runtime_profile_ref": profile.runtime_profile_ref,
        "profile_revision": profile.profile_revision,
        "provider_id": profile.provider_id, "runtime_id": profile.runtime_id,
        "adapter_id": profile.adapter_id,
        "effective_policy": decision.as_dict(),
        "routing_policy_evidence_metadata": policy_metadata,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class RuntimeDispatchAuthorization:
    run_id: str
    task_id: str
    generation_revision: int
    runtime_profile_ref: str
    profile_revision: int
    adapter_id: str
    policy_evidence_id: str
    policy_digest: str
    effective_classification: str
    execution_mode: str
    destination_trust: str
    tool_trust: str
    side_effect: bool
    issuer_ref: str
    issuer_class: DispatchIssuerClass
    issued_at: datetime
    expires_at: datetime
    authorization_id: str = ""
    state: DispatchAuthorizationState = DispatchAuthorizationState.ISSUED
    consumed_at: datetime | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.authorization_id:
            object.__setattr__(self, "authorization_id", "dispatch-auth_" + uuid4().hex)
        if any(not isinstance(value, str) or not value or len(value) > 256 for value in (
            self.authorization_id, self.run_id, self.task_id, self.runtime_profile_ref,
            self.adapter_id, self.policy_evidence_id, self.issuer_ref,
        )):
            raise DispatchAuthorizationError("authorization_identity_invalid")
        if not isinstance(self.generation_revision, int) or isinstance(self.generation_revision, bool) or self.generation_revision < 1:
            raise DispatchAuthorizationError("authorization_generation_invalid")
        if not isinstance(self.profile_revision, int) or isinstance(self.profile_revision, bool) or self.profile_revision < 1:
            raise DispatchAuthorizationError("authorization_profile_invalid")
        if not _HASH.fullmatch(self.policy_digest) or self.side_effect is not True:
            raise DispatchAuthorizationError("authorization_policy_invalid")
        if any(not isinstance(value, str) or not value for value in (
            self.effective_classification, self.execution_mode,
            self.destination_trust, self.tool_trust,
        )):
            raise DispatchAuthorizationError("authorization_policy_invalid")
        if not isinstance(self.issuer_class, DispatchIssuerClass) or not isinstance(self.state, DispatchAuthorizationState):
            raise DispatchAuthorizationError("authorization_state_invalid")
        if self.issuer_class is DispatchIssuerClass.HUMAN_ALP and not self.issuer_ref.startswith("human:"):
            raise DispatchAuthorizationError("authorization_issuer_invalid")
        if self.issuer_class is DispatchIssuerClass.TEST_ONLY and not self.issuer_ref.startswith("test-only:"):
            raise DispatchAuthorizationError("authorization_issuer_invalid")
        issued, expires = _utc(self.issued_at), _utc(self.expires_at)
        if not issued < expires <= issued + MAX_AUTHORIZATION_TTL:
            raise DispatchAuthorizationError("authorization_ttl_invalid")
        if self.state is DispatchAuthorizationState.ISSUED and (self.consumed_at or self.revoked_at):
            raise DispatchAuthorizationError("authorization_state_invalid")


def require_approval_required(decision: EgressPolicyDecision) -> None:
    if decision.decision is not PolicyDecision.APPROVAL_REQUIRED:
        raise DispatchAuthorizationError("authorization_policy_not_approval_required")
