"""Add the Core-owned local A-LP WebAuthn trust registry."""

from alembic import op
import sqlalchemy as sa


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "human_trust_keys",
        sa.Column("key_id", sa.String(80), primary_key=True),
        sa.Column("principal_ref", sa.String(256), nullable=False),
        sa.Column("credential_id", sa.String(2048), nullable=False),
        sa.Column("public_key", sa.String(256), nullable=False),
        sa.Column("algorithm", sa.String(32), nullable=False),
        sa.Column("rp_id", sa.String(256), nullable=False),
        sa.Column("origin", sa.String(512), nullable=False),
        sa.Column("installation_id", sa.String(80), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rotated_from", sa.String(80), nullable=True),
        sa.Column("retire_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("credential_id", name="uq_human_trust_key_credential"),
    )
    op.create_table(
        "human_enrollment_challenges",
        sa.Column("challenge_id", sa.String(80), primary_key=True),
        sa.Column("ceremony", sa.String(32), nullable=False),
        sa.Column("principal_ref", sa.String(256), nullable=True),
        sa.Column("key_id", sa.String(80), nullable=True),
        sa.Column("challenge_digest", sa.String(64), nullable=False),
        sa.Column("audience", sa.String(128), nullable=False),
        sa.Column("installation_id", sa.String(80), nullable=False),
        sa.Column("rp_id", sa.String(256), nullable=False),
        sa.Column("origin", sa.String(512), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_human_enrollment_challenge_digest",
        "human_enrollment_challenges",
        ["challenge_digest"],
        unique=True,
    )
    op.execute(
        """
        CREATE TRIGGER human_trust_keys_retained
        BEFORE DELETE ON human_trust_keys
        BEGIN SELECT RAISE(ABORT, 'D1b security record deletion rejected'); END
        """
    )
    op.execute(
        """
        CREATE TRIGGER human_enrollment_challenges_retained
        BEFORE DELETE ON human_enrollment_challenges
        BEGIN SELECT RAISE(ABORT, 'D1b security record deletion rejected'); END
        """
    )
    op.add_column(
        "human_pairing_grants",
        sa.Column("key_id", sa.String(80), nullable=True),
    )
    op.add_column(
        "human_pairing_grants",
        sa.Column("auth_method", sa.String(64), nullable=True),
    )
    op.add_column(
        "human_pairing_grants",
        sa.Column("installation_id", sa.String(80), nullable=True),
    )
    op.add_column(
        "human_pairing_grants",
        sa.Column("enrollment_challenge_id", sa.String(80), nullable=True),
    )


def downgrade() -> None:
    raise RuntimeError("A-LP trust registry downgrade is not lossless; restore a verified backup")
