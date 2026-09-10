# Track A Goal Execution Framework

2026-09-10 · TA-OPERATING-MODEL · READY_FOR_INDEPENDENT_REVIEW

## 1. Authority and current boundary

Human 本輪明確決定 GOAL-BASED DEVELOPMENT / BOUNDED GOAL AUTONOMY；Codex 是 PRIMARY_IMPLEMENTATION_AGENT、DEFAULT_GOAL_OWNER、DEFAULT_IMPLEMENTATION_WRITER。本文件保存此決策與供獨立審查的 operating model，不宣稱已獲獨立 PASS。

權威順序：Current explicit Human instruction → Frozen I-01..I-23 → approved architecture/governance records → current authorized Goal contract → canonical AGENTS/governance → project-local SKILL → tool adapter → model defaults。較低層不得覆蓋較高層；衝突 STOP / REPORT / ESCALATE。Human 新指示若涉及架構變更，仍須明確 Change Control，不能把一般 Goal 授權推論為解凍。

必讀來源：[Freeze Record](../reviews/POLYNEXUS_TRACK_A_V1_ARCHITECTURE_FREEZE_RECORD.md) §3（I-01..I-23 原文）、[REV1](../reviews/GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1.md)（§3.5 fixed golden authority、§17、§19、§24）、[Input Baseline](../reviews/GATE_2_INPUT_BASELINE.md)、[Formal Change Plan](../reviews/POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md)、[Work Packages](../reviews/POLYNEXUS_TRACK_A_IMPLEMENTATION_WORK_PACKAGES.md)。不複製或改寫其 frozen 契約。

- Architecture APPROVED / FROZEN；Gate 2 closure PASS；canonical design/read SHA `f34e6b29ae9e7326d1d44b9b03756b450809928f`。
- PRODUCT_IMPLEMENTATION HOLD；FORMAL_CONTRACT_SYNC NOT YET EXECUTED；S0/W1–W6 NOT AUTHORIZED；REAL_EXECUTOR NOT YET VERIFIED；B01 NOT YET EXECUTED；WORKING_PRODUCT NOT YET ACCEPTED。
- 本輪僅治理／規劃／skills／templates；禁止 checkout/reset/rebase/merge/prune/clean/stage/commit/push；不改產品、production tests、schema/migrations、Scope/PRD/SA/SD/Decision Log/Frozen ADR，也不執行 F1 exact diff。
- 開發治理 Goal、Git REVIEW_CANDIDATE_SHA 與產品 Task/Run/CandidateID 是不同層。此流程不新增產品 scheduler、parallel coding writers、DB enum 或自動 Accept/commit 功能；不改 I-02/I-16。
- 本輪 working HEAD `b87a0dc780e5d9a3bba083dbaf9552ca52508f9a`、branch `feature/first-vertical-slice` 只承載文件 overlay。不得當成實作 predecessor。新治理尚未 commit/push，**新機器 checkout 尚不能取得本輪文件**；publish readiness 與文件 review readiness 分開。

## 2. Intake and ownership

先從專案目錄讀 [AGENTS](../../AGENTS.md)、[Project State](../11_PROJECT_STATE.md)、[Current Handoff](../12_HANDOFF_CURRENT.md)、[Current Goal](../IMPLEMENTATION_CURRENT_GOAL.md)，再讀 exact Goal、handoff、上述 freeze inputs、直接相關 ADR/contract 與 skill。只按需要擴讀；聊天記憶不授權。

執行並記 actual exit：`git status --short --branch --untracked-files=all`、`git branch --show-current`、`git rev-parse HEAD`、`git diff --cached --name-status`、`git remote -v`、`git branch -vv`。擁有權不符可用經確認路徑的單次 `git -c safe.directory=<repo>`；不改全域。未知項標 [待驗證]。

開工必須有 Goal contract、Human 授權來源、exact predecessor、分支、scope/allowlist、owner 和依賴 gate。EXPECTED_FILE_AREAS 不是 allowlist。ALLOWED_FILES 必須列 exact files；可另列明確責任區域的 new-file rule（用途、目錄、排除項），同責任合理新檔可自行決定並列入記錄；跨責任／public contract／未批准 migration 不可套用此例外。

ONE MANAGED GOAL + ONE BRANCH / MANAGED SCOPE = ONE ACTIVE WRITER。Goal 記 owner/tool/context/machine、branch、scope、開始時間、authorization source；交接記釋放與接收確認。不以 CLEAN、無 log、lease 到期或 branch 存在當成無 Writer。發現衝突立即 HOLD；失聯 owner 須 Human 確認安全停止後轉移。不能靠最後寫入同一 Markdown 檔取得鎖；此為 Human 管理的開發協定，不聲稱已實作分散式鎖。

Codex 預設 Writer；OpenCode/Antigravity/Claude Code 或其他 Agent 寫產品前須 Human 明確指定 AUTHORIZED_ALTERNATE_WRITER。支援角色可為 planner/researcher/analyzer/reviewer/tester/validator/evidence/handoff assistant，但不自帶寫入／委派權。指定 reviewer 不可是同一 Writer context；預設 final reviewer 為 Human-designated ChatGPT Review Context。NEXT_PROMPT 不構成 delegation permission。

## 3. Bounded autonomy and HOLD

有效授權從 AUTHORIZED 持續至 REVIEW_READY，包括 intake、predecessor verification、analysis/plan、allowlist 修改、必要正負測試、diagnosis、bounded repair、fresh rerun、evidence、自查 invariants/scope、local review commit、review packet 與 handoff。普通 class/function arrangement、測試 fixture、局部 bug 不需逐步詢問。測試按 targeted → affected regression → relevant lint/typecheck/build；不以省 token 弱化 AC 或 negative evidence。

只有下列 exceptional gate 需要中途 HOLD：

| Gate | Trigger |
|---|---|
| A–B | I-01..I-23 或 Frozen Product Boundary 需要變更 |
| C | Goal/allowlist 責任擴張，非已批准 new-file rule |
| D | 未批准 RuntimeAdapter public contract、RuntimeBindingSnapshot semantics、workflow vocabulary、Candidate canonicalization/identity 或 Human trust 變更 |
| E | reset/discard Human work、accepted history rewrite/force push、destructive migration、lossy repair、刪未知 untracked |
| F | 同 scope 第二 active writer 或 ownership 無法安全判定 |
| G–H | 缺 Human credential/account approval、超出成本/外部權限、未授權高風險資料傳輸 |
| I–J | AC 矛盾/不足需猜測；契約未涵蓋的重大 security/migration/data-integrity 風險 |

HOLD 輸出 BLOCKER、WHY_HUMAN_DECISION_REQUIRED、OPTIONS、RECOMMENDATION、IMPACT；普通 debugging 不冒充 Human blocker。若工具權限阻止完成，先確認缺環境/權限而非改契約，保留實際錯誤並提出最小處置。

## 4. Goal lifecycle and review identity

PLANNED → AUTHORIZED → IN_PROGRESS → REVIEW_CANDIDATE → INDEPENDENT_REVIEW；REVIEW_READY 是 candidate、packet、handoff 完備且停止寫入的交付旗標。Reviewer NEED_FIX → IN_PROGRESS；HOLD 等所需決策；PASS 等 Human。Human APPROVED 且明確 exact-SHA push authorization → PUSH_AUTHORIZED → PUSHED → REMOTE_VERIFIED → INTEGRATED（適用時）→ CLOSED。

PASS != HUMAN_APPROVED；HUMAN_APPROVED != PUSHED；PUSHED != REMOTE_VERIFIED；REMOTE_VERIFIED != INTEGRATED；WIP != ACCEPTED。不需 integration 的 Goal 可在 REMOTE_VERIFIED 且 acceptance/handoff 完備後 CLOSED；需 integration 的 component 等 integration checkpoint 建立才關閉其整合依賴。

已授權 implementation Goal 包含 explicit-allowlist staging 及 local REVIEW_CANDIDATE commit，不需另問；每次先核對 branch/HEAD/index/完整 dirty+untracked，避免吸收他人內容。混合已修改檔案需能確定逐 hunk 歸屬，否則 HOLD；禁用 blanket add。**本輪 NO STAGE/COMMIT 例外優先**，僅可提交未 commit 文件審查包，不能冒稱 exact-SHA independent final acceptance 已完成。

Future normal flow：先測試固定內容並保存 file/tree hashes → local commit → resolve full SHA → 驗證測試 bytes 與 commit tree 一致（不一致則重測）→ 產 packet → STOP WRITING → independent review exact SHA。Reviewer 必要時重跑；資料來源、oracle、exit、negative、freshness、scope、invariants、mock boundary 和 cross-machine readiness 全部核對。

Self verification 不是 Independent PASS。Reviewer 輸出 PASS / NEED_FIX / HOLD 與 APPROVE_TO_PUSH / DO_NOT_PUSH；PASS 不自動授權 push。NEED_FIX 在原 Goal/allowlist/contract 內沿用原 authorization，修復後新 commit B、新測試、新 packet，保留 A evidence；A 的 PASS 不證明 B。

SHA 自引用規則：commit 內的 Goal/預備 handoff 不填自己的未來 SHA；commit 後產出 `docs/reviews/<GOAL_ID>/<SHA>.md` 與 `docs/handoffs/<GOAL_ID>/<SHA>.md` 或獨立 review artifact，引用該 SHA。packet 是 attestation，不是 candidate tree 一部分。不得為塞入 SHA 而 amend candidate。遠端可攜性需要後續另授權的 governance receipt checkpoint，明記 reviewed product SHA 與 receipt SHA；不以 receipt commit 冒充已 review 的 code。必要 code tests 依 exact candidate tree，receipt-only checks 依其新 tree；兩者不互相借 PASS。

## 5. Human push and immutable checkpoint

Reviewer PASS + APPROVE_TO_PUSH → Human 明確批准 exact SHA、remote、branch → Writer 再核對 staged/dirty/HEAD，push 該 reviewed SHA（非另一新 commit）。在批准 lane 可用 `git push <remote> <reviewed-full-SHA>:refs/heads/<approved-branch>`，不 force。保存 command/exit，續以 `git rev-parse HEAD` 與 `git ls-remote --heads <remote> refs/heads/<approved-branch>` 取 actual remote SHA；LOCAL_HEAD_SHA = REVIEW_CANDIDATE_SHA = REMOTE_BRANCH_SHA 才記 MATCH YES，否則 NOT READY。push exit 0 不充分。

Independent PASS + Human approval + verified remote SHA 才是 ACCEPTED_GOAL_CHECKPOINT；不得 amend/rebase/force-push 改寫，不重用已接受 Goal ID 指向不同 bytes。後續修正用新 Goal/commit/checkpoint，歷史不刪。對新機器 continuation 另需 clean-clone/intake/dependency checks 與可攜 governance/evidence，單有 remote SHA 不等於已驗證 clone。

## 6. Cross-machine, WIP and integration

新機器：確認授權 remote → fetch（保存 exit）→ 核對 branch 與 handoff exact predecessor SHA/object → 先保全 dirty/index/untracked → 在允許且無競爭 writer 的 lane safe checkout/switch → verify HEAD/tree → 讀 project governance/Goal/handoff → dependency checks → acquire writer ownership → 才實作。任一 exact SHA 不符 HANDOFF_INTAKE FAIL / DO_NOT_START_IMPLEMENTATION；不要用浮動 latest 代替。若本機已有工作，建立批准的隔離 lane 或等待處置，不能 reset 解決。

WIP_REMOTE_CHECKPOINT 需 Human 明確批准 WIP branch/exact SHA/transfer scope；標 WIP / NOT_ACCEPTED / NOT_REVIEWED / DO_NOT_MERGE。送方先停寫、保存 incomplete tests/findings、確認 remote SHA，再釋放 ownership；接方 fetch exact WIP SHA、intake、Human/governance writer transfer 後延續同 Goal。Reviewer 未完成不能升為 Accepted。WIP 也不容許同 branch 兩台同時寫。

每 Goal 分 SEQUENTIAL_REQUIRED / PARALLEL_SAFE / PARALLEL_WITH_CONSTRAINTS；判斷 schema/persistence/API/runtime/shared Git metadata/workspace/shared tests/dependency/evidence/integration，不只檔案交集。不確定 SEQUENTIAL_REQUIRED。初期 MAX_CONCURRENT_IMPLEMENTATION_GOALS=2 是 operational default，不是 frozen invariant。獨立 branch/managed workspace/scope/writer，工具支援不足則串行。共同 `.git` metadata 操作須序列化；獨立 clone 可減共享 metadata 風險。

Human 可批准 dependency-safe Goal Batch，逐項列 branch、writer、scope、前置與 concurrency；不是批次驗收，也不自動授權 tools/subagents。每 Goal 各自 candidate/review/Human/push。現有 Goal map 保守串行，沒有任何平行 batch 被授權。

A PASS + B PASS != A+B PASS。整合另建 INTEGRATION_GOAL（preferred writer Codex），輸入 accepted exact A/B SHAs；Human 授權整合 scope/操作；controlled integration、conflict review、affected regression、新 evidence → independent review → Human approval → exact checkpoint C。Dependent Goal 從 accepted C 開始，不从 A/B 任一 component tip 開工。

## 7. Records and model routing

TRACK → WORK PACKAGE → EPIC GOAL → GOAL → IMPLEMENTATION TASK → REVIEW CANDIDATE → INDEPENDENT ACCEPTANCE → HUMAN DECISION → REMOTE CHECKPOINT → INTEGRATION。

每 Goal 用 [Goal template](../goals/_GOAL_TEMPLATE.md)；handoff 用 [Handoff template](../handoffs/_HANDOFF_TEMPLATE.md)；review 用 [Packet / verdict template](../reviews/_REVIEW_PACKET_TEMPLATE.md)。`docs/goals/<GOAL_ID>.md` 保存 contract，`docs/handoffs/<GOAL_ID>/<SHA-or-WIP-ID>.md` 保存歷史。兩個 current 檔只由 main/integration navigation owner 更新，parallel branch 不搶全專案 current。現有 docs/tasks 與 SOP 模板保留為歷史／專用證據，Goal-level 必要欄位以本套模板為準，不另複製整套 SOP。

Environment fingerprint：OS/version、Git/Python/Node/npm/shell version、實際使用/存在的 tool version、model used、branch/full HEAD、core.autocrlf、.gitattributes blob/hash、dependency lock hashes、相關環境變數 NAMES（不含值）。記 timestamp/machine alias/scope；未觀測版本寫 UNKNOWN，不根據品牌推 readiness。揭露 path/case/Unicode/CRLF/candidate bytes/runtime 差異，不 silent normalize。見 [Capability matrix](POLYNEXUS_DEVELOPMENT_AGENT_CAPABILITY_MATRIX.md)。

| Preferred pool | 責任 | Fallback / escalation |
|---|---|---|
| ASTRA MEDIUM | frozen invariant、security/trust、migration decision、cross-WP conflict、高風險 red team、formal contract | 此類 decision 缺 Astra 則 HOLD，不讓低階猜測 |
| SOL MEDIUM | primary technical planner、decomposition、complex impact/prompt/debug/review | bounded routine 可 Luna；架構/security uncertainty 升 Astra |
| LUNA MAX | bounded reading/log/test classification、evidence/handoff/allowlist、低風險 repetitive review | uncertainty/cross-module 升 Sol，再依風險 Astra |

不是 round-robin，也不自动更換當前模型。Goal 記 actual model 與推薦值；native supported models 可用於 Human 授權 alternate/support scope。任何模型不能 self-expand/self-approve architecture、push 或 Human acceptance。一般格式整理可 fallback；D11、Candidate identity、高風險 migration/destructive recovery/public runtime ambiguity 必須 HOLD/escalate。

## 8. Full Goal map and progressive elaboration

所有下列 Goal 為 PLANNED / NOT AUTHORIZED。詳細契約見各連結；exact implementation predecessor、allowlist 與 commands 在授權前按 predecessor actual evidence 確認，不發明 SHA 或尚不存在的 tests。跨 WP 完成需 independent acceptance + Human checkpoint。共同整合規則見 §6。

| Goal | 目標 | Execution mode | Preferred owner / model | Dependencies / integration |
|---|---|---|---|---|
| [TA-F1](../goals/TA-F1.md) | formal exact diff proposal | SEQUENTIAL_REQUIRED | Codex / Astra Medium | operating model acceptance + F1授權；不套用 diff |
| [TA-F2](../goals/TA-F2.md) | exact wording/allowlist Human decision | SEQUENTIAL_REQUIRED | Human；Codex整理 / Astra Medium | F1 exact proposal identity |
| [TA-F3](../goals/TA-F3.md) | approved formal documentation sync | SEQUENTIAL_REQUIRED | Codex / Astra Medium | F2 explicit批准及安全lane |
| [TA-F4](../goals/TA-F4.md) | independent doc consistency | SEQUENTIAL_REQUIRED | Human-designated reviewer / Astra Medium | exact F3 candidate；Human決定checkpoint/S0授權 |
| [TA-S0-G01](../goals/TA-S0-G01.md) | SQLite FK / audit | SEQUENTIAL_REQUIRED | Codex / Sol Medium | F4 accepted + S0 authorization |
| [TA-S0-G02](../goals/TA-S0-G02.md) | CREATED restart | SEQUENTIAL_REQUIRED | Codex / Sol Medium | S0-G01 accepted |
| [TA-S0-G03](../goals/TA-S0-G03.md) | pairing / START / HEALTH | SEQUENTIAL_REQUIRED | Codex / Sol Medium；trust→Astra | S0-G02 accepted；M-HUMAN條件；S0 aggregate regression |
| [TA-W1-G01](../goals/TA-W1-G01.md) | repository/input/generation refs | SEQUENTIAL_REQUIRED | Codex / Sol Medium；migration→Astra | S0 accepted、formal M-IDENTITY |
| [TA-W1-G02](../goals/TA-W1-G02.md) | managed workspace / ownership | SEQUENTIAL_REQUIRED | Codex / Sol Medium | W1-G01 accepted |
| [TA-W1-G03](../goals/TA-W1-G03.md) | lineage / retry / late abort | SEQUENTIAL_REQUIRED | Codex / Sol Medium | W1-G02 accepted；W1 aggregate regression |
| TA-W2 (coarse) | brand-neutral feasibility + real executor | SEQUENTIAL_REQUIRED | Codex / Sol Medium；public mapping→Astra | accepted W1；real cwd/write/cancel/timeout/child cleanup；M-EXECUTION stays mapping-only unless demonstrated otherwise |
| TA-W3 (coarse) | Core-derived ChangeSet/Candidate/artifacts | SEQUENTIAL_REQUIRED | Codex / Astra Medium | accepted W2 quiescence；REV1 literal goldens、rebuild/partial publish negatives |
| TA-W4 (coarse) | verification/evidence truth | SEQUENTIAL_REQUIRED | Codex / Sol Medium；trust→Astra | accepted W3；mandatory invalid blocks、optional SKIPPED、trusted oracle/B04/B07/B09 |
| TA-W5 (coarse) | D11-A-LP Human decision | SEQUENTIAL_REQUIRED | Codex / Astra Medium | accepted W4 + formal M-HUMAN；security+UX/races/revoke/supersede |
| TA-W6 (coarse) | accepted result + recovery + P0 package | SEQUENTIAL_REQUIRED | Codex / Sol Medium | accepted W5；source reconstruct、takeover labels、failure/retry、START_HERE |
| TA-B01 (coarse) | working product / pilot independent acceptance | SEQUENTIAL_REQUIRED | designated reviewer / Astra Medium；Codex supplies packet | accepted W6；real journey、nine pilot metrics、Direct Agent+Git+CI comparison、Pivot/No-Go + Human acceptance |
| TA-N1 / TA-NEXT | full portability / deferred capabilities | SEQUENTIAL_REQUIRED pending elaboration | Codex / Sol Medium | not B01 prerequisites；separate Human scope |

S0/W1 子 Goal 逐一 checkpoint 串接，最後一個需驗證整個 WP accumulated behavior；若日後批准平行拆分，必須另建 integration Goal，不能只相加子 PASS。W2–W6/B01 詳細檔案、adapter 品牌、schema layout、測試名稱待 predecessor evidence，不提前寫死。

## 9. Legacy, publication and review boundary

[Legacy reconciliation](POLYNEXUS_LEGACY_OPEN_WORK_RECONCILIATION.md) 是唯一 legacy→Track A routing；舊 Gxx/CP/roadmap 不再派工。未解 decisions 保留，S0 前必須有 disposition；不刪歷史或把 bounded PASS 重算為 Working Product PASS。

本輪交付只 READY_FOR_INDEPENDENT_REVIEW，非已接受 operating model、非 immutable candidate、非 remote-ready。審查目前文件可用 [本輪 review packet](../reviews/TA-OPERATING-MODEL-REVIEW.md) 的 hashes/delta；正式 SHA final gate 須另獲 Git 授權後建立 candidate 再 review exact SHA。Independent review 後下一步為 F1 proposal 授權，F1/F2/F3/F4 不得跳過；本輪 STOP。
