"""D1b challenge replacement binding and enrollment replay race guards."""
from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "human_challenges",
        sa.Column("replacement_acceptance_id", sa.String(80), nullable=True),
    )
    op.create_index(
        "uq_human_pairing_proof_digest",
        "human_pairing_grants",
        ["proof_digest"],
        unique=True,
    )
    op.execute(
        """
        CREATE TRIGGER d1b_challenge_replacement_binding
        BEFORE INSERT ON human_decision_events
        WHEN NOT EXISTS (
            SELECT 1 FROM human_challenges c
            WHERE c.challenge_id = NEW.challenge_id
              AND c.session_id = NEW.session_id
              AND c.candidate_id = NEW.candidate_id
              AND COALESCE(c.replacement_acceptance_id, '') = COALESCE(NEW.replacement_acceptance_id, '')
        )
        BEGIN SELECT RAISE(ABORT, 'D1b challenge replacement binding rejected'); END
        """
    )


def downgrade() -> None:
    raise RuntimeError("D1b downgrade is not lossless; restore the verified pre-upgrade backup")
