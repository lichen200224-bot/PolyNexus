# ADR-011 — Runtime Binding and Transport Contract

- Status: `HUMAN_ACCEPTED`
- Date: 2026-08-21
- Integrated for Human architecture review: 2026-08-25
- Human Architecture Gate acceptance: 2026-08-25
- Governance checkpoint: `358d263e16ccafca413672399f968fe769e57563`
- Architecture authorization: `HUMAN_ACCEPTED / IMPLEMENTATION_NOT_AUTHORIZED`
- Decision owner: Human
- Implementation status: `NOT_IMPLEMENTED`
- Scope effect: Accepted architecture contract only; no change to the current V1 scope and no implementation authorization
- Depends on: ADR-002, ADR-004, ADR-006, ADR-007, ADR-008, ADR-009, ADR-010

This architecture decision was explicitly accepted by Human on 2026-08-25 after independent document review. Acceptance records the contract direction only; it does not authorize product code, schema, migration, API, workflow schema, credentials, Runtime integrations, stage, commit, push, or an implementation task.

## 1. Context

The current implementation has a Core-owned `RunSupervisor`, an adapter protocol, `ExecutionTarget.LOCAL`, `ResumeMode`, and an opaque `runtime_ref`. `ExecutionService` currently selects only the deterministic `ReferenceRuntimeAdapter`. The current Run/domain, persistence, and API models do not store Provider, Transport, Runtime, or Adapter identity.

The existing boundary is directionally correct, but a durable Runtime Binding is required before multiple official Runtime integrations can be selected and audited without later reconstructing execution facts from mutable configuration.

## 2. Accepted architecture decision

PolyNexus will keep five concepts independent:

| Concept | Meaning | Identifier rule | Example |
|---|---|---|---|
| Provider | The organization or ecosystem supplying a Runtime or service | `provider_id`: validated opaque identifier; not a closed vendor enum | `openai`, `anthropic`, `google`, `local`, `community` |
| TransportKind | How PolyNexus connects to the selected Runtime | Closed contract vocabulary defined below | `NATIVE_SUBSCRIPTION` |
| Runtime | The actual execution environment or service | `runtime_id`: validated opaque identifier; not inferred from Provider | `codex`, `claude-code`, `gemini-cli`, `opencode`, `local-model`, `openai-api` |
| Adapter | The PolyNexus implementation of normalized Runtime behavior | `adapter_id`: validated opaque identifier with independent version metadata | `builtin.codex-cli` |
| ExecutionTarget | Where the Runtime is executed or supervised | Existing Domain concept; V1 remains `LOCAL` | `LOCAL` |

Provider, Runtime, Adapter, and ExecutionTarget MUST NOT be treated as synonyms. Adding a Provider or Runtime MUST NOT require a DB migration merely to extend a closed vendor enum.

Opaque identifiers are format-validated, not vendor-enumerated. The proposed portable syntax is lower-case ASCII segments matching `^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$`. Core validates identifier syntax and length; the Registry determines whether an identifier is installed/available. The implementation gate must set and test a bounded maximum length without converting identifiers into closed Provider/Runtime enums.

### 2.1 TransportKind

The proposed vocabulary is:

- `LOCAL`: a local process or local endpoint not relying on a hosted subscription or official cloud API transport.
- `NATIVE_SUBSCRIPTION`: an officially permitted Agent/CLI Runtime that uses the vendor's supported subscription authentication and execution surface.
- `OFFICIAL_API`: a documented, supported vendor API using an official credential and public contract.
- `WEB_INTERACTIVE`: an assisted browser surface with explicit user interaction and WebSurface restrictions.

`ExecutionTarget` and `TransportKind` are orthogonal:

- `ExecutionTarget` answers **where execution is supervised**.
- `TransportKind` answers **how PolyNexus reaches the Runtime or surface**.

This ADR does not change `ExecutionTarget.LOCAL` for V1. `WEB_INTERACTIVE` reserves an identity boundary only; it does not create a production Runtime, grant API semantics to web traffic, or merge WebSurface with `RuntimeAdapter`.

## 3. RuntimeProfile

`RuntimeProfile` is user- or Workflow-selectable execution intention/configuration. A profile may refer to configuration and policy needed to resolve an Adapter, but it is not an execution fact.

Examples:

- `codex-default`
- `opencode-local`
- `claude-code-work`

If a Workflow later selects a Runtime, it may reference only:

```text
runtime_profile_ref
```

A Workflow MUST NOT contain vendor-specific CLI flags, executable paths, raw API keys, Cookie values, Session Tokens, browser profile secrets, or private endpoint information. The existing fixed workflow node vocabulary remains unchanged.

## 4. RuntimeBindingSnapshot

Before a Run begins real execution, PolyNexus must resolve its `RuntimeProfile` to an immutable `RuntimeBindingSnapshot` containing at least:

```text
provider_id
transport_kind
runtime_id
adapter_id
```

The implementation gate must also decide which version/configuration facts are required for reproducibility, such as Adapter version, Runtime version when detectable, capability snapshot, and non-secret profile revision.

The distinction is mandatory:

- `RuntimeProfile` = mutable intention/configuration.
- `RuntimeBindingSnapshot` = immutable resolved execution fact.

Run history must preserve the resolved snapshot. It must not recompute historical Provider/Transport/Runtime/Adapter identity from a profile that may later be edited, removed, or repointed.

Raw credentials, Cookie values, Session Tokens, and SecretStore values are never part of a snapshot.

### 4.1 Accepted V1 persisted snapshot direction and future migration plan

The selected V1 direction is a **Run-owned immutable persisted snapshot**, not a new Attempt, Packet Domain, Memory Domain, Provider Gateway, or independent execution identity. `Task != Run`; Run remains the durable execution identity and `Run == Attempt` is not frozen.

The separately approved future implementation task must specify:

1. One binding owned by the existing Run and fixed before real execution; repeated execution/read paths cannot silently rebind a persisted Run.
2. Required non-secret identity fields: `provider_id`, `transport_kind`, `runtime_id`, `adapter_id`, and the existing `execution_target`; version, capability, and policy/profile provenance fields require an explicit minimality decision.
3. An Alembic revision after existing `0001_initial_schema.py`, planned as `0002`; `Base.metadata.create_all()` is not migration authority.
4. Deterministic legacy/reference backfill for existing Runs. Candidate identities such as `local`, `LOCAL`, `reference`, and `builtin.reference` require a separate Human-approved implementation/migration policy; ADR acceptance does not silently approve their concrete values.
5. Upgrade verification against an existing database, persisted snapshot reload, mutation/rebinding rejection, downgrade or documented restore-from-backup, and upgrade-again preservation of old Run/Task/Evidence history.
6. Fail-closed behavior for missing binding, unknown/unavailable registry entries, incompatible auth/capability, ambiguous legacy data, or attempted secret persistence.
7. No production dependency, SecretStore subsystem, new public endpoint, workflow node, vendor-specific Core branch, or extra Provider integration unless separately justified and approved in the narrow implementation allowlist.

This section records the Human-accepted architecture direction and future acceptance requirements only; it does not authorize a migration or product implementation, and no persisted snapshot currently exists.

## 5. Adapter registry and selection

The planned resolution path is:

```text
RuntimeProfile
  -> RuntimeRegistry / AdapterFactory
  -> RuntimeBindingSnapshot
  -> RuntimeAdapter
  -> RunSupervisor
```

Core orchestration must select an Adapter by normalized registry/factory contracts. Normal Adapter differences must not produce Core branches such as:

```text
if provider == openai
if provider == anthropic
if provider == google
```

Vendor-specific invocation, session semantics, output parsing, compatibility, and failure normalization remain inside the Adapter. `RunSupervisor` remains the lifecycle owner.

## 6. Authentication ownership

Authentication ownership is separate from Provider, Transport, execution permission, and data-routing policy.

| Auth ownership | Meaning | Permitted Core state |
|---|---|---|
| `RUNTIME_MANAGED` | An officially supported CLI/Runtime manages its own official login | Profile/reference metadata only; no login Session or Cookie value |
| `SECRET_REF` | An official API requires a credential | `SecretRef` only; raw value resolved by the OS-backed `SecretStore` boundary |
| `BROWSER_PROFILE_MANAGED` | The user's browser profile owns WebSurface login | Association metadata only; Core never acquires Cookie or Session Token values |
| `NONE` | Runtime requires no credential | No credential reference |

An Adapter must declare its required auth ownership. Runtime selection must fail closed when the profile and Adapter auth requirements are incompatible.

## 7. Permanent security prohibitions

The following are prohibited architecture/security patterns, not merely deferred V1 features:

- ChatGPT Cookie extraction.
- Claude Cookie extraction.
- Gemini Cookie extraction.
- Session Token extraction.
- Bearer token stealing or replay.
- Private API reverse engineering.
- Undocumented GraphQL use.
- Unofficial WebSocket use.
- Wrapping subscription web traffic as an API.
- Bypassing vendor rate limits, quotas, confirmation, or access controls.
- Persisting raw third-party credentials in Domain tables, Run history, Events, Evidence, Artifacts, logs, exports, backups, Git, handoffs, or telemetry.

`WEB_INTERACTIVE` must remain an assisted WebSurface boundary with user-confirmed actions and manual/clipboard fallback. It is not an authorization to imitate or extract a private API.

## 8. Capability contract

The implementation must not assume all Runtimes expose the same behavior. Capability discovery must truthfully cover at least:

- cancel;
- resume;
- artifacts;
- timeout cleanup;
- usage visibility;
- auth mode.

Resume maturity remains:

- `NATIVE`
- `MANAGED`
- `NONE`

Usage visibility is:

- `UNAVAILABLE`: no supported value is available;
- `ESTIMATED`: a labeled estimate with its basis;
- `EXACT`: an authoritative value from a supported source.

PolyNexus must not infer, fabricate, or relabel usage/quota as precise when the Runtime does not provide authoritative values.

## 9. Compatibility and scope

### 9.1 V1 existing roadmap

- Codex Runtime Adapter remains under the existing WP-14 plan.
- OpenCode Runtime Adapter remains under the existing WP-15 plan.
- Both require the Runtime Contract Foundation Gate before implementation/conformance claims.

This accepted architecture decision does not expand V1 to additional production Provider integrations.

### 9.2 Post-V1 roadmap

- Claude Code `NATIVE_SUBSCRIPTION` Adapter.
- Gemini CLI `NATIVE_SUBSCRIPTION` Adapter.
- OpenAI `OFFICIAL_API` Adapter.
- Anthropic `OFFICIAL_API` Adapter.
- Google `OFFICIAL_API` Adapter.
- Multi-transport routing and fallback policy.

### 9.3 Assisted WebSurface

ChatGPT, Claude, and Gemini web automation remains governed by ADR-006 and the WebSurface/Browser Companion roadmap. It must not be represented as an official API Adapter or subscription Runtime merely because the same Provider name is involved.

## 10. ADR-007 compliance dependency

The current timeout path does not yet prove the complete ADR-007 sequence:

```text
timeout detection
  -> cancel/terminate
  -> cleanup
  -> cleanup verification
  -> truthful final state
```

This is an existing ADR-007 compliance gap, not a Subscription Runtime feature. The Pre-WP14 gate must accept it independently from Runtime Binding:

- Sub-gate A: ADR-007 Timeout Cleanup Compliance.
- Sub-gate B: Runtime Binding Contract.

No production Adapter may claim conformance above its evidence-backed maturity when timeout/process-tree cleanup remains unverified.

## 11. Alternatives considered

### Closed Provider/Runtime enums

Rejected in this proposal because each new Provider or Runtime would require code/schema churn and could force data migrations for identifier growth.

### Provider implies Runtime or Transport

Rejected because one Provider can expose multiple official execution methods, and the same Runtime family can have distinct auth and capability behavior.

### Resolve historical identity from RuntimeProfile

Rejected because mutable profiles are intentions, not durable execution facts.

### Treat WebSurface as an API Runtime

Rejected because it collapses ADR-006, user-confirmation, security, evidence maturity, and official-interface boundaries.

## 12. Consequences of the accepted architecture decision

Positive:

- The existing Supervisor/Adapter architecture remains intact.
- One Provider can support multiple Transports without Core vendor branching.
- Run history becomes auditable and reproducible.
- Auth ownership and security prohibitions become explicit.
- Doctor/Conformance can report identity and capability truthfully.

Cost and migration impact:

- The implementation gate will require Domain, persistence, migration, repository, API, wiring, and contract-test changes.
- Existing Runs will require an explicit, deterministic legacy/reference binding migration policy.
- UI selection is a later implementation concern and must use RuntimeProfile rather than Provider inference.

## 13. Acceptance and next action

ADR-011 is `HUMAN_ACCEPTED` as an explicit architecture decision dated 2026-08-25; its implementation remains `NOT_IMPLEMENTED / NOT_AUTHORIZED`. Human acceptance authorizes architecture-state synchronization and bounded implementation planning only, not code, schema, migration, API, Adapter, SecretStore, UI, stage, commit, or push.

The exact next sequence is:

```text
WP-13 accepted checkpoint `330adbc`
  -> Governance checkpoint `358d263`
  -> curated ADR-011 docs-only integration and independent review
  -> explicit Human ADR-011 Architecture Gate: HUMAN_ACCEPTED
  -> fresh independent review of accepted-state documentation synchronization
  -> separate Human docs-checkpoint / implementation-task authorization
  -> Pre-WP14 Runtime Contract Foundation Gate
       A. ADR-007 Timeout Cleanup Compliance
       B. Runtime Binding Contract
  -> WP-14
  -> WP-15
```
