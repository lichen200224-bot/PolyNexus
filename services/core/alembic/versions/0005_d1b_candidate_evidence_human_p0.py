"""D1b immutable Candidate, evidence, Human decision and P0 records.

The revision is additive.  Existing D0/D1a/D2a records are not rewritten and
the downgrade remains restore-only because removing accepted history would not
be lossless.
"""
from alembic import op
import sqlalchemy as sa


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def _immutable_trigger(table: str) -> None:
    op.execute(
        f"CREATE TRIGGER {table}_immutable BEFORE UPDATE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'D1b immutable record mutation rejected'); END"
    )
    op.execute(
        f"CREATE TRIGGER {table}_retained BEFORE DELETE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'D1b immutable record deletion rejected'); END"
    )


def _retained_trigger(table: str) -> None:
    op.execute(
        f"CREATE TRIGGER {table}_retained BEFORE DELETE ON {table} "
        "BEGIN SELECT RAISE(ABORT, 'D1b security record deletion rejected'); END"
    )


def upgrade() -> None:
    op.create_table(
        "content_snapshots",
        sa.Column("snapshot_id", sa.String(80), primary_key=True),
        sa.Column("canonical_json", sa.Text(), nullable=False),
        sa.Column("source_closure_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("source_ref", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "changesets",
        sa.Column("changeset_id", sa.String(80), primary_key=True),
        sa.Column("baseline_snapshot_id", sa.String(80), sa.ForeignKey("content_snapshots.snapshot_id"), nullable=False),
        sa.Column("result_snapshot_id", sa.String(80), sa.ForeignKey("content_snapshots.snapshot_id"), nullable=False),
        sa.Column("canonical_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "candidates",
        sa.Column("candidate_id", sa.String(80), primary_key=True),
        sa.Column("changeset_id", sa.String(80), sa.ForeignKey("changesets.changeset_id"), nullable=False),
        sa.Column("requirements_snapshot_id", sa.String(80), sa.ForeignKey("content_snapshots.snapshot_id"), nullable=False),
        sa.Column("validation_contract_snapshot_id", sa.String(80), sa.ForeignKey("content_snapshots.snapshot_id"), nullable=False),
        sa.Column("canonical_json", sa.Text(), nullable=False),
        sa.Column("source_closure_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("frozen", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "candidate_publications",
        sa.Column("publication_id", sa.String(80), primary_key=True),
        sa.Column("candidate_id", sa.String(80), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("task_id", sa.String(64), sa.ForeignKey("tasks.id"), nullable=True),
        sa.Column("generation_revision", sa.Integer(), nullable=True),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.id"), nullable=True),
        sa.Column("lineage_ref", sa.String(128), nullable=False),
        sa.Column("provenance_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "evidence_sets",
        sa.Column("evidence_set_id", sa.String(80), primary_key=True),
        sa.Column("candidate_id", sa.String(80), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("contract_id", sa.String(256), nullable=False),
        sa.Column("canonical_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "verification_records",
        sa.Column("verification_id", sa.String(80), primary_key=True),
        sa.Column("evidence_set_id", sa.String(80), sa.ForeignKey("evidence_sets.evidence_set_id"), nullable=False),
        sa.Column("candidate_id", sa.String(80), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("contract_id", sa.String(256), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "assurance_assessments",
        sa.Column("assessment_id", sa.String(80), primary_key=True),
        sa.Column("target_type", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(80), nullable=False),
        sa.Column("candidate_id", sa.String(80), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("profile_ref", sa.String(256), nullable=True),
        sa.Column("profile_revision", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=False),
        sa.Column("validity", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("verification_id", sa.String(80), sa.ForeignKey("verification_records.verification_id"), nullable=True),
        sa.Column("evidence_set_id", sa.String(80), sa.ForeignKey("evidence_sets.evidence_set_id"), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "human_pairing_grants",
        sa.Column("grant_id", sa.String(80), primary_key=True),
        sa.Column("principal_ref", sa.String(256), nullable=False),
        sa.Column("proof_digest", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "human_sessions",
        sa.Column("session_id", sa.String(80), primary_key=True),
        sa.Column("grant_id", sa.String(80), sa.ForeignKey("human_pairing_grants.grant_id"), nullable=False),
        sa.Column("principal_ref", sa.String(256), nullable=False),
        sa.Column("audience", sa.String(64), nullable=False),
        sa.Column("csrf_digest", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "human_challenges",
        sa.Column("challenge_id", sa.String(80), primary_key=True),
        sa.Column("session_id", sa.String(80), sa.ForeignKey("human_sessions.session_id"), nullable=False),
        sa.Column("candidate_id", sa.String(80), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("view_digest", sa.String(80), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("nonce_digest", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "human_decision_events",
        sa.Column("decision_id", sa.String(80), primary_key=True),
        sa.Column("candidate_id", sa.String(80), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("acceptance_id", sa.String(80), nullable=True),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("principal_ref", sa.String(256), nullable=False),
        sa.Column("session_id", sa.String(80), sa.ForeignKey("human_sessions.session_id"), nullable=False),
        sa.Column("challenge_id", sa.String(80), sa.ForeignKey("human_challenges.challenge_id"), nullable=False),
        sa.Column("command_id", sa.String(128), nullable=False),
        sa.Column("view_digest", sa.String(80), nullable=False),
        sa.Column("prior_acceptance_id", sa.String(80), nullable=True),
        sa.Column("replacement_acceptance_id", sa.String(80), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("principal_ref", "command_id", name="uq_human_decision_command"),
        sa.CheckConstraint("action IN ('Accept','Reject','Revoke','Supersede')", name="ck_human_decision_action"),
    )
    op.create_table(
        "accepted_results",
        sa.Column("acceptance_id", sa.String(80), primary_key=True),
        sa.Column("candidate_id", sa.String(80), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("accept_decision_id", sa.String(80), sa.ForeignKey("human_decision_events.decision_id"), nullable=False),
        sa.Column("publication_id", sa.String(80), sa.ForeignKey("candidate_publications.publication_id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "accepted_managed_worktrees",
        sa.Column("workspace_id", sa.String(80), primary_key=True),
        sa.Column("acceptance_id", sa.String(80), sa.ForeignKey("accepted_results.acceptance_id"), nullable=False),
        sa.Column("candidate_id", sa.String(80), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("path_ref", sa.String(1024), nullable=False),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("owner_ref", sa.String(256), nullable=False),
        sa.Column("taken_over", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "p0_packages",
        sa.Column("package_id", sa.String(80), primary_key=True),
        sa.Column("acceptance_id", sa.String(80), sa.ForeignKey("accepted_results.acceptance_id"), nullable=False),
        sa.Column("candidate_id", sa.String(80), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("package_path", sa.String(1024), nullable=False),
        sa.Column("manifest_json", sa.Text(), nullable=False),
        sa.Column("manifest_digest", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    for table in (
        "content_snapshots",
        "changesets",
        "candidates",
        "candidate_publications",
        "evidence_sets",
        "verification_records",
        "assurance_assessments",
        "human_decision_events",
        "accepted_results",
        "p0_packages",
    ):
        _immutable_trigger(table)
    for table in (
        "human_pairing_grants",
        "human_sessions",
        "human_challenges",
        "accepted_managed_worktrees",
    ):
        _retained_trigger(table)


def downgrade() -> None:
    raise RuntimeError("D1b downgrade is not lossless; restore the verified pre-upgrade backup")
