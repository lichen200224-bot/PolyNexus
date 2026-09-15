# Runtime、模組化與真實整合設計

Date: 2026-09-15 (Asia/Taipei)
Status: `HUMAN_DIRECTION_APPROVED / DOCUMENTATION_CANDIDATE`
Product version: `UNCHANGED`

本文件保留既有 static module / runtime contracts，並把加強版的 Strategic Runtime Fleet 收斂到既有 FD-06/07/08/19。它不建立新的 Runtime authority，也不把 vendor 名稱或 descriptor 當成支援證據。

## 1. Reuse 而非重造

Static ModuleManifest/ModuleRegistry -> RuntimeModuleBridge -> RuntimeProfile/RuntimeRegistry -> Run-owned immutable RuntimeBinding -> RuntimeAdapter -> RunSupervisor。

Core 不分散 vendor if/else。Module 只供 metadata/factory/capability；不能自宣告 `VERIFIED/CERTIFIED`、不能建立 Human approval，也不能繞過 Generation/Run/Candidate/Evidence contracts。

RUNTIME/TOOL/SURFACE/INTEGRATION 只有在實作 contract + evidence 存在時才可標支援。MEMORY、remote install、hot reload、marketplace 等仍屬 future scope，不能因 Runtime Fleet 擴張而偷渡成 Plugin Platform。

## 2. Current implementation facts

Current product line already contains a real external-runtime foundation:

- Core-owned external execution envelope;
- per-Run `PROJECTED_STAGING`;
- distinct input/output allowlists;
- executable/config/policy fingerprints;
- provider-model vs extension/tool egress separation;
- RuntimeSupervisor deadline/cancel/cleanup path;
- Core-owned Artifact import/provenance;
- real Codex target evidence in the D2a/B01 lineage.

Therefore D2b must add thin target integrations and shared transport machinery, not rebuild the Core runtime subsystem.

## 3. Old MCF-02 candidate disposition

`feature/mcf-02-opencode-acp-runtime@030890b30160f1063ac2cef1d36705a9ea70bddb` is **REJECTED / NOT_ADOPTED** for current product integration.

The rejection is structural: it is not descended from the accepted/current D1a product line, its diff would remove accepted delivery/security/workspace contracts, and its ACP coverage is fixture/fake-target evidence rather than the required real-target proof.

Rules:

- do not merge/cherry-pick/copy the candidate wholesale;
- do not treat its writer tests as live OpenCode support;
- useful contract ideas may be re-derived independently against the current Core and current accepted lineage;
- D2B-01 implements OpenCode ACP anew as a thin adapter over the current external contract.

## 4. Strategic Runtime Fleet

The enhanced version must visibly support the company-strategic fleet defined in `STRATEGIC_RUNTIME_FLEET.md`:

| Runtime | Transport strategy | Enhanced-version target |
|---|---|---|
| Codex | current bounded CLI / structured result path | retain existing real reference runtime |
| OpenCode | generic ACP adapter | real deep target |
| Gemini CLI | reuse generic ACP adapter when current supported environment exposes ACP | real deep target with truthful environment constraints |
| Claude Code | supported structured/headless execution, optional supported bridge | real deep target |
| Antigravity | supported headless machine-readable stream | real controlled target |

The fleet is heterogeneous. Runtime support is per capability, not an all-or-nothing green badge.

## 5. Target evidence profile

Each target stores or exposes bounded evidence for:

- provider/runtime/adapter identity and observed version;
- executable path/content identity or equivalent strong observation;
- protocol/contract/transport identity;
- auth ownership;
- effective non-secret config/fingerprint;
- model identity visibility when available;
- capability declarations and conformance evidence;
- host/environment and fixture/live markers;
- observed cwd/workspace scope;
- result/event normalization;
- cancel/timeout/cleanup evidence for claimed capabilities;
- Artifact/provenance refs;
- evidence timestamp/scope/maturity.

A descriptor, version probe or health check is not sufficient for `REAL_VERIFIED` maturity.

## 6. Shared ACP transport

D2B-01 creates one generic bounded ACP transport/integration seam. D2B-02 reuses it for Gemini CLI when supported.

Shared ACP machinery may normalize:

- process/session setup;
- ACP request/response/event framing;
- bounded input dispatch;
- permission request projection into Core policy;
- result/event normalization;
- cancel/cleanup mapping where observed;
- target-independent failure categories.

Target-specific code remains responsible for executable discovery, version/config/auth quirks and capability truth. Generic ACP code must not silently pretend two agents have the same resume, permission, cancellation or model behavior.

## 7. Claude / Antigravity non-ACP paths

PolyNexus is a multi-transport Runtime Control Plane, not an ACP frontend.

Claude Code may use a supported structured/headless execution surface or independently justified supported bridge. Antigravity should use its supported headless machine-readable path. Neither integration may rely on browser-cookie/session extraction, private IPC reverse engineering or unsupported API takeover.

If Antigravity or another vendor reports outer success while required output/postconditions are absent, PolyNexus fails the operation. Vendor success text or process exit `0` never replaces Core postcondition/Evidence validation.

## 8. Envelope / staging sequence

Every external Run receives a new Core-created projected staging/config scope. Only approved context/files are projected. The Human project root, parent/global config home, arbitrary plugins/MCP/remote skills are not implicitly exposed.

Before launch, validate the bound executable, actual resolved non-secret config, approved permissions/egress and runtime capability declaration. Drift or unknown expansion makes the target not ready.

Binding occurs before external side effect. Envelope facts bind to the exact Run/Task/Project and cannot be reused as a mutable profile-level authorization.

## 9. Permission / egress / auth

Runtime-managed provider authentication may remain vendor-owned, but PolyNexus must not read/copy/replay raw credentials. API-key routes continue to use SecretRef when applicable.

Separate:

- provider-model egress needed for the selected runtime;
- agent extension/tool/MCP/plugin egress.

The second class remains deny-by-default unless a source-bound requirement and Core policy explicitly authorize it. `LOCAL_CHILD` does not imply local inference.

## 10. Artifact lifecycle and failure

After Supervisor-owned work becomes safely quiescent, Core validates output containment, expected postconditions, size/hash and replacement/symlink conditions before importing immutable content and provenance.

Malformed streams, unsupported requests, stale handles, permission denial, cleanup failure, partial output, config drift, result mismatch or unexpected egress fail closed. No adapter may silently switch runtime or rebind an existing Run.

## 11. Capability / maturity states

Use truthful normalized states such as:

- `VERIFIED`;
- `SUPPORTED_NOT_CURRENTLY_VERIFIED`;
- `UNSUPPORTED`;
- `ENVIRONMENT_BLOCKED`;
- `UNKNOWN`.

Native resume may legitimately be `NONE`. Cancel capability is distinct from timeout-cleanup verification. Process cleanup is distinct from remote provider cancellation. One runtime's evidence never promotes another runtime.

## 12. Runtime selection

The enhanced version uses explicit or policy-bounded role/capability selection:

```text
Workflow role
  -> normalized capability requirements
  -> eligible configured runtime profiles
  -> selected profile
  -> immutable RuntimeBinding
```

Do not implement an autonomous cost/quality optimizer or silent runtime fallback as a completion requirement. Those remain future enhancements after enough real telemetry exists.

## 13. Runtime Fleet Doctor

D2B-05 / FD-19 exposes at least:

```text
runtime_id
provider
transport
observed_version
installed
health
readiness
maturity
verified_capabilities
unsupported_capabilities
environment_blockers
auth_ownership
egress_profile
last_verified_at
evidence_ref
```

The UI may present these facts compactly, but it must not turn `UNKNOWN`, `ENVIRONMENT_BLOCKED` or partial capability evidence into `SUPPORTED`/green success.

## 14. Replaceability acceptance

Under the same Core task/workflow contract, at least two approved Runtime profiles must be swappable without adding Core vendor branching or altering historical Run/Candidate identities. Golden SIT further demonstrates the broader five-runtime fleet across multiple scenarios; routine workflows are not required to invoke all five agents.
