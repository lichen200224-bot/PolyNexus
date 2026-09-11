# ARCH-MODULAR-CORE-01 — V1 Static Modular Contract Foundation

- Status: `READY_FOR_CODEX_START`
- Human direction: `APPROVED` on 2026-09-11
- Architecture source: `docs/34_ADR_013_MODULAR_CORE_EXTENSION_ARCHITECTURE.md`
- Documentation branch: `architecture/modular-core-extension-contract`
- Documentation predecessor: `f34e6b29ae9e7326d1d44b9b03756b450809928f`
- Implementation Writer: `Codex` in a new isolated branch/worktree
- Independent Reviewer: fresh Codex context that did not modify the candidate
- Human: architecture/acceptance/Git promotion authority
- G30 relationship: parallel architecture track; **G30/WP-20 remains unchanged and is not satisfied by this task**

## 1. Goal

Make the existing D07 `Plugin-ready now, Plugin Platform later` principle concrete without redesigning the PolyNexus Core.

MCF-01 must provide the smallest static extension foundation that can describe and register replaceable modules while reusing the already-accepted runtime architecture:

```text
Static Module Manifest / Module Registry
    -> Runtime Module bridge
    -> RuntimeProfile / RuntimeRegistry
    -> RuntimeBindingSnapshot
    -> RuntimeAdapter
    -> RunSupervisor
```

The task is successful when PolyNexus has a native, vendor-neutral base contract that can later host external runtimes/workspaces as components without making the Core depend on them.

## 2. Mandatory start gate

Before writing any code, Codex must:

1. Read `AGENTS.md`.
2. Read `docs/11_PROJECT_STATE.md` and `docs/12_HANDOFF_CURRENT.md` to preserve current G30 truth.
3. Read `docs/00_SCOPE_BASELINE.md`, `docs/10_DECISION_LOG.md`, `docs/18_ARCHITECTURE_DECISIONS.md`, `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`, `docs/30_RUNTIME_CONTRACT_FOUNDATION_GATE.md`, `docs/31_ADR_012_RUNTIME_DOCTOR_REPORTING.md`, and `docs/34_ADR_013_MODULAR_CORE_EXTENSION_ARCHITECTURE.md`.
4. Read the current implementations of:
   - `services/core/src/polynexus_core/runtime/contracts.py`
   - `services/core/src/polynexus_core/runtime/registry.py`
   - `services/core/src/polynexus_core/runtime/supervisor.py`
   - `services/core/src/polynexus_core/execution_service.py`
5. Resolve and record the exact Git HEAD of `architecture/modular-core-extension-contract` at task start.
6. Create a new isolated implementation branch/worktree from that exact resolved docs checkpoint. Suggested branch: `feature/mcf-01-static-module-contract`.
7. Verify the protected primary checkout is not modified.

If the repository state materially contradicts ADR-013 assumptions, stop code changes and report `ARCHITECTURE_CONFLICT` with exact file/line evidence. Do not silently reinterpret the architecture.

## 3. Existing facts that must be reused

Do not reimplement these concepts:

- `RuntimeAdapter` Protocol already exists.
- `RuntimeCapabilities` already exists.
- `RuntimeRegistry` / AdapterFactory already exists.
- `RuntimeProfile` and immutable Run-owned `RuntimeBindingSnapshot` already exist.
- Codex/OpenCode deterministic conformance adapters already exist.
- RunSupervisor owns lifecycle.
- Runtime Doctor already has truthful capability/maturity reporting rules.

MCF-01 is a generic composition/extension layer around these contracts, not a second runtime system.

## 4. Authorized implementation scope

### 4.1 New generic extension package

Codex may create a minimal package under:

```text
services/core/src/polynexus_core/extensions/
```

Expected responsibilities, not mandatory filenames:

- versioned Module Manifest / descriptor model;
- module type vocabulary;
- static Module Registry;
- deterministic duplicate/conflict rejection;
- contract-version validation;
- capability declaration normalization;
- lifecycle/health metadata boundary;
- runtime-module bridge that delegates to the existing RuntimeRegistry.

Prefer stdlib/dataclass/Protocol patterns already used in Core. Do not add dependencies unless a separate Human gate is obtained.

### 4.2 Tests

Codex may add focused tests under:

```text
services/core/tests/test_mcf01_*.py
```

Tests must be deterministic and must not require network, vendor credentials, real vendor CLI logins, browser sessions or external sends.

### 4.3 Existing source files

The first implementation should avoid modifying existing product source where possible.

Only these existing source files may be changed if Codex demonstrates that a narrow bridge cannot otherwise be implemented:

- `services/core/src/polynexus_core/runtime/contracts.py`
- `services/core/src/polynexus_core/runtime/registry.py`

Any edit to either file must be minimal, backward-compatible, and explicitly justified in the handoff. `RuntimeAdapter` method semantics, immutable RuntimeBindingSnapshot, Run identity, RunState and RunSupervisor lifecycle ownership must remain unchanged.

### 4.4 Documentation updates after implementation

Codex may update only the following documentation for current-state truth:

- this task document;
- `docs/32_KNOWN_LIMITATIONS.md` if a new limitation needs recording;
- a new MCF-01 evidence summary under `artifacts/verification/` if permitted by repository ignore/governance rules.

Do not rewrite G30 status, score, operator reports, WP-20 state or historical acceptance records.

## 5. Required Module Manifest semantics

The normalized manifest/descriptor must cover at least:

```text
module_id
module_type
module_version
contract_version
capabilities
config boundary
lifecycle / health boundary
maturity / conformance declaration boundary
```

`provider_id` is included only where meaningful; it must not become a closed vendor enum.

The manifest must not contain:

- raw API keys;
- cookies;
- session tokens;
- bearer tokens;
- browser credentials;
- private secret values.

Unknown contract versions and conflicting registrations must fail closed.

## 6. Module type boundary

Architectural vocabulary:

- `RUNTIME`
- `TOOL`
- `SURFACE`
- `INTEGRATION`

`MEMORY` is reserved for future architecture only. Do not create a new Memory Domain, DB schema or persistence service in MCF-01.

Only `RUNTIME` requires an executable bridge in this first task. Other module types may exist only as validated descriptor vocabulary unless a concrete contract already exists.

## 7. Runtime bridge requirements

The runtime bridge must reuse the existing runtime path. It must not create a competing runtime registry or bypass RuntimeBindingSnapshot.

Required behavior:

1. A runtime module can expose one or more existing `RuntimeProfile` registrations through the generic module descriptor.
2. Adapter creation still goes through the existing RuntimeRegistry/AdapterFactory contract.
3. Run execution still goes through RuntimeAdapter -> RunSupervisor.
4. Capability/policy incompatibility remains fail-closed.
5. Module metadata cannot mutate historical RuntimeBindingSnapshot data.
6. No generic extension code may contain normal-path vendor conditionals for Codex/OpenCode/holaOS/OpenHands/etc.

The deterministic proof should use existing Reference/Codex/OpenCode conformance surfaces. Do not add a production holaOS or OpenHands adapter in MCF-01.

## 8. Required negative tests

At minimum prove rejection of:

- unsupported `contract_version`;
- duplicate `module_id` with conflicting descriptor;
- conflicting runtime module/profile registration;
- malformed identifiers;
- invalid/unknown module type;
- capability declaration that cannot be normalized;
- forbidden secret-like manifest values if the implementation accepts arbitrary config metadata;
- bridge request for an unavailable runtime profile/factory;
- module failure that would otherwise silently fall back to a different runtime.

Tests must assert real exceptions/results, not log text alone.

## 9. Conformance proof

At least two interchangeable deterministic runtime module registrations must exercise the same generic module contract. Preferred proof uses Reference plus one or both existing Codex/OpenCode deterministic conformance adapters.

The proof must establish:

- same generic descriptor/registry path;
- different adapter/runtime identities;
- no Core vendor branch;
- truthful capabilities;
- successful normal resolution;
- fail-closed conflict/unknown resolution.

This is a contract proof, not a production-vendor support claim.

## 10. Regression requirements

After focused tests pass, run the relevant existing regression suites, including at least:

- Runtime skeleton/binding tests;
- WP-14 Codex Runtime tests;
- WP-15 OpenCode Runtime tests;
- WP-16 Runtime Doctor tests;
- workflow/runtime-selection tests affected by the bridge;
- Full Core pytest;
- baseline validator;
- governance validator;
- `git diff --check`.

Report actual command, actual exit code, pass/fail/skip counts and environment blockers. `SKIPPED` is not PASS. Do not reuse old logs as current evidence.

## 11. Explicit exclusions

MCF-01 MUST NOT implement:

- dynamic plugin loading;
- remote install/remove/update;
- marketplace;
- signing/PKI/trust store;
- hot reload;
- dependency resolver;
- third-party UI SDK;
- remote code execution;
- new DB table or Alembic migration;
- new workflow node;
- new public API endpoint;
- UI redesign;
- new SecretStore subsystem;
- holaOS production integration;
- OpenHands production integration;
- new authenticated vendor/WebSurface work;
- changes to G30/WP-20 acceptance state or project score.

If any excluded item becomes necessary, stop and return `SCOPE_EXPANSION_REQUIRED` with evidence and a minimal proposal.

## 12. Writer handoff format

Codex Writer must return:

```text
TASK_ID: ARCH-MODULAR-CORE-01
START_SHA: <exact>
BRANCH: <exact>
RESULT: READY_FOR_INDEPENDENT_REVIEW | NEED_FIX | BLOCKED | SCOPE_EXPANSION_REQUIRED

CHANGED_FILES:
- <exact paths>

ARCHITECTURE:
- module contract summary
- how RuntimeRegistry was reused
- whether existing runtime/contracts.py or registry.py changed and why

TESTS:
- command
- exit code
- pass/fail/skip

NEGATIVE_TESTS:
- case
- observed rejection

GOVERNANCE:
- vendor-specific Core branch: YES/NO
- migration/schema change: YES/NO
- secret boundary change: YES/NO
- G30/WP-20 change: YES/NO

KNOWN_LIMITATIONS:
- ...

NEXT_REQUIRED_ROLE:
FRESH_INDEPENDENT_CODEX_REVIEWER
```

## 13. Independent review gate

Writer != Reviewer.

A fresh Codex context must independently inspect the actual diff and rerun deterministic acceptance commands. It must not accept the Writer's PASS claims without execution evidence.

Review verdict:

- `VERIFIED_PASS`
- `NEED_FIX`
- `FAIL`
- `BLOCKED`

Only after `VERIFIED_PASS` should the Human be asked for the Git promotion decision.

## 14. Git / external side-effect boundary

This task authorizes Codex to create an isolated implementation branch/worktree and modify the bounded candidate files above.

It does **not** authorize:

- force push;
- merge/rebase into the G30/default development line;
- remote reconfiguration;
- modifying the protected primary checkout;
- external vendor send/login automation;
- promotion of G30/WP-20 or project score;
- final merge/push of the implementation candidate before independent review and Human acceptance.

The architecture documentation branch itself is a separate docs-only checkpoint and must remain recoverable independently of the MCF-01 implementation candidate.
