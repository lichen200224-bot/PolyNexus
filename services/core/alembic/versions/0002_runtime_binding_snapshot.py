"""runtime binding snapshots

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-25

Run-owned immutable RuntimeBindingSnapshot table (ADR-011 / PRE-WP14-B).

upgrade():
  - creates ``run_binding_snapshots`` (1:1 with runs, PK = run_id FK, no cascade)
  - adds a fail-closed Run-delete guard trigger on ``runs`` (Run deletion is
    rejected at the database level so no orphan snapshot can ever exist)
  - deterministically backfills every existing 0001-era Run with the approved
    legacy/reference identity:
        provider_id      = 'polynexus'
        transport_kind   = 'LOCAL'
        runtime_id       = 'reference'
        adapter_id       = 'builtin.reference'
        execution_target = existing runs.execution_target
        runtime_profile_ref / profile_revision / adapter_version / secret_ref_id = NULL
        legacy_backfill  = true
        snapshot_schema_version = 1
        auth_ownership   = 'NONE'
        usage_visibility = 'UNAVAILABLE'
        resolved_at      = earliest STARTING run_event timestamp for the Run
                           (deterministic tie-break: earliest event id),
                           falling back to runs.created_at when no STARTING event exists.
    These identities record that a Run predates runtime binding; they are NOT
    claims about what was actually resolved at execution time.

downgrade():
  - removes only what this revision created (indexes + table).
  - existing runs/tasks/events/evidence history and 0001 semantics are untouched.

This migration must only ever run against temporary/isolated test databases
or explicitly Human-approved targets. It imports no vendor adapter, executes
no Registry/SecretStore code, and never uses current system time as identity.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "run_binding_snapshots"

_PROVIDER_ID = "polynexus"
_TRANSPORT_KIND = "LOCAL"
_RUNTIME_ID = "reference"
_ADAPTER_ID = "builtin.reference"
_SNAPSHOT_SCHEMA_VERSION = 1
_AUTH_OWNERSHIP = "NONE"
_USAGE_VISIBILITY = "UNAVAILABLE"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.id"), primary_key=True),
        sa.Column("provider_id", sa.String(64), nullable=False),
        sa.Column("transport_kind", sa.String(32), nullable=False),
        sa.Column("runtime_id", sa.String(64), nullable=False),
        sa.Column("adapter_id", sa.String(64), nullable=False),
        sa.Column("execution_target", sa.String(32), nullable=False),
        sa.Column("runtime_profile_ref", sa.String(64), nullable=True),
        sa.Column("profile_revision", sa.Integer, nullable=True),
        sa.Column("adapter_version", sa.String(64), nullable=True),
        sa.Column("resolved_at", sa.DateTime, nullable=False),
        sa.Column("legacy_backfill", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("snapshot_schema_version", sa.Integer, nullable=False),
        sa.Column("auth_ownership", sa.String(32), nullable=False),
        sa.Column("secret_ref_id", sa.String(64), nullable=True),
        sa.Column("usage_visibility", sa.String(32), nullable=False),
    )
    op.create_index(
        "ix_run_binding_snapshots_provider_id", _TABLE, ["provider_id"]
    )
    op.create_index(
        "ix_run_binding_snapshots_transport_kind", _TABLE, ["transport_kind"]
    )

    # Database-level immutability guard: rejects UPDATE/DELETE even when they
    # bypass the ORM (bulk operations, raw SQL). Mirrors the create_all path.
    op.execute(
        "CREATE TRIGGER trg_rbs_reject_update "
        "BEFORE UPDATE ON run_binding_snapshots "
        "BEGIN SELECT RAISE(ABORT, "
        "'RuntimeBindingSnapshot rows are immutable'); END"
    )
    op.execute(
        "CREATE TRIGGER trg_rbs_reject_delete "
        "BEFORE DELETE ON run_binding_snapshots "
        "BEGIN SELECT RAISE(ABORT, "
        "'RuntimeBindingSnapshot rows are immutable'); END"
    )

    # Run deletion is fail-closed at the database level: a Run owns its
    # binding snapshot 1:1 forever. Deleting the Run row would orphan the
    # immutable snapshot, so Run deletion is rejected outright — regardless
    # of whether FK enforcement is enabled. Mirrors the create_all path.
    op.execute(
        "CREATE TRIGGER trg_runs_reject_delete "
        "BEFORE DELETE ON runs "
        "BEGIN SELECT RAISE(ABORT, "
        "'Run rows are protected: run deletion is not permitted'); END"
    )

    conn = op.get_bind()

    # Deterministic legacy/reference backfill for all pre-0002 Runs.
    # resolved_at: earliest STARTING event per Run with deterministic
    # tie-break by event id; falls back to runs.created_at.
    conn.execute(
        sa.text(
            f"""
            INSERT INTO {_TABLE} (
                run_id, provider_id, transport_kind, runtime_id, adapter_id,
                execution_target, runtime_profile_ref, profile_revision,
                adapter_version, resolved_at, legacy_backfill,
                snapshot_schema_version, auth_ownership, secret_ref_id,
                usage_visibility
            )
            SELECT
                r.id,
                :provider_id,
                :transport_kind,
                :runtime_id,
                :adapter_id,
                r.execution_target,
                NULL,
                NULL,
                NULL,
                COALESCE(
                    (
                        SELECT re.occurred_at
                        FROM run_events re
                        WHERE re.run_id = r.id AND re.to_state = 'STARTING'
                        ORDER BY re.occurred_at ASC, re.id ASC
                        LIMIT 1
                    ),
                    r.created_at
                ),
                1,
                :snapshot_schema_version,
                :auth_ownership,
                NULL,
                :usage_visibility
            FROM runs r
            """
        ),
        {
            "provider_id": _PROVIDER_ID,
            "transport_kind": _TRANSPORT_KIND,
            "runtime_id": _RUNTIME_ID,
            "adapter_id": _ADAPTER_ID,
            "snapshot_schema_version": _SNAPSHOT_SCHEMA_VERSION,
            "auth_ownership": _AUTH_OWNERSHIP,
            "usage_visibility": _USAGE_VISIBILITY,
        },
    )

    # Fail closed on any inconsistency: exactly one snapshot per Run.
    runs_count = conn.execute(sa.text("SELECT COUNT(*) FROM runs")).scalar_one()
    snapshots_count = conn.execute(
        sa.text(f"SELECT COUNT(*) FROM {_TABLE}")
    ).scalar_one()
    if snapshots_count != runs_count:
        raise RuntimeError(
            "Legacy backfill inconsistent: "
            f"{snapshots_count} snapshots for {runs_count} runs"
        )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_runs_reject_delete")
    op.execute("DROP TRIGGER IF EXISTS trg_rbs_reject_update")
    op.execute("DROP TRIGGER IF EXISTS trg_rbs_reject_delete")
    op.drop_index("ix_run_binding_snapshots_transport_kind", table_name=_TABLE)
    op.drop_index("ix_run_binding_snapshots_provider_id", table_name=_TABLE)
    op.drop_table(_TABLE)
