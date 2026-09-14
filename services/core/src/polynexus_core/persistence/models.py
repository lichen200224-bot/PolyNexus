from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from polynexus_core.domain.runtime_binding import RuntimeBindingError


class Base(DeclarativeBase):
    pass


class ProjectRow(Base):
    __tablename__ = "projects"
    classification = Column(String(32), nullable=False, default="INTERNAL", server_default="INTERNAL")
    archived = Column(Boolean, nullable=False, default=False, server_default="0")

    id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)


class TaskRow(Base):
    __tablename__ = "tasks"
    classification = Column(String(32), nullable=False, default="INTERNAL", server_default="INTERNAL")

    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    title = Column(String(512), nullable=False)
    workflow_id = Column(String(128), nullable=False)
    workflow_version = Column(Integer, nullable=False)
    mode = Column(String(32), nullable=False)
    context_package_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False)

    project = relationship("ProjectRow", backref="tasks")


class ContextPackageRow(Base):
    __tablename__ = "context_packages"
    classification = Column(String(32), nullable=False, default="INTERNAL", server_default="INTERNAL")

    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    version = Column(Integer, nullable=False)
    instructions = Column(Text, nullable=False, default="[]")
    constraints = Column(Text, nullable=False, default="[]")
    project_facts = Column(Text, nullable=False, default="{}")
    artifact_refs = Column(Text, nullable=False, default="[]")
    prior_decision_refs = Column(Text, nullable=False, default="[]")
    memory_refs = Column(Text, nullable=False, default="[]")
    source_refs = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, nullable=False)

    project = relationship("ProjectRow", backref="context_packages")


class RunRow(Base):
    __tablename__ = "runs"
    generation_revision = Column(Integer, nullable=True)
    generation_parent_run_id = Column(String(64), nullable=True)

    id = Column(String(64), primary_key=True)
    next_event_sequence = Column(Integer, nullable=False, default=0, server_default="0")
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    workflow_id = Column(String(128), nullable=False)
    workflow_version = Column(Integer, nullable=False)
    context_package_id = Column(String(64), nullable=False)
    execution_target = Column(String(32), nullable=False)
    resume_mode = Column(String(32), nullable=False)
    state = Column(String(32), nullable=False)
    runtime_ref = Column(String(256), nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    result_status = Column(String(32), nullable=True)
    result_summary = Column(Text, nullable=True)
    result_finding_ids = Column(Text, nullable=False, default="[]")
    result_evidence_ids = Column(Text, nullable=False, default="[]")
    result_artifact_ids = Column(Text, nullable=False, default="[]")

    task = relationship("TaskRow", backref="runs")


class RunEventRow(Base):
    __tablename__ = "run_events"
    __table_args__ = (
        UniqueConstraint("run_id", "event_sequence", name="uq_run_events_sequence"),
        CheckConstraint("event_sequence > 0", name="ck_run_events_sequence_positive"),
    )

    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False)
    event_sequence = Column(Integer, nullable=False)
    sequence_legacy_backfill = Column(Boolean, nullable=False, default=False, server_default="0")
    from_state = Column(String(32), nullable=False)
    to_state = Column(String(32), nullable=False)
    occurred_at = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)

    run = relationship("RunRow", backref="events")


@event.listens_for(RunEventRow.__table__, "after_create")
def _create_event_sequence_guard(target, connection, **kw) -> None:
    from sqlalchemy import text

    connection.execute(text(
        "CREATE TRIGGER trg_run_events_sequence_immutable "
        "BEFORE UPDATE OF run_id, event_sequence, sequence_legacy_backfill ON run_events "
        "WHEN NEW.run_id IS NOT OLD.run_id OR NEW.event_sequence IS NOT OLD.event_sequence "
        "OR NEW.sequence_legacy_backfill IS NOT OLD.sequence_legacy_backfill "
        "BEGIN SELECT RAISE(ABORT, 'Run event ordering metadata is immutable'); END"
    ))


class ArtifactRow(Base):
    __tablename__ = "artifacts"
    classification = Column(String(32), nullable=False, default="INTERNAL", server_default="INTERNAL")

    id = Column(String(64), primary_key=True)
    project_id = Column(String(64), ForeignKey("projects.id"), nullable=False)
    artifact_type = Column(String(32), nullable=False)
    mime_type = Column(String(128), nullable=False)
    source_type = Column(String(64), nullable=False)
    storage_ref = Column(String(512), nullable=False)
    sha256 = Column(String(64), nullable=False)
    size = Column(Integer, nullable=False, default=0)
    task_id = Column(String(64), nullable=True)
    run_id = Column(String(64), nullable=True)

    project = relationship("ProjectRow", backref="artifacts")


class FindingRow(Base):
    __tablename__ = "findings"

    id = Column(String(64), primary_key=True)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    run_id = Column(String(64), nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(32), nullable=False)
    evidence_refs = Column(Text, nullable=False, default="[]")
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime, nullable=False)

    task = relationship("TaskRow", backref="findings")


class EvidenceRow(Base):
    __tablename__ = "evidence"

    id = Column(String(64), primary_key=True)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=False)
    run_id = Column(String(64), nullable=False)
    actor_id = Column(String(64), nullable=False)
    source = Column(String(256), nullable=False)
    type = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)
    artifact_refs = Column(Text, nullable=False, default="[]")
    metadata_json = Column(Text, nullable=False, default="{}")
    observed_at = Column(DateTime, nullable=False)

    task = relationship("TaskRow", backref="evidence")


class RunBindingSnapshotRow(Base):
    """Run-owned immutable RuntimeBindingSnapshot (ADR-011 / PRE-WP14-B).

    - run_id is the primary key AND a foreign key to runs.id (1:1, no cascade).
    - Rows are never updated or deleted through the ORM: both operations are
      rejected fail-closed by the mapper-level listeners below.
    - No raw credential value is ever stored in any column.
    """

    __tablename__ = "run_binding_snapshots"

    run_id = Column(String(64), ForeignKey("runs.id"), primary_key=True)
    provider_id = Column(String(64), nullable=False)
    transport_kind = Column(String(32), nullable=False)
    runtime_id = Column(String(64), nullable=False)
    adapter_id = Column(String(64), nullable=False)
    execution_target = Column(String(32), nullable=False)
    runtime_profile_ref = Column(String(64), nullable=True)
    profile_revision = Column(Integer, nullable=True)
    adapter_version = Column(String(64), nullable=True)
    resolved_at = Column(DateTime, nullable=False)
    legacy_backfill = Column(Boolean, nullable=False, default=False)
    snapshot_schema_version = Column(Integer, nullable=False)
    auth_ownership = Column(String(32), nullable=False)
    secret_ref_id = Column(String(64), nullable=True)
    usage_visibility = Column(String(32), nullable=False)


@event.listens_for(RunBindingSnapshotRow, "before_update")
def _reject_snapshot_row_update(mapper, connection, target) -> None:
    raise RuntimeBindingError(
        "RuntimeBindingSnapshot rows are immutable: ORM update rejected"
    )


@event.listens_for(RunBindingSnapshotRow, "before_delete")
def _reject_snapshot_row_delete(mapper, connection, target) -> None:
    raise RuntimeBindingError(
        "RuntimeBindingSnapshot rows are immutable: ORM delete rejected"
    )


# Database-level guard: SQLite triggers reject UPDATE/DELETE even when they
# bypass the ORM (bulk Query.update()/delete(), raw SQL). This is the
# equivalent-strength transaction guard required by the PRE-WP14-B gate.
_REJECT_UPDATE_TRIGGER = (
    "CREATE TRIGGER IF NOT EXISTS trg_rbs_reject_update "
    "BEFORE UPDATE ON run_binding_snapshots "
    "BEGIN SELECT RAISE(ABORT, "
    "'RuntimeBindingSnapshot rows are immutable'); END"
)
_REJECT_DELETE_TRIGGER = (
    "CREATE TRIGGER IF NOT EXISTS trg_rbs_reject_delete "
    "BEFORE DELETE ON run_binding_snapshots "
    "BEGIN SELECT RAISE(ABORT, "
    "'RuntimeBindingSnapshot rows are immutable'); END"
)

# Run deletion is fail-closed at the database level: a Run owns its binding
# snapshot 1:1 forever, so deleting the Run row (which would orphan or
# require cascading the immutable snapshot) is rejected outright — for ORM
# deletes, bulk ORM deletes, and raw SQL alike — regardless of whether FK
# enforcement is enabled in the connection.
_RUN_DELETE_GUARD_TRIGGER = (
    "CREATE TRIGGER IF NOT EXISTS trg_runs_reject_delete "
    "BEFORE DELETE ON runs "
    "BEGIN SELECT RAISE(ABORT, "
    "'Run rows are protected: run deletion is not permitted'); END"
)


@event.listens_for(RunBindingSnapshotRow.__table__, "after_create")
def _create_snapshot_immutability_triggers(target, connection, **kw) -> None:
    from sqlalchemy import text as _text

    connection.execute(_text(_REJECT_UPDATE_TRIGGER))
    connection.execute(_text(_REJECT_DELETE_TRIGGER))


@event.listens_for(RunRow.__table__, "after_create")
def _create_run_delete_guard_trigger(target, connection, **kw) -> None:
    from sqlalchemy import text as _text

    connection.execute(_text(_RUN_DELETE_GUARD_TRIGGER))


# ---------------------------------------------------------------------------
# D1b immutable candidate/evidence/decision records
# ---------------------------------------------------------------------------


class ContentSnapshotRow(Base):
    __tablename__ = "content_snapshots"

    snapshot_id = Column(String(80), primary_key=True)
    canonical_json = Column(Text, nullable=False)
    source_closure_json = Column(Text, nullable=False, default="{}")
    source_ref = Column(String(512), nullable=True)
    created_at = Column(DateTime, nullable=False)


class ContentSnapshotObservationRow(Base):
    """Append-only provenance for each Core observation of content identity."""

    __tablename__ = "content_snapshot_observations"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "source_ref", name="uq_snapshot_observation_source"),
    )

    observation_id = Column(String(128), primary_key=True)
    snapshot_id = Column(String(80), ForeignKey("content_snapshots.snapshot_id"), nullable=False)
    source_ref = Column(String(512), nullable=False)
    observed_at = Column(DateTime, nullable=False)


class ChangeSetRow(Base):
    __tablename__ = "changesets"

    changeset_id = Column(String(80), primary_key=True)
    baseline_snapshot_id = Column(String(80), ForeignKey("content_snapshots.snapshot_id"), nullable=False)
    result_snapshot_id = Column(String(80), ForeignKey("content_snapshots.snapshot_id"), nullable=False)
    canonical_json = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)


class CandidateRow(Base):
    __tablename__ = "candidates"

    candidate_id = Column(String(80), primary_key=True)
    changeset_id = Column(String(80), ForeignKey("changesets.changeset_id"), nullable=False)
    requirements_snapshot_id = Column(String(80), ForeignKey("content_snapshots.snapshot_id"), nullable=False)
    validation_contract_snapshot_id = Column(String(80), ForeignKey("content_snapshots.snapshot_id"), nullable=False)
    canonical_json = Column(Text, nullable=False)
    source_closure_json = Column(Text, nullable=False, default="{}")
    frozen = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime, nullable=False)


class CandidatePublicationRow(Base):
    __tablename__ = "candidate_publications"

    publication_id = Column(String(80), primary_key=True)
    candidate_id = Column(String(80), ForeignKey("candidates.candidate_id"), nullable=False)
    task_id = Column(String(64), ForeignKey("tasks.id"), nullable=True)
    generation_revision = Column(Integer, nullable=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=True)
    lineage_ref = Column(String(128), nullable=False)
    provenance_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, nullable=False)


class EvidenceSetRow(Base):
    __tablename__ = "evidence_sets"

    evidence_set_id = Column(String(80), primary_key=True)
    candidate_id = Column(String(80), ForeignKey("candidates.candidate_id"), nullable=False)
    contract_id = Column(String(256), nullable=False)
    trusted_runner_ref = Column(String(256), nullable=True)
    canonical_json = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)


class VerificationRecordRow(Base):
    __tablename__ = "verification_records"

    verification_id = Column(String(80), primary_key=True)
    evidence_set_id = Column(String(80), ForeignKey("evidence_sets.evidence_set_id"), nullable=False)
    candidate_id = Column(String(80), ForeignKey("candidates.candidate_id"), nullable=False)
    contract_id = Column(String(256), nullable=False)
    requirements_snapshot_id = Column(String(80), ForeignKey("content_snapshots.snapshot_id"), nullable=True)
    result_json = Column(Text, nullable=False)
    policy_revision = Column(Integer, nullable=False, default=1, server_default="1")
    verifier_principal = Column(String(256), nullable=False, default="core", server_default="core")
    verifier_type = Column(String(64), nullable=False, default="CORE_TRUSTED_RUNNER", server_default="CORE_TRUSTED_RUNNER")
    environment_json = Column(Text, nullable=False, default="{}", server_default="{}")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)


class AssuranceAssessmentRow(Base):
    __tablename__ = "assurance_assessments"
    __table_args__ = (
        UniqueConstraint("candidate_id", "revision", name="uq_assurance_candidate_revision"),
    )

    assessment_id = Column(String(80), primary_key=True)
    target_type = Column(String(32), nullable=False)
    target_id = Column(String(80), nullable=False)
    candidate_id = Column(String(80), ForeignKey("candidates.candidate_id"), nullable=False)
    mode = Column(String(32), nullable=False)
    profile_ref = Column(String(256), nullable=True)
    profile_revision = Column(Integer, nullable=True)
    status = Column(String(32), nullable=False)
    outcome = Column(String(32), nullable=False)
    validity = Column(String(32), nullable=False)
    reason = Column(Text, nullable=False)
    verification_id = Column(String(80), ForeignKey("verification_records.verification_id"), nullable=True)
    evidence_set_id = Column(String(80), ForeignKey("evidence_sets.evidence_set_id"), nullable=True)
    revision = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False)


class HumanEnrollmentChallengeRow(Base):
    __tablename__ = "human_enrollment_challenges"

    challenge_id = Column(String(80), primary_key=True)
    ceremony = Column(String(32), nullable=False)
    principal_ref = Column(String(256), nullable=True)
    key_id = Column(String(80), nullable=True)
    challenge_digest = Column(String(64), nullable=False)
    audience = Column(String(128), nullable=False)
    installation_id = Column(String(80), nullable=False)
    rp_id = Column(String(256), nullable=False)
    origin = Column(String(512), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)


class HumanTrustKeyRow(Base):
    __tablename__ = "human_trust_keys"
    __table_args__ = (
        UniqueConstraint("credential_id", name="uq_human_trust_key_credential"),
    )

    key_id = Column(String(80), primary_key=True)
    principal_ref = Column(String(256), nullable=False)
    credential_id = Column(String(2048), nullable=False)
    public_key = Column(String(256), nullable=False)
    algorithm = Column(String(32), nullable=False)
    rp_id = Column(String(256), nullable=False)
    origin = Column(String(512), nullable=False)
    installation_id = Column(String(80), nullable=False)
    status = Column(String(32), nullable=False)
    sign_count = Column(Integer, nullable=False, default=0, server_default="0")
    rotated_from = Column(String(80), nullable=True)
    retire_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)


class HumanPairingGrantRow(Base):
    __tablename__ = "human_pairing_grants"
    __table_args__ = (
        UniqueConstraint("proof_digest", name="uq_human_pairing_proof_digest"),
    )

    grant_id = Column(String(80), primary_key=True)
    principal_ref = Column(String(256), nullable=False)
    proof_digest = Column(String(64), nullable=False)
    key_id = Column(String(80), nullable=True)
    auth_method = Column(String(64), nullable=True)
    installation_id = Column(String(80), nullable=True)
    enrollment_challenge_id = Column(String(80), nullable=True)
    status = Column(String(32), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)


class HumanSessionRow(Base):
    __tablename__ = "human_sessions"

    session_id = Column(String(80), primary_key=True)
    grant_id = Column(String(80), ForeignKey("human_pairing_grants.grant_id"), nullable=False)
    principal_ref = Column(String(256), nullable=False)
    audience = Column(String(64), nullable=False)
    csrf_digest = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)


class HumanChallengeRow(Base):
    __tablename__ = "human_challenges"

    challenge_id = Column(String(80), primary_key=True)
    session_id = Column(String(80), ForeignKey("human_sessions.session_id"), nullable=False)
    candidate_id = Column(String(80), ForeignKey("candidates.candidate_id"), nullable=False)
    view_digest = Column(String(80), nullable=False)
    action = Column(String(32), nullable=False)
    replacement_acceptance_id = Column(String(80), nullable=True)
    policy_revision = Column(Integer, nullable=True)
    nonce_digest = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    consumed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)


class HumanDecisionEventRow(Base):
    __tablename__ = "human_decision_events"
    __table_args__ = (
        UniqueConstraint("principal_ref", "command_id", name="uq_human_decision_command"),
        UniqueConstraint("candidate_id", "revision", name="uq_human_decision_candidate_revision"),
        CheckConstraint("action IN ('Accept','Reject','Revoke','Supersede')", name="ck_human_decision_action"),
    )

    decision_id = Column(String(80), primary_key=True)
    candidate_id = Column(String(80), ForeignKey("candidates.candidate_id"), nullable=False)
    acceptance_id = Column(String(80), nullable=True)
    action = Column(String(32), nullable=False)
    principal_ref = Column(String(256), nullable=False)
    session_id = Column(String(80), ForeignKey("human_sessions.session_id"), nullable=False)
    challenge_id = Column(String(80), ForeignKey("human_challenges.challenge_id"), nullable=False)
    command_id = Column(String(128), nullable=False)
    view_digest = Column(String(80), nullable=False)
    prior_acceptance_id = Column(String(80), nullable=True)
    replacement_acceptance_id = Column(String(80), nullable=True)
    reason = Column(Text, nullable=True)
    revision = Column(Integer, nullable=False)
    # Legacy rows created before the A-LP closure fields remain nullable and
    # are fail-closed by the repository.  New decisions must populate these
    # exact trust/protocol facts; they are part of the portable audit record.
    trust_scope = Column(String(64), nullable=True)
    auth_method = Column(String(64), nullable=True)
    protocol_evidence_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)


class AcceptedResultRow(Base):
    __tablename__ = "accepted_results"
    __table_args__ = (
        UniqueConstraint("candidate_id", "accept_decision_id", name="uq_accepted_candidate_decision"),
    )

    acceptance_id = Column(String(80), primary_key=True)
    candidate_id = Column(String(80), ForeignKey("candidates.candidate_id"), nullable=False)
    accept_decision_id = Column(String(80), ForeignKey("human_decision_events.decision_id"), nullable=False)
    publication_id = Column(String(80), ForeignKey("candidate_publications.publication_id"), nullable=True)
    # These are acceptance-time closure references.  SQLite's additive
    # migration cannot add foreign-key constraints without rebuilding the
    # immutable table; repository guards enforce the same candidate-scoped
    # binding before the immutable row is inserted.
    verification_id = Column(String(80), nullable=True)
    evidence_set_id = Column(String(80), nullable=True)
    policy_revision = Column(Integer, nullable=True)
    view_digest = Column(String(80), nullable=True)
    created_at = Column(DateTime, nullable=False)


class ManagedWorktreeRow(Base):
    __tablename__ = "accepted_managed_worktrees"
    __table_args__ = (
        UniqueConstraint("acceptance_id", "candidate_id", name="uq_worktree_acceptance_candidate"),
    )

    workspace_id = Column(String(80), primary_key=True)
    acceptance_id = Column(String(80), ForeignKey("accepted_results.acceptance_id"), nullable=False)
    candidate_id = Column(String(80), ForeignKey("candidates.candidate_id"), nullable=False)
    path_ref = Column(String(1024), nullable=False)
    label = Column(String(64), nullable=False)
    owner_ref = Column(String(256), nullable=False)
    taken_over = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime, nullable=False)


class P0PackageRow(Base):
    __tablename__ = "p0_packages"
    __table_args__ = (
        UniqueConstraint("acceptance_id", "candidate_id", name="uq_p0_acceptance_candidate"),
    )

    package_id = Column(String(80), primary_key=True)
    acceptance_id = Column(String(80), ForeignKey("accepted_results.acceptance_id"), nullable=False)
    candidate_id = Column(String(80), ForeignKey("candidates.candidate_id"), nullable=False)
    package_path = Column(String(1024), nullable=False)
    manifest_json = Column(Text, nullable=False)
    manifest_digest = Column(String(80), nullable=False)
    created_at = Column(DateTime, nullable=False)


_D1B_IMMUTABLE_TABLES = (
    "content_snapshots",
    "content_snapshot_observations",
    "changesets",
    "candidates",
    "candidate_publications",
    "evidence_sets",
    "verification_records",
    "assurance_assessments",
    "human_decision_events",
    "accepted_results",
    "p0_packages",
)

_D1B_RETAINED_TABLES = (
    "human_trust_keys",
    "human_enrollment_challenges",
    "human_pairing_grants",
    "human_sessions",
    "human_challenges",
    "accepted_managed_worktrees",
)


def _create_d1b_immutability_triggers(target, connection, **kw) -> None:
    from sqlalchemy import text as _text

    table = target.name
    if table in _D1B_IMMUTABLE_TABLES:
        connection.execute(_text(
            f"CREATE TRIGGER IF NOT EXISTS {table}_immutable "
            f"BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT, "
            "'D1b immutable record mutation rejected'); END"
        ))
        connection.execute(_text(
            f"CREATE TRIGGER IF NOT EXISTS {table}_retained "
            f"BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT, "
            "'D1b immutable record deletion rejected'); END"
        ))
    elif table in _D1B_RETAINED_TABLES:
        connection.execute(_text(
            f"CREATE TRIGGER IF NOT EXISTS {table}_retained "
            f"BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT, "
            "'D1b security record deletion rejected'); END"
        ))


for _d1b_table_name in _D1B_IMMUTABLE_TABLES:
    _d1b_table = Base.metadata.tables.get(_d1b_table_name)
    if _d1b_table is not None:
        event.listen(_d1b_table, "after_create", _create_d1b_immutability_triggers)
for _d1b_table_name in _D1B_RETAINED_TABLES:
    _d1b_table = Base.metadata.tables.get(_d1b_table_name)
    if _d1b_table is not None:
        event.listen(_d1b_table, "after_create", _create_d1b_immutability_triggers)


def _serialize_tuple(value: tuple) -> str:
    return json.dumps(list(value))


def _deserialize_tuple(value: str) -> tuple:
    return tuple(json.loads(value))


def _serialize_dict(value: dict) -> str:
    return json.dumps(value)


def _deserialize_dict(value: str) -> dict:
    return json.loads(value)
