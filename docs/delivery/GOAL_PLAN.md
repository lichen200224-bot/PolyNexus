# Codex 加強版收斂交付批次與依賴

Date: 2026-09-15 (Asia/Taipei)
Task: `ENHANCED-DELIVERY-REPLAN-01`
Status: `HUMAN_DIRECTION_APPROVED / DOCUMENTATION_CANDIDATE / FRESH_DOC_REVIEW_REQUIRED`
Product version: `UNCHANGED`
Primary scope: existing `FEATURE_WORK_PACKAGES.md` + `FEATURE_SCOPE_MATRIX.json` + frozen/source requirements. 本次不新增 PN、不重編原 FD，只調整 current-state routing、strategic runtime fleet、Control Plane 與驗收優先序。

## 1. Current routing basis

後續不得從舊 `PREP -> D0 -> D1a...` 文字推導目前進度。Current truth 先讀 `CURRENT_PRODUCT_STATE.md`。

已知遠端狀態：

- current D1B/default route: `e9538f328f409e2cb7d6868a8b79cc33ba4bdd87`;
- B01 technical branch: `ca85d22c44062d2856ab037a1ee1556ea26c70cc`, two commits ahead of D1B;
- old MCF-02 implementation `030890b3...`: `REJECTED / NOT_ADOPTED`;
- historical full-delivery planning repair `36d0fe45...`: provenance only, not current product authority.

D0/D1a/D2a/D1b/B01 remain historical delivery milestones and evidence sources. New work begins only after this documentation candidate receives a fresh independent documentation/design review and a bounded product-start receipt.

## 2. Enhanced-version execution order

| Unit | Existing FD responsibility | Required outcome | Human involvement |
|---|---|---|---|
| DOC-REVIEW | FD-22 governance | Fresh review of this exact docs candidate; no product source changes | None unless scope conflict is found |
| G0 | FD-21/22 reconciliation | Independently verify B01/current remote state; select exact safe product base; publish `CURRENT_PRODUCT_STATE` receipt | None for ordinary defects |
| D2B-01 | FD-06/07/08/19 | OpenCode real ACP runtime on current Core envelope | Only if required official login/auth is unavailable |
| D2B-02 | FD-06/07/08/19 | Gemini CLI real ACP runtime reusing generic ACP machinery | Only if required official login/auth is unavailable |
| D2B-03 | FD-06/07/08/19 | Claude Code real structured/headless runtime | Only if required official login/auth is unavailable |
| D2B-04 | FD-06/07/08/19 | Antigravity real controlled headless runtime | Only if required official login/auth is unavailable |
| D2B-05 | FD-19 | Runtime Fleet Doctor/capability/maturity matrix | None |
| D3 | FD-15/16 + FD-10.MIXED + FD-12 workflow gates | Council, role->runtime selection, structured handoff, nine templates, workflow/failure routing, Assurance integration | None in approved scope |
| D4 | FD-18 + FD-19 + required FD-02/03/17/20.OPS deltas | Unified Work Control Plane, Runtime Fleet view, monitor, existing Candidate/Human/Evidence integration and required daily-use UX | None in approved scope |
| D4-NEXT | FD-18.WS / FD-20.N1 only if source-required | Deliver only requirements that remain mandatory after reconciliation; WebSocket is not a blocker when bounded polling/reconnect satisfies scope | Exception only if requirement interpretation changes |
| T1 | FD-21 functional SIT | Cross-runtime Golden scenarios with UI->Core->runtime->Evidence/Candidate chain | None |
| T2 | FD-21 reliability/security SIT | Failure, permission, egress, secret, timeout, cleanup, drift and recovery evidence across strategic runtimes | None |
| DELIVERY | FD-21/22 | Exact completion reconciliation, operator docs, demo workflows, limitations, package/hash/evidence index | None |
| FINAL_HUMAN_UAT | `UAT_AND_RELEASE.md` | One concentrated Human-only acceptance session, including pending B01 Human closure | **Required Human intervention** |
| PROMOTION/RELEASE | separate side effect | merge/tag/release/deploy only if explicitly requested after acceptance | Separate Human authorization if desired |

## 3. D2b — Strategic Runtime Fleet

`STRATEGIC_RUNTIME_FLEET.md` is the target-specific execution contract. D2b MUST reuse the current external envelope/registry/supervisor/policy/evidence architecture and MUST NOT reintroduce the rejected `030890b3...` branch as a merge source.

Implementation order is deliberately:

```text
OpenCode ACP
  -> Gemini CLI ACP
  -> Claude Code structured/headless
  -> Antigravity headless
  -> Fleet Doctor/Capability Matrix
```

The order optimizes shared transport reuse and risk. It is not a ranking of business importance. Demo/runtime presentation may place Claude Code, Gemini or Antigravity more prominently.

Every runtime needs real target evidence for its claimed capability scope. The enhanced version does not require equal capabilities or native resume across all vendors. `UNKNOWN`, `UNSUPPORTED`, `ENVIRONMENT_BLOCKED` and `ResumeMode.NONE` are valid truthful states.

## 4. D3 — Multi-Agent collaboration without a second Agent framework

D3 reuses the existing Council and Workflow contracts rather than adding `AgentTeam`, `AgentMessage`, `AgentHandoff` or another orchestration domain.

Required outcomes:

1. Council `ANALYSIS -> CROSS_REVIEW -> SYNTHESIS` executes with real selected Runtime profiles where the scenario requires multi-runtime proof;
2. workflow role maps to normalized capability requirements, then to an eligible configured Runtime profile;
3. the actual Run receives an immutable binding; no post-dispatch silent runtime substitution;
4. handoff is represented by existing ContextPackage / Artifact / Evidence / Generation input / Run output references;
5. partial runtime failure remains visible and does not fabricate missing participant output;
6. `current role`, `current runtime`, `current stage`, `next owner` and blocking reason can be projected for D4;
7. existing nine templates and required failure/gate semantics remain source-bound and are not replaced by a generic BPM engine.

## 5. D4 — Unified Work Control Plane

D4 is a thin aggregation and UX layer over existing durable facts, not another execution engine.

### D4-01 `TaskControlSnapshot`

Add a non-persistent read model/API projection that aggregates, when applicable:

```text
task / workflow
current generation
current run
current stage
current role
current runtime/binding
last durable event
blocking reason
Evidence/Verification/Assurance state
Human gate state
next owner
next action
```

The projection must never become a second source of truth and must not infer success from missing/stale data.

### D4-02 Work Control UI

Provide a task-level operations view showing the role/runtime pipeline and exact current state. Existing GenerationControls, RunDetail and CandidateReview remain drill-down surfaces; do not rewrite their authority.

### D4-03 Runtime Fleet / Doctor

Expose normalized installed/health/readiness/maturity/verified-capability/limitation/evidence information for Codex, OpenCode, Gemini CLI, Claude Code and Antigravity.

### D4-04 Required operational UX

Complete the still-required portions of FD-17/18/19/20.OPS and Project/Artifact lifecycle after G0 reconciliation. Do not implement optional WebSocket or future platform scope merely because it would improve presentation.

## 6. T1 — Functional Golden SIT

At minimum prove these scenarios with exact evidence:

### T1-01 Coding collaboration

```text
Claude Code (architecture/analysis)
  -> Codex (implementation)
  -> OpenCode (independent review)
  -> PolyNexus deterministic verification
  -> Human gate remains pending until final UAT
```

### T1-02 Cross-model review

```text
Gemini CLI analysis
  -> Claude Code cross-review
  -> Council synthesis
```

### T1-03 Adversarial verification

```text
Codex candidate
  -> Antigravity secondary/adversarial verification
  -> Core evidence/verification
```

### T1-04 Runtime replaceability

Execute the same bounded contract through at least two approved Runtime profiles and prove that Core identity/Evidence/Candidate semantics remain vendor-independent.

A routine workflow does not have to invoke all five runtimes. The fleet breadth is demonstrated across the Golden suite.

## 7. T2 — Failure / Security SIT

Required classes include, where applicable to the target:

- executable/version mismatch;
- missing/unavailable auth;
- permission denied;
- vendor reports success but expected postcondition/source output is absent;
- malformed/partial event stream;
- cancel failure or unsupported cancel;
- timeout and child/process cleanup;
- output outside allowlist / path containment failure;
- undeclared egress / plugin/MCP/config drift;
- secret canary/redaction;
- stale generation/ownership;
- stale Candidate/Human challenge;
- runtime/config fingerprint drift;
- partial Council participant failure.

`exit 0`, vendor `SUCCESS`, a descriptor or a fixture is not sufficient by itself for PolyNexus PASS.

## 8. Codex / ChatGPT execution loop

Product development policy after DOC-REVIEW + G0 start receipt:

```text
Codex = sole product Writer + Test Executor
ChatGPT = Project PM / Architecture & Governance Authority / independent Product Acceptance Center
```

For each dependency-ready unit:

1. Codex fixes exact base/ref and bounded allowlist;
2. Codex implements, writes/runs UT/contract/SIT as required, records actual commands/exits and creates an immutable remote candidate;
3. ChatGPT independently reads canonical remote/exact SHA/actual source/diff/evidence;
4. PASS -> ChatGPT may emit `AUTHORIZED_TO_CONTINUE_WITHIN_APPROVED_SCOPE` and Codex proceeds without another Human micro-approval;
5. NEED_FIX -> ChatGPT returns the minimal repair prompt; Codex repairs to a new SHA and reruns affected/required tests;
6. repeat until PASS or an exception gate is reached.

Writer self-report is not acceptance. `SKIPPED != PASS`; negative child exits and verifier exit are distinct; fake target evidence does not establish live conformance.

## 9. Human intervention budget

After Human approval of this planning direction, the normal path targets:

- intermediate product approvals: `0`;
- final integrated Human UAT / acceptance: `1` required session;
- provider login / Windows Hello preparation: `0-1` conditional intervention if existing official auth cannot be reused safely;
- architecture/security/scope exception: `0-1` conditional intervention only when the approved invariants cannot be satisfied;
- merge/release/deployment: separate explicit action only if requested.

Thus the expected normal remaining Human intervention count is **1**. A realistic exception path is **2-3**, not one approval per D2b/D3/D4 goal.

## 10. Stop conditions

Do not auto-continue when the next action would:

- add/change frozen product semantics or a new Core authority;
- weaken classification, policy, Evidence, Human trust or lifecycle invariants;
- require unsupported/private vendor API, credential extraction or browser-session takeover;
- perform paid purchase or materially expand authorized egress/data exposure;
- mutate production/user database outside an explicitly approved migration/UAT path;
- force push, rewrite history, change default/protection, release or deploy without explicit authority;
- proceed with unresolved ownership or a required target that cannot be truthfully verified.

Ordinary defects, test repairs, adapter implementation choices and bounded compatibility fixes within the approved scope do not require Human approval.
