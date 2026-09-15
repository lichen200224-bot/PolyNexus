"""Add independent exact-Run dispatch authorization and append-only audit."""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "runtime_dispatch_authorizations",
        sa.Column("authorization_id", sa.String(80), primary_key=True),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("task_id", sa.String(64), sa.ForeignKey("tasks.id"), nullable=False),
        sa.Column("generation_revision", sa.Integer(), nullable=False),
        sa.Column("runtime_profile_ref", sa.String(64), nullable=False),
        sa.Column("profile_revision", sa.Integer(), nullable=False),
        sa.Column("adapter_id", sa.String(64), nullable=False),
        sa.Column("policy_evidence_id", sa.String(64), sa.ForeignKey("evidence.id"), nullable=False),
        sa.Column("policy_digest", sa.String(64), nullable=False),
        sa.Column("effective_classification", sa.String(32), nullable=False),
        sa.Column("execution_mode", sa.String(32), nullable=False),
        sa.Column("destination_trust", sa.String(32), nullable=False),
        sa.Column("tool_trust", sa.String(32), nullable=False),
        sa.Column("side_effect", sa.Boolean(), nullable=False),
        sa.Column("issuer_ref", sa.String(256), nullable=False),
        sa.Column("issuer_class", sa.String(32), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint("generation_revision >= 1 AND profile_revision >= 1 AND side_effect = 1", name="ck_dispatch_scope"),
        sa.CheckConstraint("state IN ('ISSUED','CONSUMED','REVOKED')", name="ck_dispatch_state"),
        sa.CheckConstraint("issuer_class IN ('HUMAN_ALP','TEST_ONLY')", name="ck_dispatch_issuer"),
    )
    op.create_index("ix_dispatch_authorization_run_state", "runtime_dispatch_authorizations", ["run_id", "state"])
    op.create_index("uq_dispatch_issued_run", "runtime_dispatch_authorizations", ["run_id"],
                    unique=True, sqlite_where=sa.text("state = 'ISSUED'"))
    op.create_table(
        "runtime_dispatch_authorization_events",
        sa.Column("event_id", sa.String(80), primary_key=True),
        sa.Column("authorization_id", sa.String(80), sa.ForeignKey("runtime_dispatch_authorizations.authorization_id"), nullable=False),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.id"), nullable=False),
        sa.Column("event_kind", sa.String(16), nullable=False),
        sa.Column("from_state", sa.String(16), nullable=True),
        sa.Column("to_state", sa.String(16), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("event_kind IN ('ISSUE','CONSUME','REVOKE')", name="ck_dispatch_event_kind"),
    )
    op.create_index("ix_dispatch_authorization_events", "runtime_dispatch_authorization_events", ["authorization_id", "occurred_at"])
    immutable = (
        "authorization_id", "run_id", "task_id", "generation_revision",
        "runtime_profile_ref", "profile_revision", "adapter_id", "policy_evidence_id",
        "policy_digest", "effective_classification", "execution_mode",
        "destination_trust", "tool_trust", "side_effect", "issuer_ref", "issuer_class",
        "issued_at", "expires_at",
    )
    comparisons = " OR ".join(f"NEW.{name} IS NOT OLD.{name}" for name in immutable)
    op.execute(f"CREATE TRIGGER trg_dispatch_scope_immutable BEFORE UPDATE ON runtime_dispatch_authorizations WHEN {comparisons} BEGIN SELECT RAISE(ABORT, 'Dispatch authorization scope immutable'); END")
    op.execute("CREATE TRIGGER trg_dispatch_state_guard BEFORE UPDATE ON runtime_dispatch_authorizations WHEN (NEW.state IS NOT OLD.state OR NEW.consumed_at IS NOT OLD.consumed_at OR NEW.revoked_at IS NOT OLD.revoked_at) AND (OLD.state <> 'ISSUED' OR NEW.state NOT IN ('CONSUMED','REVOKED') OR (NEW.state='CONSUMED' AND (NEW.consumed_at IS NULL OR NEW.revoked_at IS NOT NULL)) OR (NEW.state='REVOKED' AND (NEW.revoked_at IS NULL OR NEW.consumed_at IS NOT NULL))) BEGIN SELECT RAISE(ABORT, 'Dispatch authorization transition invalid'); END")
    op.execute("CREATE TRIGGER trg_dispatch_retained BEFORE DELETE ON runtime_dispatch_authorizations BEGIN SELECT RAISE(ABORT, 'Dispatch authorization retained'); END")
    for kind in ("UPDATE", "DELETE"):
        op.execute(f"CREATE TRIGGER trg_dispatch_event_{kind.lower()} BEFORE {kind} ON runtime_dispatch_authorization_events BEGIN SELECT RAISE(ABORT, 'Dispatch authorization audit immutable'); END")


def downgrade() -> None:
    raise RuntimeError("Restore the pre-upgrade database backup; dispatch authorization audit is retained")
