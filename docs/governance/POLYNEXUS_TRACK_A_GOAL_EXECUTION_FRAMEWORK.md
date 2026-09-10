# Track A Goal Execution Framework

2026-09-10 · Operating Model R2獨立PASS / Human ACCEPTED；remote closure PENDING。現行修正：REVIEW_PACKAGE_SKILL bounded NEED_FIX（status / lifecycle only）。

## 1. Authority and current boundary

Human 本輪明確決定 GOAL-BASED DEVELOPMENT / BOUNDED GOAL AUTONOMY；Codex 是 PRIMARY_IMPLEMENTATION_AGENT、DEFAULT_GOAL_OWNER、DEFAULT_IMPLEMENTATION_WRITER。本文件保存此決策與供獨立審查的 operating model，Operating Model R2已由Human確認獨立PASS及Human ACCEPTED；remote closure仍PENDING，CROSS_MACHINE_CHECKPOINT=NOT_READY。此確認不代表本次REVIEW_PACKAGE_SKILL修復已獨立PASS。

權威順序：Current explicit Human instruction → Frozen I-01..I-23 → approved architecture/governance records → current authorized Goal contract → canonical AGENTS/governance → project-local SKILL → tool adapter → model defaults。較低層不得覆蓋較高層；衝突 STOP / REPORT / ESCALATE。Human 新指示若涉及架構變更，仍須明確 Change Control，不能把一般 Goal 授權推論為解凍。

必讀來源：[Freeze Record](../reviews/POLYNEXUS_TRACK_A_V1_ARCHITECTURE_FREEZE_RECORD.md) §3（I-01..I-23 原文）、[REV1](../reviews/GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1.md)（§3.5 fixed golden authority、§17、§19、§24）、[Input Baseline](../reviews/GATE_2_INPUT_BASELINE.md)、[Formal Change Plan](../reviews/POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md)、[Work Packages](../reviews/POLYNEXUS_TRACK_A_IMPLEMENTATION_WORK_PACKAGES.md)。不複製或改寫其 frozen 契約。

- Architecture APPROVED / FROZEN；Gate 2 closure PASS；canonical design/read SHA `f34e6b29ae9e7326d1d44b9b03756b450809928f`。
- PRODUCT_IMPLEMENTATION HOLD；FORMAL_CONTRACT_SYNC NOT YET EXECUTED；S0/W1–W6 NOT AUTHORIZED；REAL_EXECUTOR NOT YET VERIFIED；B01 NOT YET EXECUTED；WORKING_PRODUCT NOT YET ACCEPTED。
- 本輪僅治理／規劃／skills／templates；禁止破壞性 checkout/reset/rebase/merge/prune/clean 與 push；R2 Human 明確授權 self-validation 後 exact-allowlist local review commit；不改產品、production tests、schema/migrations、Scope/PRD/SA/SD/Decision Log/Frozen ADR，也不執行 F1 exact diff。
- 開發治理 Goal、Git REVIEW_CANDIDATE_SHA 與產品 Task/Run/CandidateID 是不同層。此流程不新增產品 scheduler、parallel coding writers、DB enum 或自動 Accept/commit 功能；不改 I-02/I-16。
- 本輪 working HEAD `b87a0dc780e5d9a3bba083dbaf9552ca52508f9a`、branch `feature/first-vertical-slice` 只承載文件 overlay。不得當成實作 predecessor。原 checkout 保留不動；R2 在隔離的文件審查 repository 以 R1 ZIP 原bytes建立未接受的comparison predecessor，再commit限定修正。該比較SHA不是Human-accepted或product predecessor；exact C與branch見R2 package。未push，不宣稱cross-machine accepted readiness。

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

PLANNED → AUTHORIZED → IN_PROGRESS → REVIEW_CANDIDATE → REVIEW_READY → INDEPENDENT_REVIEW。REVIEW_READY 必須具備 exact immutable Review Candidate SHA、已驗證mandatory Review Package、required changed-file bytes、valid manifest、required fresh evidence、已記錄negative tests、無blocking mandatory SKIPPED、完整handoff/review packet及Writer已停止寫入。Package generation/validation是此gate內部步驟，不新增formal lifecycle states；未達REVIEW_READY不得交Independent Review。Reviewer NEED_FIX → IN_PROGRESS；HOLD 等所需決策；PASS 等 Human。Human APPROVED exact C → PUSH_AUTHORIZED_C → PUSHED_C → REMOTE_C_VERIFIED → RECEIPT_CREATED_R → RECEIPT_INTEGRITY_PASS → PUSHED_R → REMOTE_R_VERIFIED → CROSS_MACHINE_READY（intake gate另驗）→ INTEGRATED（適用時）→ CLOSED。

PASS != HUMAN_APPROVED；HUMAN_APPROVED != PUSHED；PUSHED != REMOTE_VERIFIED；REMOTE_VERIFIED != INTEGRATED；WIP != ACCEPTED。不需 integration 的 Goal 可在 REMOTE_R_VERIFIED、receipt integrity與acceptance/handoff完備後 CLOSED；需 integration 的 component 等 integration checkpoint 建立才關閉其整合依賴。

已授權 implementation Goal 包含 explicit-allowlist staging 及 local REVIEW_CANDIDATE commit，不需另問；每次先核對 branch/HEAD/index/完整 dirty+untracked，避免吸收他人內容。混合已修改檔案需能確定逐 hunk 歸屬，否則 HOLD；禁用 blanket add。**R2 Human已授權限定修正的local review commit；仍禁止push**。R1 no-commit限制是歷史，不延伸阻擋本次明確授權。不得吸收原主checkout的舊dirty內容。

Future normal flow：先測試固定內容並保存 file/tree hashes → local commit → resolve full SHA → 驗證測試 bytes 與 commit tree 一致（不一致則重測）→ 產mandatory Review Package與完整packet/handoff → package validation → STOP WRITING / REVIEW_READY → independent review exact SHA。Reviewer 必要時重跑；資料來源、oracle、exit、negative、freshness、scope、invariants、mock boundary 和 cross-machine readiness 全部核對。

Self verification 不是 Independent PASS。Reviewer 輸出 PASS / NEED_FIX / HOLD 與 APPROVE_TO_PUSH / DO_NOT_PUSH；PASS 不自動授權 push。NEED_FIX 在原 Goal/allowlist/contract 內沿用原 authorization，修復後新 commit B、新測試、新 packet，保留 A evidence；A 的 PASS 不證明 B。

SHA 自引用採兩層 checkpoint，依 §5。C 是已 review 的內容；R 是之後形成的 metadata receipt。不得為補 verdict/approval/remote proof 而 amend C。

## 5. Acceptance receipt / cross-machine closure (FINDING-01)

### 5.1 C / R identity and authorization

`REVIEWED_PRODUCT_SHA=C`：Independent Reviewer實際review的exact implementation或governance content commit；Human acceptance主要target。`ACCEPTANCE_RECEIPT_SHA=R`：Human批准C且C push/remote verified後，由該Goal authorized Writer建立的metadata-only governance commit。R不是新implementation，不取代C，不使用產品CandidateID。

Writer self verification → local Review Candidate C → Independent Review exact C（PASS/NEED_FIX/HOLD）→ Human approves exact C → push exact C → verify LOCAL_C=REMOTE_C → metadata receipt R → RECEIPT_INTEGRITY_CHECK → push exact R → verify LOCAL_R=REMOTE_R → cross-machine intake。Independent review PASS不取代Human批准。

Human批准C時可**同一次**明確授權 `ONE_BOUNDED_ACCEPTANCE_RECEIPT_CLOSURE`，記Goal ID、C、Writer、remote/ref、R必須direct parent C、exact receipt file allowlist、受保護reviewed scope、next Goal及其授權狀態。這是條件式授權一次R closure，不是所有後續metadata修改的blanket approval。缺此授權則HOLD於receipt closure；不可推論R push權。正常closure不再增加完整第二轮人工產品驗收。

R符合allowlist、C內容保全、deterministic integrity PASS才可使用該授權push exact R，不必再Product Independent Review。超scope/變更reviewed bytes/失敗gate → HOLD / HUMAN_REVIEW_REQUIRED / DO_NOT_PUSH；修正不可偷偷擴allowlist。尚未發送的失敗receipt可在原scope重新形成候選，保留失敗證據與新SHA；已發布receipt不可amend/rewrite，後續更正須新授權。C始終immutable。

### 5.2 Strict receipt files and parent rule

Reuse現有目錄，預先在Goal與Human批准記**exact paths**（以下`<GOAL_ID>`必須替換；不把glob當stage權）：

- `docs/reviews/<GOAL_ID>/acceptance-receipt.json`
- `docs/reviews/<GOAL_ID>/independent-review.md`
- `docs/reviews/<GOAL_ID>/human-decision.md`
- `docs/reviews/<GOAL_ID>/remote-c-proof.json`
- `docs/handoffs/<GOAL_ID>/accepted.md`
- 如需更新main/integration導航，另明列 `docs/IMPLEMENTATION_CURRENT_GOAL.md`、`docs/12_HANDOFF_CURRENT.md`；parallel Goal預設不改這兩檔。

不修改Goal contract實作/AC、其他governance、產品source/tests/schema/migration/runtime/frontend、Candidate或accepted implementation bytes、Scope/PRD/SA/SD/Decision Log/Frozen ADR/I-01..I-23。不另建accepted index，receipt已提供索引。不得以路徑落docs內就當metadata。

採 **R唯一parent=C**，不得merge parent、額外祖先commit或rebase；C所在remote ref先證明C，再由R fast-forward推進，同一approved branch。若中間ref被別人移動則HOLD，不能force推回。C保存為R^並可用exact SHA讀取。

C中或Human批准的scope manifest明列可更新的導航metadata；它們不屬reviewed implementation/governance result內容。除了這些**事先**排除的metadata與新receipt files，R tree所有其他path的mode/blob SHA必須與C完全相同。不得事後把受review的Goal/Framework/skills文件塞入receipt allowlist以規避保全。原C Git object與其reviewed_scope hashes永遠保持原值。

### 5.3 Deterministic RECEIPT_INTEGRITY_CHECK

輸入：immutable Git objects C/R；Human approval的exact allowlist/scope/remote/next-goal授權；R tree內receipt與其引用；C push proof。Verifier用read-only `git cat-file -e <sha>^{commit}`、`git rev-list --parents -n 1 R`、`git diff-tree --no-commit-id --name-status -r C R`、`git ls-tree -r C/R`、`git show <sha>:<path>`，保存argv/cwd/exit/bounded output。參照固定R tree，不讀浮動working tree。

| Check | Deterministic assertion / failure |
|---|---|
| RI-01 | receipt.reviewed_product_sha == full C；C/R object存在；WIP不得receipt |
| RI-02 | human decision target == C，APPROVED；有Human來源ref/hash與ONE_BOUNDED closure授權；不是Writer自寫approved字串就具Human信任 |
| RI-03 | independent-review target == C、PASS、APPROVE_TO_PUSH；reviewer context != writer；原review ref/hash可核對 |
| RI-04 | remote-c-proof保存remote identity/ref、observed LOCAL_C/REMOTE_C==C、push與ls-remote exact command/exit/output/time；缺proof或push0但SHA不符FAIL |
| RI-05 | R parent列表恰為[C]；approved remote/ref一致；發布R前fresh remote仍C，不為R偷合另一commit |
| RI-06 | actual changed path集合等於manifest.changed_files，且subset of Human-approved exact receipt allowlist；無delete/rename/symlink/path escape，metadata fields only |
| RI-07 | C reviewed_scope所有mode/blob/hash在R相同；全tree非approved metadata範圍完全相同；不可修改Goal content/contracts/tests |
| RI-08 | review、Human decision、remote C proof、handoff與next Goal references在C/R明確tree可解析；不用chat ID/本機絕對路徑當唯一來源；secrets不進記錄 |
| RI-09 | manifest對所有receipt payload refs記SHA-256/size，讀R blobs驗hash/size；重複path、缺ref、額外unlisted payload FAIL；receipt JSON本身由Git R blob/tree保護，不能自填自己的hash |
| RI-10 | receipt/handoff next_goal一致且對應實際Goal record；governance_predecessor=SELF_RECEIPT（解析為R）、reviewed_result=C；next Goal未授權仍NOT_AUTHORIZED，不能由routing授權 |

所有10項AND才 `RECEIPT_INTEGRITY: PASS`；任何缺失、UNKNOWN、SKIPPED或false → FAIL / CROSS_MACHINE_CHECKPOINT: NOT_READY。範例或mock gate不能證明真實remote proof、Human或receipt接受。Deterministic reference/hash檢查不代替Human attribution真實性；來源未受信任先HOLD。

### 5.4 Self-reference termination and remote evidence

receipt JSON不寫自身R literal SHA或自身hash；使用 `acceptance_receipt_sha: SELF_RECEIPT`，讀取者以明確checkout/fetched R解析（不可用浮動latest）。R內handoff也是此token；外部post-commit report可列literal R。manifest只hash其他payload；R Git tree保護manifest/receipt bytes，無循環。

C remote proof是在R前形成並保存在R；R的gate結果與push proof在R後形成，保存於外部closure log（記literal R/command/time/exit/output/hash），**不為把R proof放入R再造第三個receipt**。新機器直接fetch並以 `git ls-remote --heads <remote> refs/heads/<approved-branch>` 取得actual R，核對local R；重跑R integrity與讀R內C proof即足够。若ref已前進，必須有另外明確approved可解析鏈，否則本最小規則HOLD，不能默認latest。Historical C proof加上R^=C與remote取得R可證C仍在鏈中，毋須要求同branch此時仍指C。

Approved exact C push example：`git push <remote> <C>:refs/heads/<approved-branch>`；核對HEAD=C與ls-remote=C。Gate PASS後同法push exact R，核對HEAD=R與ls-remote=R。所有指令記actual exit；沒有Human R closure authority即不执行。

ACCEPTED result identity=C；cross-machine closure anchor=R。Human接受C + C remote verified只是result acceptance；R integrity及remote verified之前CROSS_MACHINE_CHECKPOINT仍NOT_READY。C/R均不得amend/rebase/force-push覆寫；後續產品修正新Goal/commit。

## 6. Cross-machine, WIP and integration

新機器：確認授權 remote → 先fetch governance predecessor ACCEPTANCE_RECEIPT_SHA=R（保存exit）→ 驗R存在、讀receipt找到C、C存在、R^=C、C remote proof/acceptance/handoff/next Goal有效、local R==remote R、重跑§5 integrity → 核對branch與handoff exact checkpoint pair(R,C) → 先保全 dirty/index/untracked → 在允許且無競爭 writer 的 lane safe checkout/switch → verify HEAD/tree → 讀 project governance/Goal/handoff → dependency checks → acquire writer ownership → 才實作。任一 exact SHA 不符 HANDOFF_INTAKE FAIL / DO_NOT_START_IMPLEMENTATION；不要用浮動 latest 代替。若本機已有工作，建立批准的隔離 lane 或等待處置，不能 reset 解決。

WIP_REMOTE_CHECKPOINT 需 Human 明確批准 WIP branch/exact SHA/transfer scope；標 WIP / NOT_ACCEPTED / NOT_REVIEWED / DO_NOT_MERGE。送方先停寫、保存 incomplete tests/findings、確認 remote SHA，再釋放 ownership；接方 fetch exact WIP SHA、intake、Human/governance writer transfer 後延續同 Goal。Reviewer 未完成不能升為 Accepted。WIP 也不容許同 branch 兩台同時寫。WIP 不產生Acceptance Receipt；只有Human accepted C才能產R。

每 Goal 分 SEQUENTIAL_REQUIRED / PARALLEL_SAFE / PARALLEL_WITH_CONSTRAINTS；判斷 schema/persistence/API/runtime/shared Git metadata/workspace/shared tests/dependency/evidence/integration，不只檔案交集。不確定 SEQUENTIAL_REQUIRED。初期 MAX_CONCURRENT_IMPLEMENTATION_GOALS=2 是 operational default，不是 frozen invariant。獨立 branch/managed workspace/scope/writer，工具支援不足則串行。共同 `.git` metadata 操作須序列化；獨立 clone 可減共享 metadata 風險。

Human 可批准 dependency-safe Goal Batch，逐項列 branch、writer、scope、前置與 concurrency；不是批次驗收，也不自動授權 tools/subagents。每 Goal 各自 candidate/review/Human/push。現有 Goal map 保守串行，沒有任何平行 batch 被授權。

A PASS + B PASS != A+B PASS。整合另建 INTEGRATION_GOAL（preferred writer Codex），輸入 accepted exact A/B SHAs；Human 授權整合 scope/操作；controlled integration、conflict review、affected regression、新 evidence → independent review → Human approval → reviewed integration result C_int → accepted receipt R_int。Dependent Goal以(R_int,C_int) intake，不从A/B任一component tip開工。

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
| [TA-LR-01](../goals/TA-LR-01.md) | Legacy closure / safe lane proposal | SEQUENTIAL_REQUIRED | Codex / Sol Medium；bounded inventory Luna Max | operating model accepted (R,C) + separate LR authorization；HD-L1/L2/L3 decision packet，不操作lane |
| [TA-F1](../goals/TA-F1.md) | formal exact diff proposal | SEQUENTIAL_REQUIRED | Codex / Astra Medium | TA-LR-01 accepted receipt + HD-L1/L2/L3 Human decision + F1授權；不套用 diff |
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

[Legacy reconciliation](POLYNEXUS_LEGACY_OPEN_WORK_RECONCILIATION.md) 是唯一 legacy→Track A routing；舊 Gxx/CP/roadmap 不再派工。未解 decisions 保留，由TA-LR-01在F1前準備完整packet，Human批准disposition後才能進F1；不刪歷史或把 bounded PASS 重算為 Working Product PASS。

Operating Model R2 reviewed C=`a82c9addaf37d8a5b659ac121f4b8f2787da8e76`：R2_INDEPENDENT_REVIEW=PASS；R2_HUMAN_ACCEPTANCE=ACCEPTED（本輪Human明確確認，原文隨REVIEW_PACKAGE_SKILL修復ZIP HUMAN_REQUEST.txt）；R2_REMOTE_CLOSURE=PENDING；CROSS_MACHINE_CHECKPOINT=NOT_READY。不宣稱Acceptance Receipt R已存在或remote proof已完成。R1/R2原始review records保留當時語意。本輪僅允許REVIEW_PACKAGE_SKILL兩項治理修復/new local commit/ZIP，不授權push、R closure或LR執行。NEXT_PROPOSED_GOAL=TA-LR-01，DEFINED_NOT_EXECUTED / NOT_AUTHORIZED；Operating Model Accepted → TA-LR-01 → F1 → F2 → F3 → F4 → S0 → W1…；跨機開工仍需remote receipt closure，LR須另行Human授權，F1前須LR accepted outcome/Human disposition。

## Mandatory external review package

依Human最新Review Package決策，每個Goal在REVIEW_READY前須完成[canonical package skill](../../.agents/skills/polynexus-review-package/SKILL.md)。NO_REVIEW_PACKAGE = NOT_REVIEW_READY；詳細level/content/evidence/manifest/safety/final response只在該skill定義。本規則不改§5 C/R acceptance closure、LR授權或產品HOLD。
