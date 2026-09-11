# ADR-013 — Modular Core and Extension Architecture

- Status: `HUMAN_DIRECTION_ACCEPTED / PENDING_INDEPENDENT_DOC_REVIEW`
- Date: 2026-09-11
- Base checkpoint: `f34e6b29ae9e7326d1d44b9b03756b450809928f`
- Branch: `architecture/modular-core-extension-contract`
- Scope: architecture/documentation formalization of the already-confirmed D07 / V1 Plugin-ready direction
- Implementation status: `NOT_STARTED`
- Depends on: D07, ADR-007, ADR-008, ADR-009, ADR-010, ADR-011, ADR-012

## 1. Decision summary

PolyNexus will remain a **Local-first Multi-AI Collaboration & Validation Workspace** whose durable value lives in the PolyNexus Core, while execution engines, tools, surfaces, integrations, and later memory providers can be replaceable extension modules behind versioned contracts.

The product metaphor is a modular robot:

- PolyNexus Core is the chassis, nervous system, governance and evidence plane.
- Runtime / Tool / Surface / Integration modules are replaceable components.
- External systems such as Codex, OpenCode, Claude Code, Gemini CLI, local runtimes, ACP-compatible agents, OpenHands-like runtimes, or holaOS-like workspaces may be integrated through an appropriate adapter/module boundary when technically and legally supportable.
- PolyNexus MUST retain a usable native baseline and MUST NOT become dependent on any one external runtime or workspace for its core product identity.

This ADR does **not** authorize a dynamic plugin marketplace. V1 remains statically registered / built-in extension architecture as already defined by `docs/00_SCOPE_BASELINE.md` and D07.

## 2. Why this is an architecture formalization, not a product reset

The existing baseline already requires:

- Plugin-ready Extension Architecture.
- Versioned contract, manifest, capabilities, lifecycle, registry, config/event boundary, failure isolation and conformance tests.
- Core-owned RunSupervisor with adapter-owned runtime logic.
- RuntimeProfile -> RuntimeRegistry / AdapterFactory -> RuntimeBindingSnapshot -> RuntimeAdapter -> RunSupervisor.
- No vendor-specific Core branching for normal adapter differences.

The repository also already implements a substantial runtime modularity foundation:

- `RuntimeAdapter` Protocol.
- `RuntimeCapabilities`.
- `RuntimeRegistry` and adapter factories.
- immutable Run-owned `RuntimeBindingSnapshot`.
- deterministic Codex/OpenCode conformance adapters.
- Runtime Doctor / capability reporting.

ADR-013 therefore generalizes an existing architectural direction instead of replacing the current Domain model or Runtime contract.

## 3. Core ownership — non-replaceable product semantics

The following remain Core-owned and are not delegated to third-party modules:

- Project / Task / Run identity and lifecycle.
- WorkflowDefinition and workflow gate semantics.
- RunSupervisor lifecycle ownership.
- RuntimeBindingSnapshot authority for execution history.
- ContextPackage semantics.
- Artifact / Evidence / Finding / RunResult semantics.
- Event Ledger and provenance.
- assurance / governance / Human Gate rules.
- data classification and egress policy.
- SecretRef and secret-boundary rules.
- validation truthfulness: AI opinion is never promoted to deterministic evidence merely because a module produced it.

An extension may produce candidate outputs, events, artifacts, evidence inputs or capability declarations, but the Core decides how those values are normalized, persisted, classified, validated and used by gates.

## 4. Extension model

### 4.1 Module vs Adapter

`Module` and `Adapter` are different concepts.

- **Module / Extension**: packaging, registration, metadata, configuration and lifecycle unit visible to PolyNexus composition.
- **Adapter**: normalized programmatic behavior contract between Core and an external capability.

A module may contain one or more adapters. A runtime module normally exposes a `RuntimeAdapter` and one or more `RuntimeProfile` definitions.

Example:

```text
holaOS Runtime Module (future compatibility target)
    -> PolyNexus RuntimeAdapter implementation
    -> supported holaOS execution surface
```

The module boundary MUST NOT bypass RuntimeAdapter, RunSupervisor, policy, evidence, secret or lifecycle contracts.

### 4.2 V1 module classes

The architectural vocabulary reserves these module classes:

- `RUNTIME`: execution runtime / harness / agent environment.
- `TOOL`: bounded callable capability used by workflows or runtimes.
- `SURFACE`: browser, desktop or other user-interaction surface boundary.
- `INTEGRATION`: external application/service connector.

`MEMORY` is a future extension class and is not authorized as a new V1 Domain or persistence subsystem by this ADR.

Only module classes backed by an implemented contract may be advertised as supported. Reserved vocabulary is not an implementation claim.

## 5. Versioned Module Manifest

Every V1 static module must have a normalized descriptor/manifest with, at minimum:

```text
module_id
module_type
module_version
contract_version
provider_id (when applicable)
capabilities
config_schema_ref or explicit no-config declaration
lifecycle declaration
security / permission declaration
conformance scope and maturity
```

Rules:

1. IDs use validated opaque identifiers; Core does not maintain a closed vendor enum.
2. A manifest contains no raw credentials, cookies, session tokens or private endpoint secrets.
3. Capabilities are declarations until backed by conformance evidence.
4. Unknown contract versions fail closed.
5. Unsupported capability requests fail closed; there is no silent fallback to another module when policy or user intent forbids it.
6. Module metadata must not alter historical Run binding facts.

## 6. Capability-based resolution

PolyNexus must resolve components by normalized capability and policy, not by Core vendor branching.

Forbidden normal-path patterns include:

```text
if provider == openai
if runtime == holaos
if runtime == opencode
```

Vendor-specific invocation, output parsing, session semantics and compatibility stay inside the adapter/module implementation.

For Runtime modules, ADR-011 remains authoritative. ADR-013 does not replace `RuntimeProfile`, `RuntimeBindingSnapshot`, `RuntimeRegistry` or `RuntimeAdapter`; it wraps the composition model around them.

A Workflow should prefer stable profile/capability references and must not embed executable paths, vendor CLI flags, tokens, cookies or module-private configuration.

## 7. V1 static registry

V1 remains **static registration**.

Required V1 behavior:

- explicit module registration at composition time;
- deterministic duplicate/conflict rejection;
- contract-version validation;
- capability declaration validation;
- health/readiness integration where the underlying contract supports it;
- enable/disable/configuration boundary without arbitrary remote code loading;
- bounded failure isolation so one unavailable extension cannot silently corrupt Core state;
- conformance tests for every claimed module contract.

Explicitly NOT authorized in V1:

- remote plugin install;
- arbitrary third-party code loading;
- marketplace;
- auto-update;
- package signing infrastructure;
- hot reload;
- dependency resolver;
- third-party UI SDK;
- automatic remote code execution.

These remain future Plugin Platform concerns.

## 8. Runtime architecture mapping

The current runtime path remains valid:

```text
RuntimeProfile
  -> RuntimeRegistry / AdapterFactory
  -> RuntimeBindingSnapshot
  -> RuntimeAdapter
  -> RunSupervisor
```

ADR-013 adds a composition layer, not a replacement execution path:

```text
Static Module Manifest / Module Registry
  -> Runtime Module bridge
  -> existing RuntimeProfile / RuntimeRegistry
  -> existing RuntimeBindingSnapshot
  -> existing RuntimeAdapter
  -> existing RunSupervisor
```

The first implementation must prove that the generic module layer can describe and register the existing deterministic Reference/Codex/OpenCode runtime capabilities without adding vendor conditionals or changing Run identity.

## 9. External workspace/runtime compatibility

Complete agent workspaces or harnesses may be integrated later as runtime modules if they can satisfy the PolyNexus contract truthfully.

Potential compatibility targets include, but are not limited to:

- Claude Code;
- Gemini CLI;
- ACP-compatible agents;
- local model runtimes/harnesses;
- OpenHands-like agent runtimes;
- holaOS-like agent workspaces.

These names are **compatibility examples only**. ADR-013 does not claim current support, certification, license compatibility, API availability, or production integration for any unimplemented target.

A future holaOS/OpenHands-style adapter must use documented/supported integration surfaces. It must not rely on cookie extraction, session-token replay, private API reverse engineering or bypass of vendor/user confirmation boundaries.

## 10. Governance and security boundary

Every module remains subordinate to PolyNexus policy:

```text
Module registration
  -> manifest / contract validation
  -> capability validation
  -> permission / data-routing checks
  -> auth ownership / SecretRef compatibility
  -> health/readiness
  -> execution
  -> normalized events / artifacts / evidence
  -> Core validation / governance gates
```

A module cannot self-declare `PASS`, `VERIFIED`, `SUPPORTED` or `CERTIFIED` beyond evidence-backed maturity.

Failure modes must be observable and fail closed where lifecycle, security, binding integrity or evidence truthfulness would otherwise be ambiguous.

## 11. Implementation strategy

### MCF-01 — V1 static modular contract foundation

Implement only the minimum generic layer required to make the already-existing D07 architecture concrete:

1. versioned Module Manifest / descriptor contract;
2. static Module Registry;
3. capability declaration and contract-version validation;
4. lifecycle/health metadata boundary;
5. runtime-module bridge using the existing RuntimeRegistry rather than replacing it;
6. deterministic conflict/failure tests;
7. conformance proof using existing Reference/Codex/OpenCode deterministic surfaces.

### Later V1.x

Only after MCF-01 is accepted:

- user-facing enable/disable/config UX;
- additional Tool/Integration contracts where a real use case exists;
- additional supported runtime modules;
- module-level Doctor inventory integration.

### Post-V1 Plugin Platform

Only with a separate ADR and Human approval:

- install/remove/upgrade packages;
- third-party packages;
- sandboxing;
- signing/trust chain;
- dependency resolution;
- remote distribution/marketplace;
- hot reload.

## 12. Compatibility and migration impact

Expected MCF-01 impact is intentionally bounded:

- no new Project/Task/Run/Artifact/Evidence/Finding Domain identity;
- no RunState change;
- no change to ADR-007 lifecycle ownership;
- no replacement of RuntimeBindingSnapshot;
- no database migration required for the initial static manifest/registry unless Codex demonstrates a concrete unavoidable requirement and stops for a separate architecture gate;
- no workflow node addition;
- no product score change and no claim that G30/WP-20 has been completed;
- current G30 external-verification `NEED_ACTION` remains independent.

## 13. Acceptance criteria

ADR-013 / MCF-01 is architecturally successful only if all are true:

- existing RuntimeAdapter and RuntimeRegistry remain valid and reusable;
- no vendor-specific Core branch is added;
- static extension manifests are versioned and fail closed on unknown versions/conflicts;
- module failure cannot rewrite or bypass immutable Run binding history;
- capability claims stay distinct from conformance evidence and maturity;
- secrets remain excluded from manifests, Domain history, Evidence, logs, Git and handoff;
- a deterministic conformance test demonstrates at least two interchangeable runtime module registrations using the same generic module contract;
- existing runtime, workflow, persistence, governance and Golden Workflow regression remain passing at their evidence-backed level;
- dynamic marketplace/remote install/hot reload remain absent.

## 14. Governance state and next action

Human explicitly agreed on 2026-09-11 to preserve PolyNexus native baseline capability while making runtime/components replaceable and future external workspaces usable as modules where appropriate.

This document records that direction as `HUMAN_DIRECTION_ACCEPTED` but still requires a fresh independent documentation/architecture review before the ADR is promoted to a final `HUMAN_ACCEPTED` architecture checkpoint.

The authorized next work item is `docs/tasks/ARCH-MODULAR-CORE-01.md`.

G30/WP-20 state, score, external Human-operator verification, and acceptance gates are unchanged by this parallel architecture track.
