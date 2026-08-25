# Runtime Contract Foundation Gate — Pre-WP14

- Status: `PRE-WP14-A IMPLEMENTATION_ACCEPTED @ 28196c9 / PRE-WP14-B PLANNING_ONLY NOT_AUTHORIZED / STATE_SYNC_INDEPENDENT_REVIEW_REQUIRED`
- Architecture decision status: `ADR-011 HUMAN_ACCEPTED / IMPLEMENTATION_NOT_AUTHORIZED` (unchanged)
- Sub-gate A (ADR-007 timeout cleanup): `HUMAN_ACCEPTED / IMPLEMENTATION_ACCEPTED` at checkpoint `28196c9`
- Sub-gate B (Runtime Binding contract): `PLANNING_ONLY / NOT_IMPLEMENTED / NOT_AUTHORIZED`; Alembic `0002`, RuntimeBindingSnapshot persistence/reload, legacy backfill and rollback/restore are NOT implemented
- Gate type: Architecture and contract gate
- Accepted-state sync Writer: OpenCode
- Required Reviewer: fresh independent Codex context; Writer != Reviewer is mandatory
- Decision and Git authority: Human
- Accepted ADR: `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`
- Existing authority: ADR-007 and ADR-010 remain frozen

## 1. Purpose

This gate prevents WP-14/WP-15 production Runtime work from being built on an identity, credential, capability, or timeout-cleanup contract that cannot represent future official Subscription and API Runtimes.

It does not implement Runtime Binding, Registry, SecretStore, migrations, APIs, UI, or vendor Adapters. It does not change WP-13 scope or status.

## 2. Verified current implementation

As of the PRE-WP14-A accepted checkpoint `28196c9705e688ee05c0bb4703cdf5b254d400c6`:

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

### PRE-WP14-B. Runtime Binding Contract — `PLANNING_ONLY / NOT_AUTHORIZED`

Status: NOT implemented. Alembic `0002`, Run-owned immutable RuntimeBindingSnapshot persistence/reload, deterministic legacy backfill, rollback/restore and their tests remain unimplemented; implementation requires a separate Human gate with an explicit source/migration allowlist.

Goal: approve a durable, vendor-neutral Runtime identity and resolution contract before production Adapter wiring.

Acceptance requirements:

1. Human acceptance of ADR-011 is explicitly recorded; it does not grant implementation or migration authority, and AI tools cannot self-promote task acceptance.
2. Provider, TransportKind, Runtime, Adapter, and ExecutionTarget have non-overlapping meanings.
3. `provider_id`, `runtime_id`, `adapter_id`, and profile identifiers use validated opaque identifiers rather than closed vendor enums.
4. `TransportKind` supports `LOCAL`, `NATIVE_SUBSCRIPTION`, `OFFICIAL_API`, and the boundary-only `WEB_INTERACTIVE` value.
5. RuntimeProfile is mutable intention/configuration; RuntimeBindingSnapshot is immutable resolved Run history.
6. Run-owned immutable snapshot persistence and a future Alembic `0002` migration preserve the resolved identity without raw credentials; deterministic legacy/reference backfill and downgrade/restore must be approved and verified.
7. Runtime Registry/Adapter Factory selection replaces hard-coded Adapter construction without Core vendor branching.
8. Workflow selection, if approved, uses only `runtime_profile_ref`.
9. Auth ownership supports `RUNTIME_MANAGED`, `SECRET_REF`, `BROWSER_PROFILE_MANAGED`, and `NONE` without mixing credentials, permission, or data policy.
10. Capability contract includes cancel, resume, artifacts, timeout cleanup, usage visibility, and auth mode.
11. Usage visibility is `UNAVAILABLE`, `ESTIMATED`, or `EXACT`; precise usage is never fabricated.
12. WebSurface remains separate from official API and Runtime execution semantics.

## 4. Planned implementation impact after approval

The implementation owner must prepare a narrow, separately approved plan for the minimum necessary changes. Likely surfaces include:

- Domain identity/value objects and Run snapshot.
- Runtime contract descriptor/capabilities.
- Registry/factory wiring.
- Run persistence/repository plus a real Alembic migration and old-data policy.
- Run API DTOs and selection contract.
- Generic workflow profile reference only if required by an approved use case.
- SecretRef/auth-ownership compatibility only where required; a new SecretStore implementation is not automatically authorized.
- Managed CLI process lifecycle/cleanup abstraction.
- Deterministic contract, persistence, migration, API, and conformance tests.

This list is impact analysis, not permission to modify those files during documentation preparation.

## 5. Test and acceptance matrix for the future implementation gate

| Area | Required evidence |
|---|---|
| Identity | Same Provider with multiple Transports remains distinguishable; Provider never implies Runtime |
| Persistence | Binding snapshot survives session close/reopen and upgrade/downgrade/re-upgrade lifecycle |
| Legacy data | Existing Runs receive an explicit deterministic legacy/reference identity or a documented fail-closed migration result |
| Registry | Profile resolves to the expected Adapter without `if provider == ...` branches |
| Auth | Raw credential/Cookie/Session markers are rejected or absent from DB, Event, Evidence, Artifact, API, log, export, and handoff |
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

Implementation entry for Sub-gate B remains blocked until:

- a fresh independent Reviewer validates this PRE-WP14-A accepted-state synchronization;
- Human separately authorizes the PRE-WP14-B implementation gate with an explicit product source/test/migration allowlist, legacy backfill policy, rollback/restore path, and executable Python environment;
- OpenCode is explicitly assigned as the single implementation Writer and a fresh independent Codex context as Reviewer (Writer != Reviewer).

Exit for Sub-gate B requires:

- separate PASS/decision records for Sub-gate B;
- approved implementation scope, migration, legacy-backfill and rollback/restore plan;
- explicit next owner for WP-14.

## 8. Do not change during this preparation task

- WP-13 code, tests, schemas, migrations, status, or active handoff ownership.
- ADR-001 through ADR-010 decision text.
- RunState or `ExecutionTarget.LOCAL`.
- Production code, API, DB schema, workflow schema, dependencies, scripts, or Adapter implementations.
- WebSurface into an API/Runtime shortcut.

## 9. Next exact step

This accepted-state synchronization (docs/11_PROJECT_STATE.md, docs/12_HANDOFF_CURRENT.md, docs/30_RUNTIME_CONTRACT_FOUNDATION_GATE.md) is handed to a fresh independent Codex Reviewer. Only after independent review PASS may Human separately authorize an exact-allowlist docs-only checkpoint (owned: the three synced docs; excluded dirty files `docs/15_DOCUMENT_INDEX.md` and `docs/tasks/WP-12.md` keep their ownership and must not be silently absorbed). PRE-WP14-B implementation, Alembic `0002`, RuntimeBindingSnapshot, legacy backfill, rollback/restore and persistence/reload remain NOT_AUTHORIZED until their own Human gate. No stage, commit, push, product implementation, migration, or AI self-acceptance is implied by this document update.
