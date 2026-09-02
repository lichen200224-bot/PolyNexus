# ADR-012 — Runtime Doctor / Capability / Version Matrix Reporting

## Status

`HUMAN_ACCEPTED / IMPLEMENTATION_AUTHORIZED` — 2026-08-27

This decision authorizes only the bounded WP-16 Core-only Doctor MVP described
below. It does not authorize API, UI, database, migration, dependency,
ExecutionService, supervisor, domain, persistence, commit, push, or WP-16
follow-up work outside the stated allowlists.

## Context

The Runtime Registry and deterministic Codex/OpenCode conformance adapters now
provide enough identity and adapter-level evidence for a read-only inventory
report. The existing product default registry must remain reference-only until
a separate integration decision changes that boundary. A Doctor therefore
needs its own composition root and must not become an implicit execution
routing mechanism or a real vendor-runtime detector.

## Decision

WP-16 v1 is a deterministic, Core-only Doctor report. It has no API, UI, DB,
migration, network, credentials, real vendor CLI, or durable persistence
surface.

### Composition root and inventory

- `runtime/doctor.py` owns an immutable ordered tuple of
  `DoctorRuntimeSpec` values.
- `build_default_doctor()` creates a private, fresh `RuntimeRegistry` for each
  report collection. It does not call or modify `build_default_registry()`.
- Inventory rows are registered explicitly in this order:
  `reference.local`, `conformance.codex.local`, and
  `conformance.opencode.local`.
- The Doctor does not add a general Registry enumeration contract. Its
  inventory is explicit and owned by the Doctor composition root.
- Inventory duplicates, conflicts, malformed profiles, invalid evidence, and
  non-callable factories fail closed as `FAILED` with no entries.

### Report authority

Each `DoctorRuntimeEntry` reports:

- identity: provider, transport, runtime, adapter, execution target, profile
  reference, and profile revision;
- `health` and `readiness` from current asynchronous probes, each marked
  `CURRENT_PROBE`;
- `adapter_version` from `RuntimeAdapter.version_info()`, marked
  `ADAPTER_DECLARATION`;
- `runtime_version` as `None` with source `UNAVAILABLE` when no distinct
  runtime version is detected;
- `capabilities` from `RuntimeAdapter.capabilities()`, marked
  `ADAPTER_DECLARATION`;
- `maturity`, `evidence_source`, and separate conformance evidence containing
  outcome, scope, checkpoint, and test source;
- one fixed public-safe `error_category`, when a row is partial.

`COMPLETE` means that the report was collected without an inventory or probe
error; it does not mean that every runtime is healthy. A valid `False` health
or readiness probe remains a complete report with a truthful unhealthy value.

### Maturity policy

- `reference.local` is `SUPPORTED` only within the explicit
  `DETERMINISTIC_REFERENCE_RUNTIME` scope.
- Codex and OpenCode rows are `EXPERIMENTAL`, scoped to
  `DETERMINISTIC_LOCAL_CONFORMANCE`.
- Codex and OpenCode are not `PREVIEW`, `SUPPORTED`, `CERTIFIED`, or detected
  production runtimes. Their report evidence cannot be read as real vendor
  CLI availability.
- Capabilities are adapter declarations; conformance evidence is a separate
  field and never upgrades current health/readiness.

### Failure and secrecy policy

- Factory failure produces an unavailable row with `FACTORY_FAILURE`; other
  rows continue and no reference fallback is attempted.
- Health/readiness timeout uses a bounded `asyncio.wait_for()` probe; the
  timed-out operation is cancelled and the row reports `PROBE_TIMEOUT`.
- Health, readiness, capability, version, and timestamp exceptions produce
  fixed categories and `None` values where applicable. Raw exception objects,
  messages, args, causes, contexts, and tracebacks are never placed in a
  report.
- A row error makes the overall report `PARTIAL`; invalid inventory makes it
  `FAILED` with an empty entry tuple.

## Fixed default evidence

The default conformance evidence points to the accepted integration
checkpoint `65c6582c70c4e724005adb983d65aba10ea3e8be` and the corresponding
deterministic test source. These references describe evidence scope only; they
do not authorize Git operations or claim production vendor support.

## Scope and allowlists

### Architecture-record allowlist

- `docs/31_ADR_012_RUNTIME_DOCTOR_REPORTING.md`
- `docs/10_DECISION_LOG.md`
- `docs/tasks/WP-16.md`

### Implementation allowlist (original WP-16 scope)

- `services/core/src/polynexus_core/runtime/doctor.py`
- `services/core/tests/test_wp16_runtime_doctor.py`
- `docs/tasks/WP-16.md`

### Explicit exclusions for original WP-16 v1

`runtime/contracts.py`, `runtime/registry.py`, `ExecutionService`,
`supervisor`, `domain`, `persistence`, API, UI, DB, migrations, dependencies,
`docs/11_PROJECT_STATE.md`, and `docs/12_HANDOFF_CURRENT.md` remain outside
this decision and must not be modified for WP-16 v1.

## G25 integration addendum — 2026-09-02

The combined G25 lane explicitly supersedes the original WP-16 implementation
exclusion only for `runtime/registry.py` and the new
`runtime/doctor_legacy.py` compatibility module. The G25 implementation
allowlist is therefore the union of the original WP-16 files plus those two
bounded integration files and the G25 control-panel/ledger documents recorded
in `docs/12_HANDOFF_CURRENT.md`. `RuntimeRegistry.create_adapter()` keeps its
normal execution-time capability/auth validation; the observation path is used
only so Doctor can report declaration/probe failures separately from factory
failures. This does not alter the frozen RuntimeAdapter Protocol, default
execution registry, persistence schema, Alembic authority, Run identity, or
maturity policy. The addendum is limited to G25 review and Human acceptance.

## Rollback and acceptance gates

Rollback is a file-level revert of the original WP-16 implementation/record
files plus the two bounded G25 integration seams and current G25 evidence/docs,
leaving the accepted `65c6582...` integration checkpoint untouched. The exact
combined allowlist is recorded in the G25 handoff; no unrelated files may be
staged.
No migration or data rollback is needed because the MVP has no persistence.

Independent Codex review must verify the exact allowlist, protected-path
absence, fixed inventory, no default-registry mutation, sanitized partial and
failed reports, timeout cancellation, truthful maturity, and the required
targeted/regression/validator exit codes. Human acceptance remains separate
from implementation review; stage, commit, and named-ref push are separate
Human Git gates.
