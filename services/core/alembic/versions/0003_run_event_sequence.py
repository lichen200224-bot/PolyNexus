"""Durable per-Run append sequence; legacy rowid is reconstruction, not causal proof.

Revision ID: 0003
Revises: 0002
Downgrade preserves event facts but loses ordering metadata. Back up before upgrade
and before any downgrade; restore with compatible code and writers stopped.
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

_FACTS = "id, run_id, from_state, to_state, occurred_at, reason"
_BASE_COLUMNS = """
    id VARCHAR(64) NOT NULL PRIMARY KEY,
    run_id VARCHAR(64) NOT NULL REFERENCES runs(id),
    from_state VARCHAR(32) NOT NULL,
    to_state VARCHAR(32) NOT NULL,
    occurred_at DATETIME NOT NULL,
    reason TEXT
"""


def _verify_facts(conn):
    for left, right in [("run_events", "run_events_0003_copy"),
                        ("run_events_0003_copy", "run_events")]:
        count = conn.exec_driver_sql(f"SELECT COUNT(*) FROM {left}").scalar_one()
        other = conn.exec_driver_sql(f"SELECT COUNT(*) FROM {right}").scalar_one()
        changed = conn.exec_driver_sql(
            f"SELECT {_FACTS} FROM {left} EXCEPT SELECT {_FACTS} FROM {right}"
        ).first()
        if count != other or changed is not None:
            raise RuntimeError("Event migration changed legacy facts")


def _replace_table(conn):
    _verify_facts(conn)
    conn.exec_driver_sql("DROP TABLE run_events")
    conn.exec_driver_sql("ALTER TABLE run_events_0003_copy RENAME TO run_events")


def upgrade():
    conn = op.get_bind()
    if conn.dialect.name != "sqlite":
        raise RuntimeError("SEQUENCE_ALLOCATOR_ARCHITECTURE_CONFLICT")
    # SAVEPOINT makes DDL and data changes rollback together even under SQLite's
    # legacy driver transaction mode. No migration of real databases is implicit.
    with conn.begin_nested():
        conn.exec_driver_sql(
            "ALTER TABLE runs ADD COLUMN next_event_sequence INTEGER NOT NULL DEFAULT 0"
        )
        conn.exec_driver_sql(
            "CREATE TABLE run_events_0003_copy (" + _BASE_COLUMNS + ","
            "event_sequence INTEGER NOT NULL, "
            "sequence_legacy_backfill BOOLEAN NOT NULL DEFAULT 0, "
            "CONSTRAINT uq_run_events_sequence UNIQUE(run_id, event_sequence), "
            "CONSTRAINT ck_run_events_sequence_positive CHECK(event_sequence > 0))"
        )
        conn.exec_driver_sql(
            f"INSERT INTO run_events_0003_copy(rowid, {_FACTS}, event_sequence, sequence_legacy_backfill) "
            f"SELECT rowid, {_FACTS}, ROW_NUMBER() OVER(PARTITION BY run_id ORDER BY rowid), 1 "
            "FROM run_events ORDER BY rowid"
        )
        # MAX is used only for the approved one-time migration high-water mark,
        # never as a concurrent append allocator.
        conn.exec_driver_sql(
            "UPDATE runs SET next_event_sequence = COALESCE(("
            "SELECT MAX(event_sequence) FROM run_events_0003_copy e WHERE e.run_id=runs.id), 0)"
        )
        invalid = conn.exec_driver_sql(
            "SELECT run_id FROM run_events_0003_copy GROUP BY run_id "
            "HAVING MIN(event_sequence) != 1 OR MAX(event_sequence) != COUNT(*) "
            "OR COUNT(DISTINCT event_sequence) != COUNT(*) "
            "OR COUNT(event_sequence) != COUNT(*) "
            "OR MIN(sequence_legacy_backfill) != 1"
        ).first()
        orphan = conn.exec_driver_sql(
            "SELECT 1 FROM run_events_0003_copy e LEFT JOIN runs r ON e.run_id=r.id WHERE r.id IS NULL"
        ).first()
        bad_counter = conn.exec_driver_sql(
            "SELECT 1 FROM runs r WHERE next_event_sequence != COALESCE(("
            "SELECT MAX(event_sequence) FROM run_events_0003_copy e WHERE e.run_id=r.id),0)"
        ).first()
        if invalid or orphan or bad_counter:
            raise RuntimeError("Event sequence backfill inconsistent")
        _replace_table(conn)
        conn.exec_driver_sql(
            "CREATE TRIGGER trg_run_events_sequence_immutable "
            "BEFORE UPDATE OF run_id, event_sequence, sequence_legacy_backfill ON run_events "
            "WHEN NEW.run_id IS NOT OLD.run_id OR NEW.event_sequence IS NOT OLD.event_sequence "
            "OR NEW.sequence_legacy_backfill IS NOT OLD.sequence_legacy_backfill "
            "BEGIN SELECT RAISE(ABORT, 'Run event ordering metadata is immutable'); END"
        )


def downgrade():
    conn = op.get_bind()
    with conn.begin_nested():
        conn.exec_driver_sql("CREATE TABLE run_events_0003_copy (" + _BASE_COLUMNS + ")")
        conn.exec_driver_sql(
            f"INSERT INTO run_events_0003_copy(rowid, {_FACTS}) "
            f"SELECT rowid, {_FACTS} FROM run_events ORDER BY rowid"
        )
        _replace_table(conn)
        conn.exec_driver_sql("ALTER TABLE runs DROP COLUMN next_event_sequence")
