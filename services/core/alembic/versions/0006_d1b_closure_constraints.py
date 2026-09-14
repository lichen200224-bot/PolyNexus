"""D1b closure, acceptance provenance and concurrency constraints.

The first D1b migration created the immutable graph.  This additive revision
binds an Accepted Result to the exact verification/view that was accepted and
adds database uniqueness guards for per-candidate revisions and one-to-one
portable hand-off records.  It does not rewrite or delete historical rows.
"""
from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evidence_sets", sa.Column("trusted_runner_ref", sa.String(256), nullable=True))
    op.add_column("human_challenges", sa.Column("policy_revision", sa.Integer(), nullable=True))
    # A-LP decision closure is nullable only for legacy 0005 rows.  The
    # insert trigger below makes the fields mandatory for every new decision
    # without guessing trust facts for historical data.
    op.add_column("human_decision_events", sa.Column("trust_scope", sa.String(64), nullable=True))
    op.add_column("human_decision_events", sa.Column("auth_method", sa.String(64), nullable=True))
    op.add_column("human_decision_events", sa.Column("protocol_evidence_json", sa.Text(), nullable=True))
    op.add_column(
        "accepted_results",
        sa.Column("verification_id", sa.String(80), nullable=True),
    )
    op.add_column(
        "accepted_results",
        sa.Column("evidence_set_id", sa.String(80), nullable=True),
    )
    op.add_column("accepted_results", sa.Column("policy_revision", sa.Integer(), nullable=True))
    op.add_column("accepted_results", sa.Column("view_digest", sa.String(80), nullable=True))
    # SQLite cannot ALTER an existing table with a new FK constraint.  The
    # insert trigger below enforces this candidate-scoped closure edge.
    op.add_column("verification_records", sa.Column("requirements_snapshot_id", sa.String(80), nullable=True))
    op.add_column("verification_records", sa.Column("policy_revision", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("verification_records", sa.Column("verifier_principal", sa.String(256), nullable=False, server_default="core"))
    op.add_column("verification_records", sa.Column("verifier_type", sa.String(64), nullable=False, server_default="CORE_TRUSTED_RUNNER"))
    op.add_column("verification_records", sa.Column("environment_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("verification_records", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("verification_records", sa.Column("completed_at", sa.DateTime(), nullable=True))
    op.create_index(
        "uq_assurance_candidate_revision",
        "assurance_assessments",
        ["candidate_id", "revision"],
        unique=True,
    )
    op.create_index(
        "uq_human_decision_candidate_revision",
        "human_decision_events",
        ["candidate_id", "revision"],
        unique=True,
    )
    op.create_index(
        "uq_accepted_candidate_decision",
        "accepted_results",
        ["candidate_id", "accept_decision_id"],
        unique=True,
    )
    op.create_index(
        "uq_worktree_acceptance_candidate",
        "accepted_managed_worktrees",
        ["acceptance_id", "candidate_id"],
        unique=True,
    )
    op.create_index(
        "uq_p0_acceptance_candidate",
        "p0_packages",
        ["acceptance_id", "candidate_id"],
        unique=True,
    )
    # SQLite cannot add composite foreign keys to the already-created
    # immutable tables without rebuilding them.  These insert-time triggers
    # preserve the same referential-integrity boundary for the additive
    # revision, including the candidate-scoped edges that ordinary FKs cannot
    # express.
    op.execute(
        """
        CREATE TRIGGER d1b_decision_reference_binding
        BEFORE INSERT ON human_decision_events
        WHEN NOT EXISTS (
            SELECT 1 FROM human_challenges c
            WHERE c.challenge_id = NEW.challenge_id
              AND c.session_id = NEW.session_id
              AND c.candidate_id = NEW.candidate_id
              AND c.action = NEW.action
              AND c.view_digest = NEW.view_digest
        )
        OR (NEW.action = 'Accept' AND (NEW.acceptance_id IS NULL OR NEW.prior_acceptance_id IS NOT NULL OR NEW.replacement_acceptance_id IS NOT NULL))
        OR (NEW.action <> 'Accept' AND NEW.acceptance_id IS NOT NULL)
        OR NEW.trust_scope IS NULL
        OR NEW.auth_method IS NULL
        OR NEW.protocol_evidence_json IS NULL
        OR (NEW.action = 'Revoke' AND NOT EXISTS (
            SELECT 1 FROM accepted_results a
            WHERE a.acceptance_id = NEW.prior_acceptance_id
              AND a.candidate_id = NEW.candidate_id
        ))
        OR (NEW.action = 'Supersede' AND (
            NOT EXISTS (
                SELECT 1 FROM accepted_results a
                WHERE a.acceptance_id = NEW.prior_acceptance_id
                  AND a.candidate_id = NEW.candidate_id
            )
             OR NOT EXISTS (
                 SELECT 1 FROM accepted_results a
                 WHERE a.acceptance_id = NEW.replacement_acceptance_id
                   AND EXISTS (
                       SELECT 1 FROM human_decision_events d
                       WHERE d.decision_id = a.accept_decision_id
                         AND d.action = 'Accept'
                         AND d.acceptance_id = a.acceptance_id
                   )
             )
             OR COALESCE((
                 SELECT p.task_id || ':' || p.generation_revision || ':' || p.run_id
                 FROM accepted_results a
                 LEFT JOIN candidate_publications p ON p.publication_id = a.publication_id
                 WHERE a.acceptance_id = NEW.prior_acceptance_id
             ), '') IS NOT COALESCE((
                 SELECT p.task_id || ':' || p.generation_revision || ':' || p.run_id
                 FROM accepted_results a
                 LEFT JOIN candidate_publications p ON p.publication_id = a.publication_id
                 WHERE a.acceptance_id = NEW.replacement_acceptance_id
             ), '')
         ))
        BEGIN SELECT RAISE(ABORT, 'D1b decision reference binding rejected'); END
        """
    )
    op.execute(
        """
        CREATE TRIGGER d1b_verification_evidence_binding
        BEFORE INSERT ON verification_records
        WHEN NOT EXISTS (
            SELECT 1 FROM evidence_sets e
            WHERE e.evidence_set_id = NEW.evidence_set_id
              AND e.candidate_id = NEW.candidate_id
              AND e.contract_id = NEW.contract_id
        )
        OR NOT EXISTS (
            SELECT 1 FROM candidates c
            WHERE c.candidate_id = NEW.candidate_id
              AND c.requirements_snapshot_id = NEW.requirements_snapshot_id
        )
        BEGIN SELECT RAISE(ABORT, 'D1b verification evidence binding rejected'); END
        """
    )
    op.execute(
        """
        CREATE TRIGGER d1b_evidence_contract_binding
        BEFORE INSERT ON evidence_sets
        WHEN NOT EXISTS (
            SELECT 1 FROM candidates c
            WHERE c.candidate_id = NEW.candidate_id
              AND c.validation_contract_snapshot_id = NEW.contract_id
        )
        BEGIN SELECT RAISE(ABORT, 'D1b evidence contract binding rejected'); END
        """
    )
    op.execute(
        """
        CREATE TRIGGER d1b_assurance_binding
        BEFORE INSERT ON assurance_assessments
        WHEN (NEW.verification_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM verification_records v
            WHERE v.verification_id = NEW.verification_id
              AND v.candidate_id = NEW.candidate_id
              AND (NEW.evidence_set_id IS NULL OR v.evidence_set_id = NEW.evidence_set_id)
        ))
        OR (NEW.evidence_set_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM evidence_sets e
            WHERE e.evidence_set_id = NEW.evidence_set_id
              AND e.candidate_id = NEW.candidate_id
        ))
        OR NEW.target_type <> 'CANDIDATE'
        OR NEW.target_id <> NEW.candidate_id
        BEGIN SELECT RAISE(ABORT, 'D1b assurance binding rejected'); END
        """
    )
    op.execute(
        """
        CREATE TRIGGER d1b_publication_scope_binding
        BEFORE INSERT ON candidate_publications
        WHEN ((NEW.task_id IS NULL) != (NEW.generation_revision IS NULL))
          OR ((NEW.task_id IS NULL) != (NEW.run_id IS NULL))
          OR (NEW.task_id IS NOT NULL AND NOT EXISTS (
              SELECT 1 FROM runs r
              WHERE r.id = NEW.run_id
                AND r.task_id = NEW.task_id
                AND r.generation_revision = NEW.generation_revision
          ))
        BEGIN SELECT RAISE(ABORT, 'D1b publication scope binding rejected'); END
        """
    )
    op.execute(
        """
        CREATE TRIGGER d1b_accepted_result_binding
        BEFORE INSERT ON accepted_results
        WHEN NOT EXISTS (
            SELECT 1 FROM human_decision_events d
            WHERE d.decision_id = NEW.accept_decision_id
              AND d.candidate_id = NEW.candidate_id
              AND d.action = 'Accept'
              AND d.acceptance_id = NEW.acceptance_id
        )
        OR NEW.verification_id IS NULL
        OR NEW.evidence_set_id IS NULL
        OR NEW.policy_revision IS NULL
        OR NEW.view_digest IS NULL
        OR NOT EXISTS (
            SELECT 1 FROM verification_records v
            WHERE v.verification_id = NEW.verification_id
              AND v.candidate_id = NEW.candidate_id
              AND v.evidence_set_id = NEW.evidence_set_id
        )
        OR (NEW.publication_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM candidate_publications p
            WHERE p.publication_id = NEW.publication_id
              AND p.candidate_id = NEW.candidate_id
        ))
        BEGIN SELECT RAISE(ABORT, 'D1b accepted result binding rejected'); END
        """
    )
    op.execute(
        """
        CREATE TRIGGER d1b_worktree_acceptance_binding
        BEFORE INSERT ON accepted_managed_worktrees
        WHEN NOT EXISTS (
            SELECT 1 FROM accepted_results a
            WHERE a.acceptance_id = NEW.acceptance_id
              AND a.candidate_id = NEW.candidate_id
        )
        BEGIN SELECT RAISE(ABORT, 'D1b worktree binding rejected'); END
        """
    )
    op.execute(
        """
        CREATE TRIGGER d1b_p0_acceptance_binding
        BEFORE INSERT ON p0_packages
        WHEN NOT EXISTS (
            SELECT 1 FROM accepted_results a
            WHERE a.acceptance_id = NEW.acceptance_id
              AND a.candidate_id = NEW.candidate_id
        )
        BEGIN SELECT RAISE(ABORT, 'D1b p0 package binding rejected'); END
        """
    )


def downgrade() -> None:
    raise RuntimeError("D1b downgrade is not lossless; restore the verified pre-upgrade backup")
