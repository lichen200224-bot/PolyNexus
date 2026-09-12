# ADR-014 — Durable Event Ordering and Cancellation Cleanup

Status: **HUMAN_ACCEPTED / IMPLEMENTATION_AUTHORIZED** (2026-09-12)
Task: BASELINE-DEBT-01. Independent implementation review remains required.

## Decision and boundaries

UUID identity and occurred_at timestamp do not establish lifecycle append order.
Persist `event_sequence` per Run: 1-based, strictly increasing, immutable after
persistence, representing durable append order. Canonical reads use
`ORDER BY run_id, event_sequence`. It is not wall-clock time, is not derived from
UUID, does not replace occurred_at, and survives reload/restart.

This metadata stays in persistence. Domain Run/RunEvent, RunState, lifecycle graph,
REST/workflow schema, runtime binding contracts and dependencies are unchanged.
Repository consumers receive correctly ordered `Run.events` without new fields.
No G30, WP-20 or score change is authorized by this decision.

## Atomic allocation

`runs.next_event_sequence INTEGER NOT NULL DEFAULT 0` is the allocated high-water
mark, not a Domain Run property. For N new events, one database atomic statement
updates `next_event_sequence = next_event_sequence + N WHERE id = :run_id
RETURNING next_event_sequence`; assign high-N+1 through high in append-list order
within the same transaction. Concurrent sessions serialize allocation in SQLite.
A missing Run fails closed. No MAX()+1 allocator is permitted.
Ordinary RunRepository.update explicitly excludes the counter from column copying.

`run_events.event_sequence INTEGER NOT NULL` and
`sequence_legacy_backfill BOOLEAN NOT NULL DEFAULT FALSE` accompany a unique
(run_id,event_sequence) constraint, whose composite SQLite index supports reads.
A positive-sequence check and immutable metadata trigger add database guards.
The tested SQLite/SQLAlchemy environment supports atomic RETURNING. Unsupported
allocation must fail rather than fall back to a race-prone allocator.

## Migration 0003 and historical truthfulness

`0003_run_event_sequence.py` follows revision `0002`. On SQLite, the approved
legacy anchor is physical insertion rowid: ROW_NUMBER() OVER (PARTITION BY run_id
ORDER BY rowid). Existing events receive sequence_legacy_backfill=TRUE; newly
appended events receive FALSE. This is historical persistence insertion-order
reconstruction, not event-time proof, causal-time certification, or vendor/runtime
execution evidence. Original id, run_id, state, timestamp and reason remain intact;
timestamps are never rewritten to impose order.

Upgrade uses a savepoint and verifies row counts, original facts in both directions,
non-null unique contiguous sequences starting at 1, all legacy flags, and each
Run counter equal to its event maximum (0 for empty Runs). Inconsistency aborts
and rolls back, with no silent repair. MAX is used only to initialize migration
high-water marks, never for runtime allocation.

Downgrade preserves original event rows/facts and removes only 0003 ordering
metadata and constraints. It leaves other tables and RuntimeBindingSnapshot
untouched. It loses sequence metadata, not events. Physical rowid is retained
through table replacement so re-upgrade is deterministic. Events added after
0003 become legacy backfill on re-upgrade, because downgrade discarded their
metadata; this is explicitly not recovery of their former provenance flag.

Before an approved deployment, take a restorable SQLite backup and prevent
concurrent application writes. On failure retain the original database and error;
restore from the backup if an operational interruption prevents normal rollback.
This task migrates isolated test databases only; production rollout is not claimed.
Upgrade→downgrade→re-upgrade and injected failure rollback are regression-tested.

## Cleanup timeout and cancellation

Normal operation timeout and `_DEFAULT_CLEANUP_TIMEOUT_SECONDS` are independent
internal policies, each currently 30 seconds. Cancel, cleanup and status verification
use cleanup policy with count_budget=False. Tests synchronize at an Event/blocking
point before exercising a bounded deadline; timeout values do not synchronize setup.

External CancelledError with a known runtime_ref transitions STARTING/RUNNING to
CANCEL_REQUESTED, performs protected cancel/cleanup/status verification, then
CANCELLED only if cleanup is verified. False return, exception, timeout, mismatch
or inability to verify yields ORPHANED. Cancellation before a known reference
also yields CANCEL_REQUESTED→ORPHANED: possible allocation cannot be certified safe.

Cleanup runs in a shielded task with per-call and aggregate cleanup deadlines.
Repeated caller cancellation cannot directly cancel verification and conservatively
produces ORPHANED, never a false CANCELLED. The original CancelledError is re-raised;
there is no normal success response or fabricated Result/Finding/Evidence/Artifact.
No new RunState or lifecycle transition is introduced.

ExecutionService catches the propagated cancellation only to sanitize and persist
the updated Run/events and commit, then re-raises. Persistence failure rolls back
and propagates the failure; no durable cleanup-state claim is made in that case.
Reopen tests cover all three service execution entry points.
