# 最終 UAT 與交付契約

Date: 2026-09-15 (Asia/Taipei)
Status: `HUMAN_DIRECTION_APPROVED / UAT_PLAN / ENHANCED_PRODUCT_NOT_YET_READY`
Product version: `UNCHANGED`

目標：Codex 先完成批准範圍內的開發、UT/contract/SIT/build/live target tests 與同範圍修復；ChatGPT 對每個 exact remote candidate 做獨立驗收。中間不逐 Goal 要 Human 批准。所有必要 Human-only 情境最後集中為 **一次整合 Human UAT / Final Acceptance session**。

## 1. AI 交付前入口

進入最終 Human UAT 前必須同時成立：

- `CURRENT_PRODUCT_STATE.md` 已對應最終 exact product candidate；
- D2b Strategic Runtime Fleet 的 required target capabilities 已有真實 evidence，或 source-bound 允許的限制被明確標示；
- D2B-06 FD-09 / PN-022/PN-023 的 LM Studio、Ollama、Generic compatible 三類 local endpoint 已各自有真實 health/model discovery/selection/stream/result/identity/capability evidence 與 SIT-09 positive/negative 結果；fixture 或單一 endpoint PASS 不算三個 live target 完成；
- D3 Council/Workflow/role routing 完成並有 cross-runtime evidence；
- D4 Unified Work Control Plane / Runtime Fleet Doctor 可用；
- T1/T2 required functional + failure/security SIT 通過；
- required PN/FD/source clauses 有 implementation/test/evidence/review 對應；
- 無未解 BLOCKER/MAJOR；
- final candidate 已由 ChatGPT independent Product Acceptance Center 判定 `READY_FOR_HUMAN_UAT`；
- known limitation 不能用來掩蓋 required 未完成項。

Human protocol automated tests 只能使用隔離 TEST_ONLY principal。實際 Final Acceptance、Windows Hello、人類使用體驗與其他 Human-only 決定由 Human 本人執行。

## 2. Human 介入預算

本 UAT 設計的目的之一是降低 Human 中途介入：

| 類型 | 預期次數 | 規則 |
|---|---:|---|
| D2b/D3/D4/T1/T2 中間產品批准 | `0` | Codex -> ChatGPT review -> PASS 自動續行 |
| 最終整合 Human UAT / Acceptance | `1` | 正常路徑唯一必要 Human acceptance session |
| Provider 官方 login / Windows Hello 前置 | `0-1` conditional | 僅現有安全 auth 無法使用時 |
| 架構/安全/scope exception | `0-1` conditional | 只有批准 invariants 無法滿足時 |
| merge/tag/release/deploy | separate optional | Product Accept 不自動授權發布 |

正常預期剩餘 Human 介入：**1 次**。有環境/架構例外時合理上限約 **2-3 次**。

## 3. 必交資產

- exact final source/candidate SHA、ancestry、build/package hashes；
- `CURRENT_PRODUCT_STATE` final reconciliation；
- Runtime Fleet capability/maturity/evidence matrix for Codex/OpenCode/Gemini CLI/Claude Code/Antigravity；
- 繁中使用手冊：安裝、啟動、runtime readiness、Project/Task、Work Control、Council、Candidate/Evidence/Human、取消恢復、Doctor、備份還原；
- 功能核銷：每 required PN/子項/source clause -> implementation -> test -> evidence -> review -> limitation；
- T1/T2 Golden/failure scenario evidence index；
- B01 technical + pending Human closure trace；
- P0 accepted package verify/reconstruct 方法；
- 最終人工操作表，只要求 Human 驗證真正需要使用者判斷/體驗/身份的項目，不要求閱讀全部 UT logs。

## 4. Final Human UAT scenarios

以下 HU-01–HU-12 形成**同一次集中 session**；必要時可分段休息，但不重新建立逐 Goal approval 模式。

| UAT | Human 操作 | 必要結果 | 不可接受 |
|---|---|---|---|
| HU-01 | 依手冊 clean start / restart PolyNexus | Core/UI/schema/runtime readiness分層清楚；歷史可讀；舊 durable facts 未遺失 | 開發者手改DB/隱藏global設定才可啟動 |
| HU-02 | 開 Project/Task，查看 Unified Work Control Plane | current stage/role/runtime/generation/run/blocker/next owner/next action 可理解且與 durable facts 一致 | UI 自己發明 success/next state |
| HU-03 | 查看 Runtime Fleet / Doctor | Codex、OpenCode、Gemini CLI、Claude Code、Antigravity 的 installed/readiness/maturity/capability/limitation truthfully displayed | descriptor 就全部顯示 SUPPORTED/green |
| HU-04 | 執行 Multi-Agent Golden coding flow | 至少觀察 Claude/Architect -> Codex/Implementer -> OpenCode/Reviewer 的真實接力；handoff/context 可追蹤 | 同一回答冒充多AI、無 real runtime evidence |
| HU-05 | 執行 Gemini/Claude Council 或等價 cross-model review | 可看 individual analysis、cross-review、synthesis、partial failure | 缺 participant 輸出卻產生假共識 |
| HU-06 | 執行 Antigravity secondary/adversarial verification 情境 | outer success 仍受 Core Evidence/postcondition 驗證；限制可理解 | vendor `SUCCESS`/exit0 直接變 PASS |
| HU-07 | failure/Cancel/Retry/restart | g1/g2、Run、owner/fence、cleanup、late abort 狀態清楚；安全 retry | ownership unknown 還放行新 writer |
| HU-08 | Candidate verification + exact Human decision | required evidence/eligibility 正確；Windows Hello/exact-view challenge；Accept 後對應 exact result | stale/missing evidence 可 Accept |
| HU-09 | Reject/Revoke/Supersede/takeover representative path | append-only history與 Working Copy/immutable accepted result 區分清楚 | 覆寫歷史、Accept 自動修改 Human repo |
| HU-10 | Local-only / approved cloud mixed routing representative path | runtime/egress/policy 與實際記錄一致；禁止 route fail closed | 敏感資料 silent cloud fallback |
| HU-11 | B01 closure + P0 verify/reconstruct + Backup/Restore representative path | 真實 bug-fix/recovery 技術鏈對得上 final product；P0/source/hash 可重建；secret 不出包 | 依賴私有 provider session 才可重建 |
| HU-12 | 日用 UX、九模板代表操作、Web/Local/source-required remainder | 必要 workflow/monitor/findings/assurance/metrics/操作性符合用途；known limitations 清楚 | 為 Demo 而省略 required source scope |

Human 不需在 HU-04～HU-06 每次重新批准 provider invocation；那些 runtime executions 應在 AI technical acceptance 階段已完成。Human UAT 的重點是最終產品可理解性、實際身份/decision 與 end-to-end 行為。

HU-10／HU-12 檢視 FD-09 / PN-022/PN-023 local endpoint 選擇、實際 model identity/capability 與 LOCAL_ONLY fail-closed 行為；三個 live target 的技術證據應已由 D2B-06/SIT-09 在 AI acceptance 階段逐一核對，不以 Human 的代表性操作代替。

HU-08／HU-12 涉及的 PN-078 Assurance Mode/Status 與 PN-038 attributable human override metric，依 [ASSURANCE_CONTRACT.md](ASSURANCE_CONTRACT.md) 核對；Assurance Status、metric 均不得代替 verification PASS 或 Human acceptance。

## 5. Strategic Runtime acceptance boundary

五 Runtime 都必須進產品 Fleet，但不要求 capability 完全等價。

Human 應看到 truthful matrix：

- `VERIFIED`;
- `SUPPORTED_NOT_CURRENTLY_VERIFIED`;
- `UNSUPPORTED`;
- `ENVIRONMENT_BLOCKED`;
- `UNKNOWN`.

`ResumeMode.NONE`、不支援特定 tool/MCP/plugin 或環境登入阻擋都可以是合法限制，只要不違反 source-required scope。不能為了 Demo 把未驗 capability 顯示成 green。

## 6. B01 closure policy

`codex/product-b01-tech@ca85d22c...` 的技術證據不得遺失；其 historical status `B01_TECHNICAL_READY / PENDING_FINAL_HUMAN_UAT` 保留。

最終 HU-11 將 B01 Human-only requirement 與 full enhanced-product UAT 一起結案，而不是現在再開一個中途 Human Gate。若 G0 或後續 product lineage 對 B01 技術 evidence 做了影響修改，Codex 必須先重跑 affected/required evidence 並由 ChatGPT 重新驗收，再交 Human。

## 7. UAT problem handling

UAT defect categories:

- functional mismatch;
- unusable UX/operation;
- data/security/trust issue;
- environment issue;
- actual new requirement/change request.

前四類若仍在 approved scope：

```text
Human reports issue
  -> Codex fixes
  -> new exact candidate
  -> required/affected tests
  -> ChatGPT independent re-review
  -> only affected Human scenario rerun
```

不要求 Human 重新批准修 bug 本身。

只有第五類、frozen semantic change、new authority/security/egress/cost expansion 才走 change control。

## 8. Final state and release

AI may declare only:

`READY_FOR_HUMAN_UAT`

Human may then accept/reject the exact delivered candidate and documented limitations. Product Human Accept does not automatically authorize:

- merge to another protected/default branch;
- tag/release;
- deployment;
- production DB migration;
- paid purchase;
- broader external data egress.

Those remain separate side effects requiring explicit authority when requested.
