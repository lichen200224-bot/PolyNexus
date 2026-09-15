# Strategic Runtime Fleet

Date: 2026-09-15 (Asia/Taipei)
Task: `ENHANCED-DELIVERY-REPLAN-01`
Status: `HUMAN_DIRECTION_APPROVED / DOCUMENTATION_CANDIDATE / IMPLEMENTATION_NOT_STARTED`
Product version: `UNCHANGED`

本文件定義加強版 Demo 與產品收斂所需的公司主力 Runtime Fleet。它不新增新的 Core authority、PN 或產品版本，也不把 vendor 名稱本身當作支援證據。所有 Runtime 都必須服從既有 PolyNexus Core lifecycle、policy、evidence、Human Gate 與 immutable binding。

## 1. Product objective

PolyNexus 的加強版必須以實際執行證明「一個控制面可治理多個公司主力 Agent Runtime」，而不只是宣稱架構可替換。

Required strategic fleet:

| Runtime | Enhanced-version role | Preferred transport | Required maturity |
|---|---|---|---|
| Codex | existing reference deep runtime | bounded CLI / structured JSONL path already evidenced in D2a/B01 | retain real verified baseline |
| OpenCode | ACP reference runtime | ACP | real deep execution |
| Gemini CLI | Google CLI runtime | reuse generic ACP adapter where current supported surface allows | real deep execution, truthful environment limitations |
| Claude Code | primary architecture/review runtime | supported headless / structured execution; ACP bridge only when independently justified | real deep execution |
| Antigravity | Google strategic agent runtime | supported headless machine-readable stream; do not invent ACP support | real controlled execution |

Support does not mean equal capability. Each runtime exposes only independently observed capabilities.

## 2. Shared Core contract — MUST reuse

Every new runtime adapter MUST reuse the current Core-owned path:

```text
Static Module / Runtime profile
  -> RuntimeRegistry
  -> immutable RuntimeBinding
  -> Core-owned external execution envelope
  -> PROJECTED_STAGING
  -> RunSupervisor
  -> vendor adapter / transport
  -> normalized observations/results
  -> Core Artifact / Evidence / Candidate / Verification
```

Adapters MUST NOT create a second workspace authority, policy engine, Evidence authority, Human decision path, Candidate identity, retry model or accepted-result model.

The following remain Core-owned and cannot be relaxed per vendor:

- exact Project / Task / WorkGeneration / Run identity;
- input/output allowlists and path containment;
- executable/config/policy fingerprinting;
- egress classification and decision;
- SecretRef / runtime-managed-auth boundary;
- timeout, cancel and cleanup truthfulness;
- artifact import and provenance;
- Evidence/Verification/Assurance classification;
- Human exact-view decision authority.

## 3. Minimum real-runtime contract

A runtime can be shown as `REAL_VERIFIED` for the enhanced version only when the target-specific evidence proves, within its declared capability scope:

1. actual executable identity/version observation;
2. actual bounded working directory under a Core-controlled workspace;
3. real task dispatch through the supported transport;
4. at least one real allowed source/output modification or equivalent target-specific result where code modification is not the declared use case;
5. normalized terminal result rather than trusting an outer `success` string alone;
6. bounded stdout/stderr/event capture appropriate to the transport;
7. timeout behavior and Core-owned deadline;
8. cancel/cleanup behavior according to the capability actually claimed;
9. process/session ownership evidence sufficient for the claimed cleanup scope;
10. input/output containment and postcondition verification;
11. provider-model vs extension/tool egress declaration;
12. sanitized Artifact/Evidence provenance;
13. positive and negative target-specific tests;
14. no silent fallback to another runtime when the selected target cannot satisfy the contract.

`ResumeMode.NONE` is acceptable. Native resume is not a completion requirement unless a source-bound requirement explicitly demands it.

## 4. D2b implementation order

The implementation order optimizes reuse and risk, not business importance:

### D2B-01 — OpenCode ACP

Purpose: establish the generic ACP execution path on top of the current external envelope.

Minimum scope:

- real `opencode` executable/version probe;
- Core-created projected staging;
- ACP session/create/dispatch/event/result mapping required by the approved scope;
- cancel/timeout/cleanup according to independently verified capability;
- real source/result evidence;
- config/plugin/MCP/skill state bound or explicitly `NONE`/unsupported;
- no reuse of the rejected `030890b3...` branch as a merge source. Useful ideas may only be re-derived against the current accepted lineage and current contracts.

### D2B-02 — Gemini CLI ACP

Purpose: prove the generic ACP path can support a second independent vendor without Core vendor branching.

Reuse D2B-01 protocol machinery. Target-specific code is limited to executable discovery/version, launch/config/auth/maturity declaration and documented quirks. If the installed/account environment does not expose the required supported Gemini CLI ACP path, mark the exact capability `ENVIRONMENT_BLOCKED` or `UNSUPPORTED`; do not substitute another Google product while claiming Gemini CLI PASS.

### D2B-03 — Claude Code

Purpose: prove PolyNexus is not only an ACP frontend and can control another mature structured headless runtime.

Minimum scope:

- supported headless/structured-output invocation;
- real bounded code/review task;
- event/result normalization;
- permission and side-effect mapping into Core policy;
- cancellation/timeout/cleanup only to the extent independently observed;
- exact version/auth/provenance;
- no browser-cookie/session extraction or unsupported private API.

An ACP bridge may be used only when it is a supported, independently verifiable integration surface and does not move lifecycle authority outside PolyNexus.

### D2B-04 — Antigravity

Purpose: include the company-strategic Antigravity runtime in the same control plane without depending on desktop UI automation.

Preferred path: supported headless machine-readable CLI output/stream. Runtime success requires Core postcondition/result validation. `exit 0` or vendor `SUCCESS` alone is not PolyNexus PASS.

Minimum negative cases include permission denial, no expected output change, malformed/partial machine stream, timeout and cleanup behavior. Unsupported native features remain visibly unsupported rather than emulated by weakening Core controls.

### D2B-05 — Runtime Fleet Doctor / Capability Matrix

Expose a truthful normalized read model:

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

A descriptor or health probe alone must never upgrade maturity to `REAL_VERIFIED`.

### D2B-06 — FD-09 Local AI endpoints (PN-022/PN-023)

This is a separate, still-required D2b work unit after the five strategic Runtime Fleet units; it does not replace or enlarge that five-runtime vendor list. Its declared dependencies are FD-05 lifecycle/binding and FD-10 policy/SecretRef. After G0 reconciles their actual state, Codex may execute the dependency-ready unit without claiming that the Fleet Doctor is an FD-09 technical prerequisite.

LM Studio, Ollama and Generic compatible local endpoints each need real target-specific health, model discovery/selection, stream/result and actual model identity/capability evidence. Existing local adapter source or fixture tests do not prove the three live targets, and one endpoint's result cannot stand in for another. Unsupported structured output/cancel must be explicit; unknown model, timeout, malformed stream and LOCAL_ONLY routing failure must remain truthful and fail closed. Complete FD-09 positive/negative evidence and SIT-09 before D3/T1 completion or final delivery readiness; an exact candidate still requires independent review.

## 5. Capability truthfulness

The fleet is intentionally heterogeneous. Example capability states are `VERIFIED`, `SUPPORTED_NOT_CURRENTLY_VERIFIED`, `UNSUPPORTED`, `ENVIRONMENT_BLOCKED`, `UNKNOWN`.

Do not force a fully green matrix. In particular:

- native resume may be `NONE`;
- vendor-managed conversation/session continuation may be unsupported;
- arbitrary MCP/plugin/remote skills are not enabled merely because the vendor supports them;
- cancel support is separate from verified timeout cleanup;
- process cleanup and remote provider cancellation are separate claims;
- model identity visibility may differ by provider;
- account/subscription availability is environment evidence, not a product guarantee.

## 6. Routing policy for the enhanced version

The enhanced version does NOT require an autonomous cost/quality optimizer. Runtime choice remains explicit or policy-bounded by role/capability, followed by immutable binding for the actual Run.

Allowed enhanced-version pattern:

```text
Workflow role
  -> required normalized capabilities
  -> eligible configured runtime profiles
  -> explicit/policy-bounded selection
  -> immutable RuntimeBinding for the Run
```

Do not add an AI-controlled silent fallback or change the bound runtime after dispatch.

## 7. Demo / Golden role examples

The product must support role-to-runtime demonstrations without requiring every workflow to invoke every runtime:

```text
Architect / Analysis     -> Claude Code
Implementer              -> Codex
Independent Reviewer     -> OpenCode
Cross-check              -> Gemini CLI
Adversarial Verification -> Antigravity
Deterministic validation -> PolyNexus Core
Final decision           -> Human
```

Other workflows may use only the necessary subset. A five-runtime demo proves fleet breadth; it is not a rule that routine work must always consume five providers.

## 8. Stop / exception conditions

Stop the affected target and issue an exception packet instead of widening scope when:

- the only available path requires private/unsupported vendor APIs, credential extraction or browser-session takeover;
- required runtime login/auth cannot be completed without the Human;
- the installed version no longer exposes the documented transport;
- satisfying the target would require weakening Core lifecycle, Evidence, Human or egress invariants;
- a new dependency materially changes security, licensing, deployment or cost beyond the approved envelope;
- target behavior cannot be verified without real external side effects outside the authorized test scope.

Other independent D2b targets may continue when their dependencies are ready.
