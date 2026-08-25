# Runtime Contract Foundation Gate — Pre-WP14

- Status: `ARCHITECTURE_ACCEPTED / STATE_SYNC_INDEPENDENT_REVIEW_REQUIRED`
- Architecture decision status: `ADR-011 HUMAN_ACCEPTED / IMPLEMENTATION_NOT_AUTHORIZED`
- Product implementation status: `NOT_STARTED`
- Gate type: Architecture and contract gate
- Implementation status: `NOT_IMPLEMENTED`
- Entry condition: satisfied for planning — WP-13 checkpoint `330adbc` and Governance checkpoint `358d263`; implementation remains separately gated
- Documentation Writer: Codex (current context)
- Documentation Reviewer: fresh independent context
- Future implementation Writer / Reviewer: OpenCode / fresh independent Codex
- Decision and Git authority: Human
- Accepted ADR: `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`
- Existing authority: ADR-007 and ADR-010 remain frozen

## 1. Purpose

This gate prevents WP-14/WP-15 production Runtime work from being built on an identity, credential, capability, or timeout-cleanup contract that cannot represent future official Subscription and API Runtimes.

It does not implement Runtime Binding, Registry, SecretStore, migrations, APIs, UI, or vendor Adapters. It does not change WP-13 scope or status.

## 2. Verified current implementation

As of current Governance checkpoint `358d263e16ccafca413672399f968fe769e57563` and the current read-only source inspection:

- `RunSupervisor` accepts a generic `RuntimeAdapter` and owns normalized Run lifecycle.
- `ExecutionService` constructs `ReferenceRuntimeAdapter` directly.
- `Run` and `RunRow` store `execution_target`, `resume_mode`, and opaque `runtime_ref` only.
- `ExecutionTarget` contains `LOCAL`; `ResumeMode` contains `NATIVE`, `MANAGED`, and `NONE`.
- `RuntimeCapabilities` declares only cancel, resume, and artifacts.
- API Run creation accepts only `context_package_id`.
- Workflow nodes are vendor-neutral, but step additional properties are not a Runtime Binding contract.
- No implemented Provider, TransportKind, RuntimeProfile, RuntimeBindingSnapshot, Adapter Registry, SecretRef/SecretStore, or managed CLI process abstraction exists.
- Existing tests are Reference Runtime-centric and assert the current `LOCAL/NONE` default.
- User cancel verifies Adapter cleanup; timeout paths do not yet prove the complete ADR-007 timeout-to-cleanup sequence.

These are `CURRENT IMPLEMENTATION` facts, not statements that accepted architecture capabilities already exist.

## 3. Gate split

The Foundation Gate has two independent sub-gates. Neither may be hidden inside the other.

### PRE-WP14-A. ADR-007 Timeout Cleanup Compliance

Goal: prove the existing ADR-007 requirement for every real process/session Runtime.

Required contract sequence:

```text
timeout detection
  -> cancel/terminate the owned work
  -> cleanup child/tool/process/resource tree
  -> verify cleanup
  -> record a truthful legal final state and evidence
```

Acceptance requirements:

1. Timeout uses the same cleanup machinery and verification standard as cancel.
2. A Run is not reported as cleanly timed out until cleanup is verified.
3. Cleanup failure produces the existing diagnostic behavior (`ORPHANED` through a legal lifecycle path) and never PASS evidence.
4. Raw vendor errors, process output, paths, tokens, and credentials are sanitized before durable persistence.
5. Deterministic fake-process/fake-resource tests prove success and cleanup-failure paths.
6. Adapter maturity cannot exceed the highest level supported by current cleanup evidence.

This sub-gate is existing ADR-007 compliance work. It is not introduced by subscription support.

### PRE-WP14-B. Runtime Binding Contract

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

Planning entry is satisfied:

- WP-13 was independently accepted and checkpointed at `330adbc`.
- Governance v1.1 was independently accepted, Human-approved and checkpointed at `358d263`.
- Human authorized curated docs-only integration without merging or overwriting the older docs worktree.
- The integrated ADR documentation received independent `VERIFIED_PASS`, and Human explicitly accepted ADR-011 architecture on 2026-08-25.

Implementation entry remains blocked until:

- a fresh independent Reviewer validates the Human-accepted ADR-011 state synchronization;
- Human separately authorizes each PRE-WP14 implementation gate and resolves existing `supervisor.py` dirty-file ownership before any task touches it;
- the exact product source/test/migration allowlist, legacy policy, rollback/restore path, and executable Python environment are approved/available;
- OpenCode is explicitly assigned as the single implementation Writer.

Exit requires:

- recorded Human acceptance of ADR-011 architecture, without implying implementation authority;
- separate PASS/decision records for Sub-gate A and Sub-gate B;
- approved implementation scope and migration/rollback plan;
- explicit next owner for WP-14.

## 8. Do not change during this preparation task

- WP-13 code, tests, schemas, migrations, status, or active handoff ownership.
- ADR-001 through ADR-010 decision text.
- RunState or `ExecutionTarget.LOCAL`.
- Production code, API, DB schema, workflow schema, dependencies, scripts, or Adapter implementations.
- WebSurface into an API/Runtime shortcut.

## 9. Next exact step

A fresh independent Reviewer verifies the Human-accepted ADR-011 state synchronization against checkpoint `358d263`, the two protected worktrees, ADR-001–010, D11, and the three excluded pre-existing dirty files. Human may then separately authorize an exact-allowlist documentation checkpoint and later bounded PRE-WP14-A/B implementation tasks for OpenCode. No stage, commit, push, worktree merge, product implementation, migration, or AI self-acceptance is implied.
