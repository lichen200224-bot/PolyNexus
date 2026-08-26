# Runtime Contract Foundation Gate — Pre-WP14

- Status: `PRE-WP14-A IMPLEMENTATION_ACCEPTED @ 28196c9 / PRE-WP14-B HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED (checkpoint SHA recorded after commit)`
- Architecture decision status: `ADR-011 HUMAN_ACCEPTED` (decision text unchanged); ADR-001～010 frozen
- Sub-gate A (ADR-007 timeout cleanup): `HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED` at checkpoint `28196c9`
- Sub-gate B (Runtime Binding contract): `HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED`; Human approved the bounded 15-file implementation allowlist, fresh independent Codex returned `VERIFIED_PASS`, and the exact-allowlist Git checkpoint is in progress. Alembic `0002`, Run-owned immutable RuntimeBindingSnapshot persistence/reload, legacy backfill and mutation rejection are implemented and accepted within this bounded gate.
- Gate type: Architecture and contract gate
- Implementation Writer: OpenCode
- Required Reviewer: fresh independent Codex context; Writer != Reviewer is mandatory
- Decision and Git authority: Human
- Accepted ADR: `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`
- Existing authority: ADR-007 and ADR-010 remain frozen

## 1. Purpose

This gate prevents WP-14/WP-15 production Runtime work from being built on an identity, credential, capability, or timeout-cleanup contract that cannot represent future official Subscription and API Runtimes.

This gate document itself does not authorize production execution, migration against real/user databases, or Git operations; decision and Git authority remain with Human.

(Historical planning statement, pre-implementation preparation phase — SUPERSEDED by the later Human-approved PRE-WP14-B implementation allowlist: "It does not implement Runtime Binding, Registry, SecretStore, migrations, APIs, UI, or vendor Adapters. It does not change WP-13 scope or status." PRE-WP14-B Runtime Binding is now implemented in the working tree under that approved allowlist and is `IMPLEMENTED_PENDING_INDEPENDENT_REVIEW`; WP-13 scope/status remains unchanged.)

## 2. Verified current implementation

Pre-PRE-WP14-B baseline (historical snapshot as of the PRE-WP14-A accepted checkpoint `28196c9705e688ee05c0bb4703cdf5b254d400c6`; superseded where PRE-WP14-B is implemented below):

- `RunSupervisor` accepts a generic `RuntimeAdapter` and owns normalized Run lifecycle.
- `ExecutionService` constructs `ReferenceRuntimeAdapter` directly.
- `Run` and `RunRow` store `execution_target`, `resume_mode`, and opaque `runtime_ref` only.
- `ExecutionTarget` contains `LOCAL`; `ResumeMode` contains `NATIVE`, `MANAGED`, and `NONE`.
- `RuntimeCapabilities` declares only cancel, resume, and artifacts.
- API Run creation accepts only `context_package_id`.
- Workflow nodes are vendor-neutral, but step additional properties are not a Runtime Binding contract.
- No implemented Provider, TransportKind, RuntimeProfile, RuntimeBindingSnapshot, Adapter Registry, SecretRef/SecretStore, or managed CLI process abstraction exists.
- Existing tests are Reference Runtime-centric and assert the current `LOCAL/NONE` default.
- PRE-WP14-A implemented: timeout paths (`execute_claimed_run()` / `execute_run()` / `collect()`) and user cancel share one `_cleanup_and_verify(runtime_ref, expected_state)` machinery — adapter cancel -> cleanup -> post-cleanup status must return exactly `{TIMED_OUT}` (timeout) or `{CANCELLED}` (cancel) with `cleanup=True`; any exception or mismatch inside this shared boundary fails closed via CANCEL_REQUESTED -> ORPHANED with sanitized constant reasons; timeout success is a direct RUNNING -> TIMED_OUT transition.
- PRE-WP14-A sanitization evidence scope (boundary-only): the shared `_cleanup_and_verify()` cancel/cleanup/post-cleanup-status exception containment, timeout/cancel `status.error` sanitization to constant reasons, and no PASS evidence for TIMED_OUT/ORPHANED executions. Generic workflow-executor exception handling elsewhere in `execute_run()` (the workflow-executor try/except persists `str(exc)` as the event reason and re-raises) is pre-existing behavior, unchanged by PRE-WP14-A, and NOT covered by its evidence.
- PRE-WP14-B implemented (current, Attempt 4, independently verified and Human-accepted): every executed Run — both `execute_existing_run()` and `execute_task()` — resolves its profile through the Runtime Registry and persists an immutable Run-owned `RuntimeBindingSnapshot` (`run_binding_snapshots`, PK run_id FK→runs.id, no cascade) in the same transaction that claims the Run and appends CREATED→STARTING — before any adapter invocation; a probe test reads through an independent connection at the adapter's first observable point to prove commit ordering. Duplicate insert / repository update/delete / ORM mutation / bulk Query.update()-delete() / direct raw SQL are ALL rejected fail-closed via SQLite triggers plus mapper listeners and repository guards; unknown snapshot schema versions and auth-ownership/secret-ref mismatches fail closed on reload; binding failures roll back completely with zero adapter construction. Alembic `0002` deterministically backfills pre-existing Runs with the legacy/reference identity (earliest STARTING event timestamp, id tie-break, fallback runs.created_at) and installs the same immutability triggers; the migration-installed database additionally rejects all Run deletion paths via `trg_runs_reject_delete`, dynamically verified across upgrade/downgrade/re-upgrade. Adapter factory construction failure after the binding commit legally transitions STARTING → FAILED with a sanitized reason/event. Binding error messages never echo caller-supplied identifier material.

These are `CURRENT IMPLEMENTATION` facts, not statements that accepted architecture capabilities already exist.

## 3. Gate split

The Foundation Gate has two independent sub-gates. Neither may be hidden inside the other.

### PRE-WP14-A. ADR-007 Timeout Cleanup Compliance — `ACCEPTED`

Status: `HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED` at checkpoint `28196c9`.

Goal: prove the existing ADR-007 requirement for every real process/session Runtime.

Required contract sequence:

```text
timeout detection
  -> cancel/terminate the owned work
  -> cleanup child/tool/process/resource tree
  -> verify cleanup
  -> record a truthful legal final state and evidence
```

Acceptance requirements (all implemented and independently reviewed):

1. Timeout uses the same cleanup machinery and verification standard as cancel. — DONE: shared `_cleanup_and_verify()`.
2. A Run is not reported as cleanly timed out until cleanup is verified. — DONE: post-cleanup status must be exactly `TIMED_OUT`; otherwise fail closed.
3. Cleanup failure produces the existing diagnostic behavior (`ORPHANED` through a legal lifecycle path) and never PASS evidence. — DONE: CANCEL_REQUESTED -> ORPHANED; no PASS evidence for TIMED_OUT/ORPHANED.
4. Raw vendor errors, process output, paths, tokens, and credentials are sanitized before durable persistence. — DONE within the PRE-WP14-A cleanup/cancel/timeout boundary only: shared `_cleanup_and_verify()` exception containment and timeout/cancel `status.error` sanitization to constant reasons; TIMED_OUT/ORPHANED produce no PASS evidence. This DONE does not extend to generic workflow-executor failure paths outside that boundary (pre-existing behavior, unchanged).
5. Deterministic fake-process/fake-resource tests prove success and cleanup-failure paths. — DONE: 17 tests in `test_runtime_skeleton.py`, including cancel-exception x3, wrong post-cleanup status x3, sanitization x2.
6. Adapter maturity cannot exceed the highest level supported by current cleanup evidence. — standing rule; unchanged.

### PRE-WP14-B. Runtime Binding Contract — `IMPLEMENTED_PENDING_INDEPENDENT_REVIEW`

Status: implemented by OpenCode under the Human-approved 15-file allowlist; Attempt 1 FAIL remediated; Attempt 2 independently reviewed by Codex with verdict FAIL (4 findings); Attempt 3 remediated Findings 1–3 and was reviewed with verdict FAIL on 3 new findings (false log-capture PASS label, missing migration-path trigger acceptance, stale docstring); Attempt 4 remediated all three within the same allowlist; fresh independent Codex re-review returned `VERIFIED_PASS`; Human accepted PRE-WP14-B on 2026-08-26; exact-allowlist Git checkpoint is in progress. Alembic `0002`, Run-owned immutable RuntimeBindingSnapshot persistence/reload, deterministic legacy backfill and ORM/repository mutation rejection are implemented and accepted within this bounded gate; Run deletion is additionally rejected fail-closed at the database level (`trg_runs_reject_delete` on `runs`, created by both create_all and Alembic 0002, dynamically verified on the migration-installed database across upgrade/downgrade/re-upgrade), and adapter factory construction failure after the binding commit legally transitions STARTING → FAILED with a sanitized reason/event instead of leaving the Run in STARTING. WP-14/WP-15 production adapter conformance remains out of scope.

Attempt 4 secret-exclusion coverage labels (detailed evidence table in `docs/tasks/PRE-WP14-B.md`): DB rows / events / evidence / artifacts / result_summary / persisted runtime error capture = PASS (exit code 0); application log capture = NOT_IN_SCOPE this round (no logging surface exists in the Core runtime source within this allowlist), UNVERIFIED; API response surface = NOT_IN_SCOPE this round (no API change in allowlist), UNVERIFIED; exports/handoff marker scan = NOT_IN_SCOPE (no such Core mechanism exists yet), UNVERIFIED. Persisted error capture and application log capture are distinct surfaces; only the former has deterministic evidence. NOT_IN_SCOPE surfaces are not claimed as verified.

Goal: approve a durable, vendor-neutral Runtime identity and resolution contract before production Adapter wiring.

Acceptance requirements:

1. Human acceptance of ADR-011 is explicitly recorded; it does not grant implementation or migration authority, and AI tools cannot self-promote task acceptance.
2. Provider, TransportKind, Runtime, Adapter, and ExecutionTarget have non-overlapping meanings.
3. `provider_id`, `runtime_id`, `adapter_id`, and profile identifiers use validated opaque identifiers rather than closed vendor enums.
4. `TransportKind` supports `LOCAL`, `NATIVE_SUBSCRIPTION`, `OFFICIAL_API`, and the boundary-only `WEB_INTERACTIVE` value.
5. RuntimeProfile is mutable intention/configuration; RuntimeBindingSnapshot is immutable resolved Run history.
6. Run-owned immutable snapshot persistence preserves the resolved identity without raw credentials; deterministic legacy/reference backfill and downgrade/restore are approved and verified within this bounded gate. (The contract criterion was written before implementation, when Alembic `0002` was still future; `0002` is now implemented and its lifecycle was independently verified on pytest temporary isolated databases.)
7. Runtime Registry/Adapter Factory selection replaces hard-coded Adapter construction without Core vendor branching.
8. Workflow selection, if approved, uses only `runtime_profile_ref`.
9. Auth ownership supports `RUNTIME_MANAGED`, `SECRET_REF`, `BROWSER_PROFILE_MANAGED`, and `NONE` without mixing credentials, permission, or data policy.
10. Capability contract includes cancel, resume, artifacts, timeout cleanup, usage visibility, and auth mode.
11. Usage visibility is `UNAVAILABLE`, `ESTIMATED`, or `EXACT`; precise usage is never fabricated.
12. WebSurface remains separate from official API and Runtime execution semantics.

## 4. Planned implementation impact after approval (HISTORICAL / SUPERSEDED planning state)

Historical planning analysis from the pre-implementation preparation phase. The implementation allowlist has since been Human-approved and executed (PRE-WP14-B, 15 files); this list is retained only as impact-analysis history and grants no permission by itself:

- Domain identity/value objects and Run snapshot.
- Runtime contract descriptor/capabilities.
- Registry/factory wiring.
- Run persistence/repository plus a real Alembic migration and old-data policy.
- Run API DTOs and selection contract.
- Generic workflow profile reference only if required by an approved use case.
- SecretRef/auth-ownership compatibility only where required; a new SecretStore implementation is not automatically authorized.
- Managed CLI process lifecycle/cleanup abstraction.
- Deterministic contract, persistence, migration, API, and conformance tests.

## 5. Test and acceptance matrix for the implementation gate (contract criteria; PRE-WP14-B evidence labeled inline)

| Area | Required evidence |
|---|---|
| Identity | Same Provider with multiple Transports remains distinguishable; Provider never implies Runtime |
| Persistence | Binding snapshot survives session close/reopen and upgrade/downgrade/re-upgrade lifecycle |
| Legacy data | Existing Runs receive an explicit deterministic legacy/reference identity or a documented fail-closed migration result |
| Registry | Profile resolves to the expected Adapter without `if provider == ...` branches |
| Auth | Raw credential/Cookie/Session markers are rejected or absent from DB, Event, Evidence, Artifact, API, log, export, and handoff. PRE-WP14-B Attempt 4 evidence: DB/Event/Evidence/Artifact/result_summary/persisted-runtime-error-capture PASS; application log capture NOT_IN_SCOPE/UNVERIFIED (no logging surface in this gate); API surface NOT_IN_SCOPE/UNVERIFIED (no API change this round); export/handoff scan NOT_IN_SCOPE/UNVERIFIED until such mechanisms exist |
| Cancel | Process/resource cleanup is verified before `CANCELLED`; failure is diagnostic and not PASS |
| Timeout | Timeout triggers termination/cleanup/verification and records a truthful final state |
| Resume | `NATIVE`, `MANAGED`, and `NONE` behavior is separately tested; native resume is never fabricated |
| Usage | `UNAVAILABLE`, `ESTIMATED`, and `EXACT` remain distinguishable through persistence and API output |
| Workflow | Only generic `runtime_profile_ref`; no vendor CLI flags or credentials |
| WebSurface | User-confirmed assisted flow and manual fallback; no private API/session extraction |
| Doctor | Provider/Transport/Runtime/Adapter version and capability claims have actual evidence and maturity labels |

All PASS claims require actual commands/tool results and exit codes. `SKIPPED`, environment blockers, historical evidence, and unimplemented paths remain explicit.

## 6. Roadmap boundary

### V1 existing roadmap

- WP-14: Codex Runtime Adapter conformance.
- WP-15: OpenCode Runtime Adapter conformance.
- WP-16: Doctor/capability/version matrix.

The Foundation Gate is a prerequisite and does not renumber existing work packages.

### Post-V1

- Claude Code `NATIVE_SUBSCRIPTION` Adapter.
- Gemini CLI `NATIVE_SUBSCRIPTION` Adapter.
- OpenAI, Anthropic, and Google `OFFICIAL_API` Adapters.
- Multi-transport routing/fallback policy.

### Assisted WebSurface

WP-19/WP-20 remain the WebSurface/Browser Companion path. They are not Subscription Runtime or official API implementations.

## 7. Entry and exit conditions

Sub-gate A entry/exit is satisfied:

- PRE-WP14-A was implemented by OpenCode (Attempt 2), independently reviewed by a fresh Codex context after an initial FAIL was remediated, Human-accepted, and checkpointed at `28196c9`.
- PRE-WP14-A Attempt 2 deterministic evidence (2026-08-25, basis `8994ef9`): targeted 17 passed; lifecycle+WP07 regression 17 tests / 16 passed / 1 skipped; WP09+WP12+WP13 regression 218 passed; Full Core 390 collected / 389 passed / 1 skipped; baseline PASS — all exit code 0. These are historical evidence for checkpoint `28196c9`, not new claims.

Implementation entry conditions for Sub-gate B (HISTORICAL entry gate — all three have since been satisfied; retained as record):

- a fresh independent Reviewer validated the PRE-WP14-A accepted-state synchronization — DONE before the PRE-WP14-B implementation gate opened;
- Human separately authorized the PRE-WP14-B implementation gate with an explicit product source/test/migration allowlist, legacy backfill policy, rollback/restore path, and executable Python environment — DONE (the exact 15-file allowlist);
- OpenCode was explicitly assigned as the single implementation Writer and a fresh independent Codex context as Reviewer (Writer != Reviewer) — DONE.

Exit for Sub-gate B is satisfied for this bounded implementation gate:

- Fresh independent Codex re-review: `VERIFIED_PASS`.
- Human acceptance decision: granted 2026-08-26.
- Next owner for WP-14: Human, through a separate WP-14 Architecture/Implementation gate; WP-14 remains out of scope here.

## 8. Do not change during this preparation task (HISTORICAL / SUPERSEDED by the Human-approved PRE-WP14-B implementation allowlist)

Historical preparation-phase constraints, retained as record. Items marked DONE were executed only within the later Human-approved 15-file allowlist; everything outside that allowlist remains unchanged and not authorized:

- WP-13 code, tests, schemas, migrations, status, or active handoff ownership.
- ADR-001 through ADR-010 decision text.
- RunState or `ExecutionTarget.LOCAL`.
- Production code, API, DB schema, workflow schema, dependencies, scripts, or Adapter implementations — CHANGED ONLY within the approved PRE-WP14-B 15-file allowlist; API/DB-schema-of-runs/workflows/dependencies remain untouched.
- WebSurface into an API/Runtime shortcut.

## 9. Next exact step

Current state (supersedes the historical planning wording previously in this section):

- PRE-WP14-B implementation is authorized under the Human-approved exact 15-file allowlist and is `HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED` on baseline `934a219` after fresh independent Codex `VERIFIED_PASS`.
- Human acceptance was granted on 2026-08-26; the exact-allowlist Git checkpoint is in progress and its final SHA is recorded after commit.
- No push, remote operation, or migration against any real/user database is authorized. Alembic may run ONLY inside pytest temporary isolated SQLite databases; stage/commit are authorized only for the exact 15-file allowlist in this checkpoint.
- Excluded dirty files `docs/15_DOCUMENT_INDEX.md` and `docs/tasks/WP-12.md` keep their ownership and must not be silently absorbed.
- Human acceptance was granted after independent review `VERIFIED_PASS`; the remaining action is the exact-allowlist Git checkpoint. AI tools cannot self-accept, and this acceptance does not authorize scope expansion into WP-14/WP-15, push, remote changes or real-database migration.
