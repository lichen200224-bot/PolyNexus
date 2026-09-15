"""Durable RuntimeDispatchAuthorization issue, exact validation and CAS consume.

Scope fields cannot be updated, consumed authority cannot be replayed, and
all state transitions produce append-only rows in the same SQL transaction.
"""
from __future__ import annotations

import hmac
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from polynexus_core.domain.models import Evidence, Run, new_id, utc_now
from polynexus_core.domain.enums import EvidenceStatus, EvidenceType, RunState
from polynexus_core.domain.runtime_binding import RuntimeProfile
from polynexus_core.domain.runtime_dispatch_authorization import (
    DispatchAuthorizationError, DispatchAuthorizationState, DispatchIssuerClass,
    RuntimeDispatchAuthorization, MAX_AUTHORIZATION_TTL,
    policy_authorization_digest, require_approval_required,
)
from polynexus_core.persistence.models import (
    RuntimeDispatchAuthorizationRow, RuntimeDispatchAuthorizationEventRow,
)
from polynexus_core.runtime.routing_policy import EgressPolicyDecision


def _db_time(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _test_only_database(session: Session) -> bool:
    """TEST_ONLY cannot be issued/consumed against a normal product database."""
    if os.environ.get("POLYNEXUS_DISPATCH_TEST_ONLY") != "1":
        return False
    bind = session.get_bind()
    url = bind.url
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return False
    database = Path(url.database).resolve(strict=False)
    temporary = Path(tempfile.gettempdir()).resolve(strict=True)
    return database.is_relative_to(temporary)


def _as_domain(row: RuntimeDispatchAuthorizationRow) -> RuntimeDispatchAuthorization:
    return RuntimeDispatchAuthorization(
        authorization_id=row.authorization_id, run_id=row.run_id, task_id=row.task_id,
        generation_revision=row.generation_revision, runtime_profile_ref=row.runtime_profile_ref,
        profile_revision=row.profile_revision, adapter_id=row.adapter_id,
        policy_evidence_id=row.policy_evidence_id, policy_digest=row.policy_digest,
        effective_classification=row.effective_classification,
        execution_mode=row.execution_mode, destination_trust=row.destination_trust,
        tool_trust=row.tool_trust, side_effect=bool(row.side_effect),
        issuer_ref=row.issuer_ref, issuer_class=DispatchIssuerClass(row.issuer_class),
        issued_at=_utc(row.issued_at), expires_at=_utc(row.expires_at),
        state=DispatchAuthorizationState(row.state),
        consumed_at=_utc(row.consumed_at) if row.consumed_at else None,
        revoked_at=_utc(row.revoked_at) if row.revoked_at else None,
    )


class RuntimeDispatchAuthorizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _event(
        self, authorization_id: str, run_id: str, kind: str,
        before: str | None, after: str, at: datetime,
    ) -> None:
        self.session.add(RuntimeDispatchAuthorizationEventRow(
            event_id=new_id("dispatch-event"), authorization_id=authorization_id,
            run_id=run_id, event_kind=kind, from_state=before,
            to_state=after, occurred_at=_db_time(at),
        ))
        self.session.flush()

    def issue_human(
        self, run: Run, profile: RuntimeProfile, decision: EgressPolicyDecision,
        policy_evidence: Evidence, *, session_id: str, csrf_token: str | bytes,
        ttl: timedelta = timedelta(minutes=5),
    ) -> RuntimeDispatchAuthorization:
        """Reuse A-LP verified principal/session proof, with separate action scope."""
        from polynexus_core.persistence.d1b import (
            D1bRepository, HumanProtocolError, HumanPairingGrantRow,
            HUMAN_WEBAUTHN_AUTH_METHOD, _raw_digest,
        )
        try:
            human = D1bRepository(self.session)._active_session(session_id)
            grant = self.session.get(HumanPairingGrantRow, human.grant_id)
            if (
                human.audience != "runtime-dispatch" or grant is None
                or grant.auth_method != HUMAN_WEBAUTHN_AUTH_METHOD
                or not hmac.compare_digest(human.csrf_digest, _raw_digest(csrf_token, "csrf_token"))
            ):
                raise DispatchAuthorizationError("authorization_human_proof_invalid")
        except (HumanProtocolError, TypeError, ValueError) as exc:
            raise DispatchAuthorizationError("authorization_human_proof_invalid") from exc
        return self._issue(run, profile, decision, policy_evidence,
                           issuer_ref=human.principal_ref,
                           issuer_class=DispatchIssuerClass.HUMAN_ALP, ttl=ttl)

    def issue_test_only(
        self, run: Run, profile: RuntimeProfile, decision: EgressPolicyDecision,
        policy_evidence: Evidence, *, ttl: timedelta = timedelta(minutes=5),
    ) -> RuntimeDispatchAuthorization:
        if not _test_only_database(self.session):
            raise DispatchAuthorizationError("authorization_test_only_environment_invalid")
        return self._issue(run, profile, decision, policy_evidence,
                           issuer_ref="test-only:isolated-technical",
                           issuer_class=DispatchIssuerClass.TEST_ONLY, ttl=ttl)

    def _issue(
        self, run: Run, profile: RuntimeProfile, decision: EgressPolicyDecision,
        policy_evidence: Evidence, *, issuer_ref: str, issuer_class: DispatchIssuerClass,
        ttl: timedelta,
    ) -> RuntimeDispatchAuthorization:
        require_approval_required(decision)
        if not isinstance(ttl, timedelta) or not timedelta(0) < ttl <= MAX_AUTHORIZATION_TTL:
            raise DispatchAuthorizationError("authorization_ttl_invalid")
        if run.state is not RunState.CREATED or run.generation_revision is None:
            raise DispatchAuthorizationError("authorization_run_not_created")
        if policy_evidence.run_id != run.id or policy_evidence.task_id != run.task_id or policy_evidence.source != "runtime.routing_policy":
            raise DispatchAuthorizationError("authorization_policy_evidence_invalid")
        if policy_evidence.metadata != {**{key: str(value) for key, value in decision.as_dict().items()},
                                       "generation_revision": str(run.generation_revision)}:
            raise DispatchAuthorizationError("authorization_policy_evidence_invalid")
        existing = self.session.execute(select(RuntimeDispatchAuthorizationRow).where(
            RuntimeDispatchAuthorizationRow.run_id == run.id,
            RuntimeDispatchAuthorizationRow.state == DispatchAuthorizationState.ISSUED.value,
        )).scalars().all()
        if existing:
            raise DispatchAuthorizationError("authorization_already_issued")
        now = utc_now()
        authorization = RuntimeDispatchAuthorization(
            run_id=run.id, task_id=run.task_id,
            generation_revision=run.generation_revision,
            runtime_profile_ref=profile.runtime_profile_ref,
            profile_revision=profile.profile_revision, adapter_id=profile.adapter_id,
            policy_evidence_id=policy_evidence.id,
            policy_digest=policy_authorization_digest(run, profile, decision, dict(policy_evidence.metadata)),
            effective_classification=decision.classification.value,
            execution_mode=decision.execution_mode.value,
            destination_trust=decision.destination_trust.value,
            tool_trust=decision.tool_trust.value,
            side_effect=decision.side_effect,
            issuer_ref=issuer_ref, issuer_class=issuer_class,
            issued_at=now, expires_at=now + ttl,
        )
        row = RuntimeDispatchAuthorizationRow(
            **{key: getattr(authorization, key) for key in (
                "authorization_id", "run_id", "task_id", "generation_revision",
                "runtime_profile_ref", "profile_revision", "adapter_id", "policy_evidence_id",
                "policy_digest", "effective_classification", "execution_mode",
                "destination_trust", "tool_trust", "side_effect", "issuer_ref",
            )},
            issuer_class=authorization.issuer_class.value,
            issued_at=_db_time(authorization.issued_at),
            expires_at=_db_time(authorization.expires_at),
            state=authorization.state.value,
            consumed_at=None, revoked_at=None,
        )
        self.session.add(row)
        self.session.flush()
        self._event(authorization.authorization_id, run.id, "ISSUE", None, "ISSUED", now)
        return authorization

    def get_issued_for_run(self, run_id: str) -> RuntimeDispatchAuthorization | None:
        rows = self.session.execute(select(RuntimeDispatchAuthorizationRow).where(
            RuntimeDispatchAuthorizationRow.run_id == run_id,
            RuntimeDispatchAuthorizationRow.state == DispatchAuthorizationState.ISSUED.value,
        )).scalars().all()
        if len(rows) > 1:
            raise DispatchAuthorizationError("authorization_ambiguous")
        return _as_domain(rows[0]) if rows else None

    def get(self, authorization_id: str) -> RuntimeDispatchAuthorization | None:
        row = self.session.get(RuntimeDispatchAuthorizationRow, authorization_id)
        return _as_domain(row) if row else None

    def validate(
        self, authorization: RuntimeDispatchAuthorization, run: Run,
        profile: RuntimeProfile, decision: EgressPolicyDecision, policy_evidence: Evidence,
    ) -> None:
        require_approval_required(decision)
        if authorization.state is not DispatchAuthorizationState.ISSUED:
            raise DispatchAuthorizationError("authorization_replayed")
        if authorization.expires_at <= utc_now():
            raise DispatchAuthorizationError("authorization_expired")
        if authorization.issuer_class is DispatchIssuerClass.TEST_ONLY and not _test_only_database(self.session):
            raise DispatchAuthorizationError("authorization_test_only_environment_invalid")
        if authorization.run_id != run.id or authorization.task_id != run.task_id:
            raise DispatchAuthorizationError("authorization_run_scope_mismatch")
        if authorization.generation_revision != run.generation_revision:
            raise DispatchAuthorizationError("authorization_generation_mismatch")
        if (
            authorization.runtime_profile_ref != profile.runtime_profile_ref
            or authorization.profile_revision != profile.profile_revision
            or authorization.adapter_id != profile.adapter_id
        ):
            raise DispatchAuthorizationError("authorization_profile_mismatch")
        if authorization.policy_evidence_id != policy_evidence.id:
            raise DispatchAuthorizationError("authorization_policy_evidence_mismatch")
        if (
            authorization.policy_digest != policy_authorization_digest(run, profile, decision, dict(policy_evidence.metadata))
            or authorization.effective_classification != decision.classification.value
            or authorization.execution_mode != decision.execution_mode.value
            or authorization.destination_trust != decision.destination_trust.value
            or authorization.tool_trust != decision.tool_trust.value
            or authorization.side_effect is not True
        ):
            raise DispatchAuthorizationError("authorization_stale")

    def consume(
        self, authorization: RuntimeDispatchAuthorization, run: Run,
        profile: RuntimeProfile, decision: EgressPolicyDecision, policy_evidence: Evidence,
    ) -> Evidence:
        self.validate(authorization, run, profile, decision, policy_evidence)
        now = utc_now()
        changed = self.session.execute(update(RuntimeDispatchAuthorizationRow).where(
            RuntimeDispatchAuthorizationRow.authorization_id == authorization.authorization_id,
            RuntimeDispatchAuthorizationRow.run_id == run.id,
            RuntimeDispatchAuthorizationRow.state == "ISSUED",
            RuntimeDispatchAuthorizationRow.expires_at > _db_time(now),
        ).values(state="CONSUMED", consumed_at=_db_time(now))).rowcount
        if changed != 1:
            raise DispatchAuthorizationError("authorization_replayed")
        self._event(authorization.authorization_id, run.id, "CONSUME", "ISSUED", "CONSUMED", now)
        return Evidence(
            task_id=run.task_id, run_id=run.id,
            actor_id="core:runtime-dispatch-authorization",
            source="runtime.dispatch_authorization",
            type=EvidenceType.RUNTIME_EVIDENCE, status=EvidenceStatus.OBSERVED,
            metadata={
                "authorization_id": authorization.authorization_id,
                "issuer_class": authorization.issuer_class.value,
                "policy_digest": authorization.policy_digest,
                "policy_evidence_id": authorization.policy_evidence_id,
                "issued_at": authorization.issued_at.isoformat(),
                "consumed_at": now.isoformat(),
                "effective_dispatch_outcome": "AUTHORIZED_FOR_EXACT_RUN",
                "original_policy_decision": "APPROVAL_REQUIRED",
            },
        )

    def revoke(self, authorization_id: str) -> None:
        authorization = self.get(authorization_id)
        if authorization is None or authorization.state is not DispatchAuthorizationState.ISSUED:
            raise DispatchAuthorizationError("authorization_replayed")
        now = utc_now()
        changed = self.session.execute(update(RuntimeDispatchAuthorizationRow).where(
            RuntimeDispatchAuthorizationRow.authorization_id == authorization_id,
            RuntimeDispatchAuthorizationRow.state == "ISSUED",
        ).values(state="REVOKED", revoked_at=_db_time(now))).rowcount
        if changed != 1:
            raise DispatchAuthorizationError("authorization_replayed")
        self._event(authorization_id, authorization.run_id, "REVOKE", "ISSUED", "REVOKED", now)

    def events(self, authorization_id: str) -> tuple[RuntimeDispatchAuthorizationEventRow, ...]:
        return tuple(self.session.execute(select(RuntimeDispatchAuthorizationEventRow).where(
            RuntimeDispatchAuthorizationEventRow.authorization_id == authorization_id
        ).order_by(RuntimeDispatchAuthorizationEventRow.occurred_at, RuntimeDispatchAuthorizationEventRow.event_id)).scalars())
