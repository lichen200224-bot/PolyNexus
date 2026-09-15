# PolyNexus 加強版收斂：唯一文件與開工入口

Date: 2026-09-15 (Asia/Taipei)
Task: `ENHANCED-DELIVERY-REPLAN-01`
State: `HUMAN_DIRECTION_APPROVED / DOCUMENTATION_CANDIDATE / FRESH_DOC_REVIEW_REQUIRED`
Active branch: `planning/enhanced-runtime-control-plane`
Product version: `UNCHANGED`
Product implementation: `NO_NEW_PRODUCT_WRITES_UNTIL_FRESH_DOC_REVIEW_PASS`

Human 已批准依目前實際產品進度重新收斂後續開發：保留既有 Core/Generation/Runtime/Evidence/Human 架構，加入公司主力 Strategic Runtime Fleet、Multi-Agent Council/Workflow 與 Unified Work Control Plane；Codex 全開發測試，ChatGPT 驗收 exact product candidate，PASS 後可在批准範圍內自動續下一批，Human 正常只在最後集中 UAT / Final Acceptance 介入。

本 docs patch 由 ChatGPT 撰寫，因此不能由同一 Writer 自我宣告 fresh docs PASS。正式產品新寫入先完成 `DESIGN_REVIEW.md` 的 exact remote review，再進 `G0`。

## 1. Current-state reading order

| 目的 | 入口 |
|---|---|
| **目前真正產品/remote/acceptance狀態** | [CURRENT_PRODUCT_STATE](CURRENT_PRODUCT_STATE.md) |
| **五 Runtime 加強版契約** | [STRATEGIC_RUNTIME_FLEET](STRATEGIC_RUNTIME_FLEET.md) |
| 後續批次/順序/人為介入 | [GOAL_PLAN](GOAL_PLAN.md) |
| AI/Codex/ChatGPT/Human 權限 | [EXECUTION_CONTRACT](EXECUTION_CONTRACT.md) |
| Fresh docs review | [DESIGN_REVIEW](DESIGN_REVIEW.md) |
| Codex 正式接手入口 | [CODEX_HANDOFF](CODEX_HANDOFF.md) |
| Runtime / module details | [RUNTIME_AND_MODULES](RUNTIME_AND_MODULES.md) |
| Unified Control Plane / UX | [UX_SPEC](UX_SPEC.md) |
| Final concentrated Human UAT | [UAT_AND_RELEASE](UAT_AND_RELEASE.md) |
| 原 required 功能/FD/PN | [FEATURE_WORK_PACKAGES](FEATURE_WORK_PACKAGES.md)、[FEATURE_SCOPE_MATRIX](FEATURE_SCOPE_MATRIX.json)、[REQUIREMENTS](REQUIREMENTS.md) |
| Frozen/source authority | [SOURCE_LOCK](SOURCE_LOCK.json)、[SOURCE_INDEX](SOURCE_INDEX.md) |

其他 full-delivery/frozen/reference 文件保留來源與歷史證據；其過期 `NEXT_GOAL`、`NOT_STARTED`、`HOLD`、舊 branch routing 不再是 active current-state authority。

## 2. Current product facts to preserve

At planning time, canonical remote facts included:

```text
D1B/current default route:
  e9538f328f409e2cb7d6868a8b79cc33ba4bdd87

B01 technical candidate:
  codex/product-b01-tech
  ca85d22c44062d2856ab037a1ee1556ea26c70cc

old MCF-02 candidate:
  030890b30160f1063ac2cef1d36705a9ea70bddb
  REJECTED / NOT_ADOPTED
```

Fresh reviewers/controllers must re-read remote truth; these values are not permission to skip verification.

D1B evidence records bounded technical + isolated Human product acceptance. B01 records technical readiness/fresh engineering review but still `PENDING_FINAL_HUMAN_UAT`. Neither status equals full enhanced-product completion/release.

## 3. What this replan changes

This replan changes delivery order and completion emphasis, not frozen product identity:

- D2b becomes **Strategic Runtime Fleet**: OpenCode, Gemini CLI, Claude Code, Antigravity on top of existing Codex/reference runtime;
- D2b also retains separate **FD-09 / PN-022/PN-023 Local AI** scope: real LM Studio, Ollama and Generic compatible local endpoint evidence in D2B-06; the five strategic vendor runtimes do not close it;
- D3 completes **Council / role->runtime / structured handoff / workflow/templates** without a new Agent framework;
- D4 completes **Unified Work Control Plane + Runtime Fleet Doctor** as a thin read-model/UX layer;
- T1/T2 prove functional cross-runtime Golden scenarios and failure/security truthfulness;
- Final Human-only work is concentrated into one integrated UAT session.

No new PN or version bump is created. Existing FD responsibility remains authoritative.

## 4. What is explicitly not rebuilt

Do not create parallel authority for:

- Project/Task/WorkGeneration/Run/Candidate;
- workspace ownership/retry;
- RuntimeBinding/RunSupervisor;
- ContextPackage/Artifact/Evidence/Finding;
- verification/Assurance/Human exact-view decision;
- Council lifecycle;
- policy/egress/SecretRef.

Do not reintroduce duplicate `AgentSession`, `AgentMessage`, `AgentHandoff`, `AgentWorkspace` domains simply to copy another multi-agent product shape.

## 5. Current execution routing

After fresh docs review PASS:

```text
G0 Current/B01 reconciliation
  -> D2B-01 OpenCode ACP
  -> D2B-02 Gemini CLI ACP
  -> D2B-03 Claude Code
  -> D2B-04 Antigravity
  -> D2B-05 Runtime Fleet Doctor
  -> D2B-06 FD-09 Local AI endpoints (LM Studio/Ollama/Generic compatible)
  -> D3 Multi-Agent Council/Workflow
  -> D4 Unified Work Control Plane
  -> D4-NEXT only source-required remainder
  -> T1 Functional Golden SIT
  -> T2 Failure/Security SIT
  -> DELIVERY
  -> FINAL_HUMAN_UAT
```

Codex product candidates are independently reviewed by ChatGPT. A ChatGPT PASS may authorize the next already-approved dependency-ready unit without another Human response.

## 6. Human boundary

Expected normal remaining Human involvement after this planning approval: **1** concentrated final UAT/acceptance session.

Conditional Human involvement only when actually required:

- official provider login / Windows Hello cannot safely be reused;
- architecture/frozen/security/scope exception;
- separate release/merge/deploy/payment/production-data action.

Ordinary bugs, adapter fixes, tests, regressions and same-scope compatibility work remain Codex -> ChatGPT review loops.

## 7. Publication boundary

This branch is documentation/planning only. Do not infer that publishing these documents accepts B01, starts D2b, merges any branch, changes default/protection, releases software or promotes the product version.
