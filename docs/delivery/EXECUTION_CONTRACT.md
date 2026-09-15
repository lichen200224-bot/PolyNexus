# 有界 AI 批次執行契約

Date: 2026-09-15 (Asia/Taipei)
Task: `ENHANCED-DELIVERY-REPLAN-01`
Status: `HUMAN_DIRECTION_APPROVED / DOCUMENTATION_CANDIDATE / PRODUCT_START_REQUIRES_FRESH_DOC_REVIEW`
Product version: `UNCHANGED`

## 1. 當前 Human 授權

Human 已明確批准加強版收斂方向，包含：

- 以 current remote truth 重新整理後續開發順序；
- Strategic Runtime Fleet 納入 Codex、OpenCode、Gemini CLI、Claude Code、Antigravity；
- 不新增第二套 Agent/Core authority，優先重用既有 Runtime/Generation/Council/Workflow/Evidence/Human contracts；
- Codex 擔任產品唯一 Writer + Test Executor；
- ChatGPT 擔任 Project PM / Architecture & Governance Authority / independent Product Acceptance Center；
- 在批准範圍內，Codex candidate 經 ChatGPT 獨立 PASS 後可以直接進下一 dependency-ready unit，不再逐 Goal 要 Human 批准；
- Human 正常情況只在最後集中 Human UAT / Final Acceptance 介入。

本輪 Human 授權同時允許 ChatGPT 更新本 planning/documentation branch。**它尚不等於立即啟動新的產品寫入。** 本文件 patch 是 ChatGPT Writer 產物，必須先由 fresh independent documentation/design reviewer 對 exact remote candidate 做只讀審查；通過後才能產生新的 bounded product-start receipt。

## 2. Authority / role model

### Documentation phase

- ChatGPT: documentation Writer / planner。
- Fresh documentation reviewer: 不是本 patch Writer；驗 exact SHA、source facts、scope mapping、routing、安全與驗收契約。
- Human: 已批准方向，不需要再逐條批准普通文件修正；只有 scope/architecture/trust 重大衝突才回 Human。

### Product phase

- `Codex = SOLE_PRODUCT_WRITER + TEST_EXECUTOR`。
- `ChatGPT = PROJECT_PM + ARCHITECTURE_GOVERNANCE_AUTHORITY + INDEPENDENT_PRODUCT_ACCEPTANCE_CENTER`。
- Human = final product acceptance authority and exception authority defined below.

Codex 不能 final-accept 自己的 product candidate。ChatGPT 驗收 exact Codex candidate 時不得修改該 candidate；finding 必須回 Codex，修復形成新 SHA 再驗。

## 3. Current-state prerequisite

產品開工前先讀：

1. `CURRENT_PRODUCT_STATE.md`;
2. `STRATEGIC_RUNTIME_FLEET.md`;
3. `GOAL_PLAN.md`;
4. current exact documentation review receipt;
5. canonical remote refs and actual candidate ancestry.

Do not reactivate stale routing from historical `PREP`, old `HOLD`, old `NEXT_GOAL`, old MCF or copied source documents.

The first product action is `G0 Current/B01 reconciliation`:

- independently verify `codex/product-b01-tech@ca85d22c44062d2856ab037a1ee1556ea26c70cc` and its ancestry/evidence;
- determine whether it is the safe next technical base;
- if not, preserve accepted D1B `e9538f328f409e2cb7d6868a8b79cc33ba4bdd87` and issue a bounded B01 repair route;
- do not treat the rejected `030890b3...` MCF-02 branch as an integration source.

## 4. 權限表

| Action | Documentation phase | After fresh docs PASS + G0/start receipt |
|---|---|---|
| planning/docs update, scope/routing/evidence references | ChatGPT may write/publish non-force | maintain only as needed |
| product source/tests/dependencies/migrations | NO | Codex only, inside approved unit/allowlist |
| UT/contract/SIT/build/live bounded target tests | planning only | Codex executes and records actual commands/exits |
| product candidate commit/non-force push | NO | Codex may publish immutable candidates |
| exact candidate independent acceptance | docs patch requires fresh non-writer reviewer | ChatGPT reviews Codex product candidate read-only |
| same-scope bug repair and required regressions | docs writer may repair docs | Codex auto-repair -> new SHA -> ChatGPT re-review |
| continue to next approved unit | NO product start before gate | ChatGPT PASS may authorize automatically |
| provider official login / Windows Hello | not automated if unavailable | Human only when required by actual environment |
| release/default branch/ruleset/force/history rewrite/deploy | NO | separate explicit Human authorization |
| paid purchase/material egress expansion/production DB | NO | only with explicit pre-existing or new Human authority |

## 5. Batch execution protocol

Each product unit MUST start with an exact execution receipt containing:

- task/unit ID;
- canonical remote repository;
- exact accepted/reviewed base SHA and expected branch;
- current remote tip read-back;
- selected FD/PN/source-bound responsibilities;
- actual changed-file allowlist / protected areas;
- runtime/target/auth ownership/egress envelope;
- finite resource/time/budget limits where applicable;
- required UT/contract/SIT/build/live evidence;
- stop conditions;
- next reviewer.

Codex then performs implementation + tests + evidence in one bounded unit. Ordinary engineering decisions and same-scope defect fixes are delegated to Codex and must not be returned to Human as micro-approvals.

## 6. Product acceptance loop

For every immutable Codex candidate:

```text
Codex publishes exact candidate + evidence
  -> ChatGPT independently reads remote truth
  -> verify SHA / ancestry / diff / actual source / commands / exits / negative evidence
  -> PASS or NEED_FIX/BLOCKED
```

PASS conditions are source-bound. Writer narrative, dashboard state or `PASS` strings are not sufficient.

Rules:

- `SKIPPED != PASS`;
- `NOT_RUN / UNKNOWN / STALE != PASS`;
- fake/simulator evidence cannot prove real target capability;
- vendor `SUCCESS` / exit `0` cannot replace postcondition/Evidence validation;
- negative child exit and checking-runner exit are different facts;
- old accepted scope is not silently reopened by a later unrelated failure;
- finding repair creates a new immutable SHA; reviewed SHA is never amended away.

### Automatic continuation

If ChatGPT returns `PASS` and the next unit is already covered by this approved plan, ChatGPT may issue:

`AUTHORIZED_TO_CONTINUE_WITHIN_APPROVED_SCOPE`

Codex may proceed directly. No additional Human response is required.

## 7. Approved product units

The approved sequence is defined in `GOAL_PLAN.md`:

```text
G0
D2B-01 OpenCode ACP
D2B-02 Gemini CLI ACP
D2B-03 Claude Code
D2B-04 Antigravity
D2B-05 Runtime Fleet Doctor
D3 Multi-Agent Council/Workflow
D4 Unified Work Control Plane
D4-NEXT only source-required remainder
T1 Functional Golden SIT
T2 Failure/Security SIT
DELIVERY
FINAL_HUMAN_UAT
```

This sequence does not add PN or change frozen acceptance semantics. Units map to existing FD responsibilities.

## 8. Exception gates — when Human is required

Stop only the affected action and preserve safe continuation when any of the following is true:

1. a required official provider login/Windows Hello ceremony cannot be performed without the Human;
2. satisfying the work requires changing frozen semantics, public authority boundaries or introducing a new Core domain/authority;
3. proposed integration needs unsupported/private API, cookie/session extraction, credential replay or security-boundary bypass;
4. required change materially weakens classification, Evidence, Human trust, egress, ownership or cleanup invariants;
5. new cost/payment, data exposure, external side effect or production database mutation is outside existing authority;
6. force push/history rewrite/default-branch/protection/release/deployment is proposed;
7. unresolved ownership, corrupted accepted history or source conflict makes safe continuation impossible.

The exception packet must contain exact blocker evidence, affected scope, safe preserved SHA, independent work that can continue, minimum Human decision and recommended option.

Do not ask the Human merely because a normal unit test fails or an adapter requires ordinary bounded repair.

## 9. Strategic Runtime rules

All runtime adapters remain subordinate to `STRATEGIC_RUNTIME_FLEET.md` and the existing Core external contract.

- Codex is the existing real reference runtime.
- OpenCode establishes the generic ACP reference path.
- Gemini CLI should reuse the generic ACP path when its installed/supported environment exposes it.
- Claude Code uses a supported structured/headless path or independently justified bridge; PolyNexus is not limited to ACP.
- Antigravity uses a supported headless machine-readable path; do not fabricate ACP support.
- capability equality is not required;
- `ResumeMode.NONE`, `UNSUPPORTED`, `UNKNOWN` and `ENVIRONMENT_BLOCKED` are valid truthful states;
- no silent auto-fallback or post-dispatch runtime rebinding.

## 10. Human-intervention budget

Expected normal remaining Human involvement after approval of this plan:

- intermediate development approval: `0`;
- final integrated Human UAT / acceptance: `1` required session;
- provider login / Windows Hello: `0-1` conditional intervention;
- architecture/security/scope exception: `0-1` conditional intervention;
- merge/release/deploy: separate optional authorization if requested.

Normal expected count: **1**. Realistic exception path: **2-3**.

## 11. Final Human boundary

B01, future multi-runtime workflows and Human decision protocol may be technically exercised with controlled fixtures or prior isolated evidence, but final enhanced-product acceptance remains Human-only.

AI endpoint is `READY_FOR_HUMAN_UAT`, not `HUMAN_ACCEPTED`, `SIGNED`, `RELEASED` or `PRODUCTION_READY`.

Final UAT is concentrated in `UAT_AND_RELEASE.md`. Same-scope UAT defects return to Codex -> new SHA -> affected/required tests -> ChatGPT independent re-review -> only affected Human scenario rerun. Human does not reapprove every repair.

Product acceptance does not automatically authorize merge, push to another protected ref, tag, release, deploy or production data migration.
