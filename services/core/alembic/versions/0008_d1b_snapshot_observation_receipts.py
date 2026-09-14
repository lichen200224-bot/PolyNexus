"""Preserve per-capture provenance for content-addressed snapshots."""
from alembic import op
import sqlalchemy as sa


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "content_snapshot_observations",
        sa.Column("observation_id", sa.String(128), primary_key=True),
        sa.Column(
            "snapshot_id",
            sa.String(80),
            sa.ForeignKey("content_snapshots.snapshot_id"),
            nullable=False,
        ),
        sa.Column("source_ref", sa.String(512), nullable=False),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "snapshot_id",
            "source_ref",
            name="uq_snapshot_observation_source",
        ),
    )
    op.execute(
        """
        CREATE TRIGGER content_snapshot_observations_immutable
        BEFORE UPDATE ON content_snapshot_observations
        BEGIN SELECT RAISE(ABORT, 'D1b immutable record mutation rejected'); END
        """
    )
    op.execute(
        """
        CREATE TRIGGER content_snapshot_observations_retained
        BEFORE DELETE ON content_snapshot_observations
        BEGIN SELECT RAISE(ABORT, 'D1b immutable record deletion rejected'); END
        """
    )


def downgrade() -> None:
    raise RuntimeError("D1b downgrade is not lossless; restore the verified pre-upgrade backup")
