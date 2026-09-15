# UI / UX 流程與使用者驗收設計

Date: 2026-09-15 (Asia/Taipei)
Status: `HUMAN_DIRECTION_APPROVED / DOCUMENTATION_CANDIDATE`
Product version: `UNCHANGED`

首頁仍 Project -> Discuss/Review/Validate；Develop 屬動作，不新增頂層入口。Runtime/Model/Policy/Doctor 以 progressive disclosure 展開。加強版新增的是「Unified Work Control Plane」的聚合視圖，不是另一套執行引擎。

## 1. 畫面與必要狀態

| Screen | 必要內容/主要 action | Empty/loading/error 與安全行為 |
|---|---|---|
| Workspace/Project | Create/Open/Archive、分類、近期 Task 與結果 | 無專案提供 Create；load/error可重試，Archive不刪 accepted 歷史 |
| Task setup | mode/template、目的/scope/AC、context/artifact選擇、repo/baseline | 明示缺必填/不相容；未選 dirty 預設排除，顯示 excluded 數量而非洩露內容 |
| **Work Control** | current stage/role/runtime/generation/run/state/blocker/next owner/next action、Evidence/Verification/Human Gate 摘要 | missing/stale 不推論；durable source unavailable 時標 UNKNOWN/STALE，不自行猜下一步 |
| Run preparation | role/runtime/model、分類/目的地、可用能力、budget、必要批准 | 分開 installed/health/readiness/policy；not ready不可按 Start；無 silent fallback |
| Work monitor | generation/Run、4-axis facts、進度、events、cancel/abort、recovery | HTTP accepted顯示準備中，不假 RUNNING；連線失敗保留上次 observed time 並重連查 durable |
| Discuss/Council | 各 role 原稿、runtime、cross review、共識/分歧/風險 | partial role失敗可查看已完成輸出；不可杜撰缺失結果 |
| Review findings | artifact/code位置、severity、來源、理由、建議 | 可篩選/定位；AI opinion與tool evidence有不同標籤 |
| Candidate view | exact Candidate/publication、變更摘要/檔案、requirements、validation | 不使用浮動 latest 替換頁面；switch candidate清除舊 challenge |
| Verification | required/optional、applicability、outcome、validity、command/evidence | SKIPPED/ERROR/MISSING/STALE/MISMATCH均可理解；required缺證阻 Accept |
| Human decision | exact view＋eligibility、Accept/Reject或Revoke/Supersede | 只有 Human session可操作；無 Override；stale刷新並再次呈現內容 |
| Accepted result | immutable accepted內容、歷史accepted、current disposition | Open Accepted Managed Worktree；takeover後大字標 Working Copy based on Candidate，不冒稱 immutable |
| Web handoff | launch/fill/confirm-send/capture/associate | capture失敗明示 clipboard/manual/launch-only，不自動再send |
| **Runtime Fleet / Doctor** | Codex/OpenCode/Gemini/Claude/Antigravity transport/version/health/readiness/maturity/capabilities/limitations/evidence | UNKNOWN/ENVIRONMENT_BLOCKED/UNSUPPORTED 不轉綠；descriptor != verified capability |
| Settings/Doctor | config來源、versions、capabilities/maturity、routing、resources | 未測 UNKNOWN、不具備 UNSUPPORTED；敏感設定只顯示 reference |
| Export/Backup | P0/N1/backup明確分別、scope、hash/closure結果 | failure不產生看似完整套件；不匯出 Human session或secret |

## 2. Unified Work Control Plane

### 2.1 `TaskControlSnapshot`

D4 應提供一個**非持久化**聚合 read model。它不是新 Domain entity、不是 DB table、不是第二 source of truth。

Minimum projection:

```text
task_id
workflow_id / workflow_version
current_generation
current_run
current_stage
current_role
current_runtime_profile / runtime identity
current_state
last_durable_event / observed_at
blocking_reason
evidence_state
verification_state
assurance_state
human_gate_state
next_owner
next_action
```

Projection 必須從既有 durable facts / registry / workflow / council / candidate 讀取。欄位無法安全推導時回 `UNKNOWN`/`null`/bounded reason，不以 UI convenience 製造狀態。

### 2.2 Control Plane presentation

典型顯示可以是：

```text
ARCHITECT     Claude Code    COMPLETED
IMPLEMENTER   Codex          COMPLETED
REVIEWER      OpenCode       RUNNING
CROSS-CHECK   Gemini CLI     WAITING
VERIFY        Antigravity    BLOCKED
HUMAN         Human          NOT_REQUIRED
```

每列至少可連到其 exact Run/Council/Candidate/Evidence surface。`next owner` 必須來自 workflow/routing facts，不從 provider name 或「最新 Run」猜測。

### 2.3 Thin index rule

Work Control 只做聚合/導航/狀態理解。既有 `GenerationControls`、`RunDetail`、`CandidateReview`、Evidence/Findings/Doctor 仍是細節與 authoritative action surface。不要把所有操作重做成第二套 dashboard action engine。

## 3. Runtime Fleet UX

Runtime Fleet 必須讓使用者理解「支援」是 capability-based，而非品牌 badge。

每 runtime 最少顯示：

```text
name/provider
transport
observed version
installed
health
readiness
maturity
verified capabilities
unsupported/unknown capabilities
auth ownership / environment blocker
egress profile
last verified timestamp
evidence link
```

Canonical maturity examples:

- `VERIFIED`;
- `SUPPORTED_NOT_CURRENTLY_VERIFIED`;
- `UNSUPPORTED`;
- `ENVIRONMENT_BLOCKED`;
- `UNKNOWN`.

不要要求五個 runtime 功能全等價。`ResumeMode.NONE` 可以正常顯示；cancel、timeout cleanup、remote provider cancellation 必須是不同 capability claim。

## 4. 主要操作流程

### Engineering

開 Project -> 選 Review/Validate 與 bug-fix workflow action -> 選乾淨 baseline 或明選 dirty snapshot -> 確認 scope/AC/runtime/route -> Begin/Start -> Work Control/Monitor -> freeze -> deterministic驗證 -> exact diff -> Human Accept -> Open Accepted Result -> export。

這條必須在真實 UI/SIT 中測，不可只用 API 成功冒充。

### General document work

選 Artifact -> Review/Discuss 模板 -> 選 role/AI -> 查看各自結果與分歧 -> Validate 所需 rules -> Evidence -> Decision。流程不要求使用者理解 RuntimeBinding 或手動編 JSON。

### Multi-Agent collaboration

角色與 runtime 是可見的兩個維度。例如 Architect=Claude Code、Implementer=Codex、Reviewer=OpenCode。Role 是 workflow responsibility；Runtime 是該次 Run 的 immutable execution choice。UI 不把 provider 名稱當 role。

### Retry

畫面先說明舊 generation 與原因、舊 writer 是否安全釋放、選擇續用/變更 input；執行後顯示新的 g2。舊 g1 的 Cancel/Abort 始終綁 exact target，不能指向 latest Run。

## 5. Human decision exact-view

View 包含 CandidateID、選定 publication、source/requirements/validation references、checks/evidence eligibility、當前 review/decision revision。前端不得從 local storage 組合一份不存在於 server 的 accepted view。

使用者選 Accept 時取得/使用 fresh challenge；任何 source/policy/evidence/candidate/revision 改變立即失效。Server 提交時再次驗證。Double-click/斷線重送同 command 回同一 receipt；無法確認結果時先 GET receipt/decision，不建新 Accept。

Reject 只適用未 accepted Candidate。accepted 後顯示 Revoke 與選定已有效接受 replacement 的 Supersede；不將舊 Accept 塗改為 Reject。歷史 accepted 與目前失效/撤銷要同時看得懂。

## 6. 控制與例外

Cancel 是 Run、Abort 是 generation，確認對話框列 exact target 與影響範圍；不以同一「停止全部」偷偷混合。cleanup unknown 時標等待安全恢復，不能誘導點 Start 繞過鎖。

權限/分類/目的地變更呈現差異，若需 Human-required approval 則真的停在 gate。一般可由既有 Core policy 允許的 local 動作不新增多餘確認。產品必要 Human gate 不受開發批次授權影響。

Runtime 不可用時不 silent fallback。可呈現可選的其他 eligible profiles，但切換需要形成新的合法 execution choice / Run binding，不修改已 dispatch 的 Run。

## 7. 無障礙 / 防誤用

所有主要 action 可 keyboard 操作、具有 label 與可見 focus；modal 進出回復 focus；錯誤不只靠顏色。長內容分區/搜尋/可展開 raw evidence，但不把 raw secrets/server traceback 直接塞畫面。

狀態訊息區分 working、partial、needs action、verified、accepted、unsupported、environment blocked，避免單一綠色 Success 混淆。

重要 action 保留 idempotency 與 disabled pending；refresh/back 不重送副作用。空/慢/離線/無權限/部分資料/長 log 皆有驗收例子。

## 8. Polling / WebSocket scope

目前既有 bounded polling + reconnect 可以作為加強版完成路徑，只要 T1/T2/Human UAT 證明 durable facts 不遺失且狀態延遲可接受。

`FD-18.WS` 只有在 frozen/source requirement 仍明確 required，或實測證明 polling 無法滿足 required UX 時才成為 blocker。不要為視覺即時性額外建立另一套 event truth。

## 9. UX oracle

UJ-01–UJ-10 與後續 Control Plane/Fleet cases 必須記錄 route、輸入、預期/實際、artifact/screenshot與 negative path。成功要能由 UI -> server durable state -> evidence 交叉確認；screenshot不是內容完整性證據。

Final user experience 由 `UAT_AND_RELEASE.md` 的集中 Human UAT 接受；AI rehearsal只能說 ready。

## 10. Assurance / metric

PN-078 的 Task mode、read-only Status badge、失效理由及分軸 Candidate view 依 `ASSURANCE_CONTRACT`；Mode/Status 不得與 PASS 或 Human accepted 混成同一 success icon。

PN-038 human override 只顯示 attributable disagreement telemetry，無接受或 override 操作；UNKNOWN 不顯示為 0。Control Plane 可以摘要 Assurance/metric，但不能藉摘要改變其 authoritative state。
