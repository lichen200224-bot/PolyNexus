# 完整功能繼承、設計與驗收核銷索引

每列是可核對的交付要求，AT-xxx為規劃中的驗收案例ID，不是已存在test或PASS。Source代號見SOURCE_INDEX。所有列初始verification=NOT_RUN；已有成果由IMPLEMENTATION_LEDGER逐項引用，不能因本表新增而重做既有accepted功能。Requiredness按原成熟度/phase：NEXT不阻擋B01，但不得無聲從完整交付刪除。正文及frozen原件中未被摘要到的義務仍有效，independent design review必須做source-to-row覆蓋核對。

| ID | Source/section | 必要功能與完成條件 | 負例/不可冒稱 | Design / Batch / Test |
|---|---|---|---|---|
| PN-001 | BASE PRD§7 | Create/Open/Archive Project及default classification；durable reopen | Archive不刪歷史；foreign project拒絕 | SA / D1 / AT-001 |
| PN-002 | BASE PRD§7 | Task/Run/Context/Artifact/Finding/Evidence/Decision可關聯查詢 | 不用vendor session當唯一歷史 | SA / D1 / AT-002 |
| PN-003 | BASE Scope§3 | Discuss/Review/Validate三入口可串接；Develop為action | 不增加第四個頂層入口 | UX_SPEC / D4 / AT-003 |
| PN-004 | BASE PRD§7 Council | 2–4角色真實獨立分析 | 不把單答案重貼成多方意見 | SD / D3 / AT-004 |
| PN-005 | BASE Scope§3 | Cross Review與Synthesis保留共識、分歧、風險、缺資料 | 不以摘要消除反對意見 | SD / D3 / AT-005 |
| PN-006 | BASE PRD§7 Council | max rounds/timeout/partial failure可配置與呈現 | 失敗角色不製造輸出 | SD / D3 / AT-006 |
| PN-007 | BASE Scope§4 | 九個範本均能執行且schema有效 | YAML存在不等於功能完成 | SD / D3 / AT-007 |
| PN-008 | BASE Acceptance§3 | 四Golden flows深度端到端驗證 | component PASS不當E2E PASS | TEST_PLAN / T1 / AT-008 |
| PN-009 | BASE SD§7 | versioned ContextPackage引用來源/decision/artifact及分類 | 不退化prompt string，不跨Run失去version | DATA_AND_API / D1 / AT-009 |
| PN-010 | BASE SD§6 | Artifact metadata+immutable content+hash+分類 | path locator不保證安全/內容identity | DATA_AND_API / D1 / AT-010 |
| PN-011 | BASE Scope§2 | Context/Artifact lifecycle可定位、重用與安全保留 | 不刪accepted/evidence必要closure | SD / D4 / AT-011 |
| PN-012 | BASE PRD§7 Evidence | 五Evidence類型與source actor可追溯 | AI_OPINION不得升為TOOL_EVIDENCE | DATA_AND_API / D1 / AT-012 |
| PN-013 | BASE Scope§3 | Findings具severity/位置/理由/修復建議 | 不以無來源結論冒稱verified | UX_SPEC / D3 / AT-013 |
| PN-014 | BASE SD§8 | 固定九類workflow node、limited CONDITION、immutable version | 不擴一般程式語言/任意script DSL | SD / D3 / AT-014 |
| PN-015 | BASE PRD§7 | required deterministic hard gate否決Verified PASS | 不可AI投票覆寫FAIL | SD / D3 / AT-015 |
| PN-016 | BASE ADR-007 | Core Supervisor擁有normalized lifecycle | vendor observation不直接寫Run truth | RUNTIME_AND_MODULES / D2 / AT-016 |
| PN-017 | BASE ADR-007 | cancel/timeout實際停止owned work且驗cleanup | 改flag、lease到期不算停工 | RUNTIME_AND_MODULES / D2 / AT-017 |
| PN-018 | BASE SA§7 | NATIVE/MANAGED/NONE如實宣告及接續 | 不保證provider session portability | RUNTIME_AND_MODULES / D2 / AT-018 |
| PN-019 | BASE ADR-011 | immutable Run binding在副作用前持久化 | 不以mutable profile補写歷史或rebind | DATA_AND_API / D2 / AT-019 |
| PN-020 | BASE PRD§3 | Codex深度Runtime真實cwd/change/result/cleanup/conformance | deterministic adapter不等於live target | RUNTIME_AND_MODULES / D2 / AT-020 |
| PN-021 | BASE PRD§3, MCF | OpenCode深度Runtime及ACP候選依實證整合 | 030890b3未審、deny-all不等完整改碼 | RUNTIME_AND_MODULES / D2 / AT-021 |
| PN-022 | BASE Scope§2 | LM Studio/Ollama/Generic compatible真實local接入 | fixture不算三個live target證據 | RUNTIME_AND_MODULES / D2 / AT-022 |
| PN-023 | BASE SA§9 | model discovery/selection/stream/result/capability/identity | 不支援structured output/cancel須明示 | RUNTIME_AND_MODULES / D2 / AT-023 |
| PN-024 | BASE PRD§7 Web | ChatGPT/Claude/Gemini launch/fill/confirmed send/capture | 不繞過逐次Human send | UX_SPEC / D4 / AT-024 |
| PN-025 | BASE ADR-006 | clipboard/manual/launch-only fallback，driver失敗隔離 | Web不可用不得使Core崩潰 | UX_SPEC / D4 / AT-025 |
| PN-026 | BASE ADR-006/010 | authenticated loopback/MV3 caller/least permissions | 未授權caller、Origin、port drift拒絕 | SECURITY / D4 / AT-026 |
| PN-027 | BASE Scope§6 | Highest Classification Wins；禁止自動降級 | 子步驟不忽略高分類artifact | SECURITY / D3 / AT-027 |
| PN-028 | BASE Scope§6 | STANDARD/LOCAL_PREFERRED/LOCAL_ONLY及逐步egress | local failure不得silent cloud fallback | SECURITY / D3 / AT-028 |
| PN-029 | BASE PRD§3/7 | 核准流程可本地/外部混用且記錄實際route | provider選擇不繞過data policy | SD / D3 / AT-029 |
| PN-030 | BASE ADR-010 | SecretRef與OS-backed secret provider、權限/認證/資料分離 | 秘密不進Git/log/export/domain | SECURITY / D2 / AT-030 |
| PN-031 | BASE PRD§7 | timeout/concurrency/budget guards與安全停止 | 不無限retry、不自動付費升級 | OPERATIONS / D4 / AT-031 |
| PN-032 | BASE ADR-012 | Doctor版本/health/readiness/能力/成熟度分層 | 宣告或fixture不升SUPPORTED/CERTIFIED | RUNTIME_AND_MODULES / D4 / AT-032 |
| PN-033 | BASE Scope Compatibility | 核准其他targets有真實偵測/接入/驗證路徑與限制 | 不把相容性例子都當深度支援承諾 | RUNTIME_AND_MODULES / D4 / AT-033 |
| PN-034 | BASE SD§12 | Alembic authoritative，upgrade/backfill/restore有證據 | create_all不冒充production migration | DATA_AND_API / D1 / AT-034 |
| PN-035 | BASE PRD§7 | metadata+artifact backup/restore/export可驗證 | 秘密排除，real DB不自動repair | OPERATIONS / D4 / AT-035 |
| PN-036 | BASE PRD§9 | progressive disclosure；loading/empty/error/offline/retry | 正常流程不必讀log才知道操作 | UX_SPEC / D4 / AT-036 |
| PN-037 | BASE WP-26 | keyboard/focus/labels及可讀錯誤、無障礙路徑 | 不只截圖驗外觀 | UX_SPEC / D4 / AT-037 |
| PN-038 | BASE PRD§10 | duration/manual action/usage/quality/fallback等真實metric | 未觀察usage不是0；不捏造ROI | OPERATIONS / D4 / AT-038 |
| PN-039 | BASE WP-30/31 | clean install、package compatibility、可重現build | 開發機可用不等乾淨環境可用 | OPERATIONS / T2 / AT-039 |
| PN-040 | MOD§3-8 | static manifest/registry、version/capability/duplicate驗證 | 不引入remote loader/marketplace | RUNTIME_AND_MODULES / D2 / AT-040 |
| PN-041 | MOD§8/13 | generic module bridge重用RuntimeRegistry，至少兩個可交換註冊 | 不加vendor-specific Core分支 | RUNTIME_AND_MODULES / D2 / AT-041 |
| PN-042 | MOD§5/10 | module不可改既有binding、Evidence/Human authority | config/enable失敗不污染Core | SECURITY / D2 / AT-042 |
| PN-043 | FROZEN I-03/04 | Task/generation/Run/Candidate分離；generation單調不重用 | 不造Attempt Aggregate | DATA_AND_API / D1 / AT-043 |
| PN-044 | FROZEN§7, WORK W1 | 同generation不因新command/入口產生第二writer lineage | 一般lock釋放後不能繞過lineage唯一性 | SD / D1 / AT-044 |
| PN-045 | REV1§2 | Begin/Retry固定輸入/requirements/validation、expected revision | Retry新generation，重送同command不新建第三輪 | DATA_AND_API / D1 / AT-045 |
| PN-046 | REV1§2.4 | Abort exact generation、Cancel exact Run、Reject exact candidate | g1→retry g2→late Abort(g1)不可停止g2 | SD / D1 / AT-046 |
| PN-047 | FROZEN I-02/14/15 | managed Git worktree＋四軸ownership/recovery，保護Human dirty | CLEAN/PID/lease不等安全可接手 | SD / D1 / AT-047 |
| PN-048 | FROZEN I-15 | dirty input明選fixed snapshot、不修改原index/untracked | 不自動stash/clean/匯入未選檔 | SD / D1 / AT-048 |
| PN-049 | FROZEN I-05/06 | Core從verified snapshots推導ChangeSet，REV1 canonical/Golden | caller manifest/display diff不可定義identity | DATA_AND_API / D1 / AT-049 |
| PN-050 | FROZEN I-07 | writer quiescence後freeze Candidate，source變動新Candidate | verifier不可改被驗內容 | SD / D1 / AT-050 |
| PN-051 | FROZEN I-09 | EvidenceSet/Verification/Decision exact Candidate binding | 其他candidate、mutable workspace、舊證據拒絕 | DATA_AND_API / D1 / AT-051 |
| PN-052 | FROZEN I-08 | requirement/applicability/outcome/validity分開，trusted N/A | optional skip不自動fail；required skip不pass | DATA_AND_API / D1 / AT-052 |
| PN-053 | FROZEN I-10 | 當下mandatory policy＋fresh exact view才可Accept | 無Override、stale/policy drift阻擋 | SECURITY / D1 / AT-053 |
| PN-054 | FROZEN I-11 | append-only Accept/Reject/Revoke/Supersede歷史 | accepted後不可ordinaryReject/覆寫decision | DATA_AND_API / D1 / AT-054 |
| PN-055 | D11-A-LP | Human-only principal與Agent/runtime credential分離 | Agent不能換prefix/alias取得Human能力 | SECURITY / D1 / AT-055 |
| PN-056 | D11-A-LP | pairing/session/challenge分離、expiry/revoke/anti-replay/idempotency | pairing/session本身不是decision | SECURITY / D1 / AT-056 |
| PN-057 | D11-A-LP | exact-view、CSRF、Origin、nonce與scope驗證 | cross-candidate/wrong origin/stale/replay拒絕 | SECURITY / D1 / AT-057 |
| PN-058 | D11-A-LP | 無/失效A-LP回D11-C HUMAN_DECISION/NEED_ACTION | 不以chat開發授權冒充產品Accept | SECURITY / D1 / AT-058 |
| PN-059 | FROZEN I-16 | Open Accepted Managed Worktree、explicit takeover、Working Copy label | Accept不自動commit/merge/push/apply/release | UX_SPEC / D1 / AT-059 |
| PN-060 | FROZEN I-18, WORK W6 | P0 accepted package驗完整closure並可重建exact source | 缺source/私有session依賴/篡改拒絕 | OPERATIONS / B01 / AT-060 |
| PN-061 | FROZEN I-18/19 | N1 selected-task history/continuation/export/import namespace後續交付 | N1不阻B01，不跨機繼承Human session | OPERATIONS / D4-NEXT / AT-061 |
| PN-062 | FROZEN I-17 | REST polling＋durable facts為first vertical monitor | WebSocket掉線不得丟Run truth | DATA_AND_API / D1 / AT-062 |
| PN-063 | FROZEN I-17, BASE ADR-004 | WebSocket保留後續live target，版本/重連/去重 | 非B01前置，不以socket state當durable truth | DATA_AND_API / D4-NEXT / AT-063 |
| PN-064 | WORK S0 | 每條SQLite connection FK on＋legacy relation audit | dangling資料不靜默刪除，不按.db副檔名判dialect | DATA_AND_API / D0 / AT-064 |
| PN-065 | WORK S0 | CREATED未execute可restart；binding只在真實claim時建立 | 不補造binding、不重複launch | SD / D0 / AT-065 |
| PN-066 | WORK S0 | start/health/pairing基礎與schema/client/executor分層 | HTTP活著不等executor ready | OPERATIONS / D0 / AT-066 |
| PN-067 | FROZEN I-22/23 | Stability P0先通；real executor feasibility先於選用 | mock/Golden數值不能宣稱Working Product PASS | TEST_PLAN / D0-D2 / AT-067 |
| PN-068 | MCF§5.2 | Run-scoped execution envelope、resolved config、binary identity | config來源不明/漂移不dispatch | RUNTIME_AND_MODULES / D2 / AT-068 |
| PN-069 | MCF§5.2 | PROJECTED_STAGING、approved input、containment與最小暴露 | 不把direct Human project/home默認交給external runtime | SECURITY / D2 / AT-069 |
| PN-070 | MCF, repair F003/F004 | Core policy按Run/Task/destination/envelope授權；permission callback依實證能力 | boolean approval不造Human auth、deny-all不聲稱tool-write | SECURITY / D2 / AT-070 |
| PN-071 | MCF repair F005 | quiescence後import、hash/size/re-read、Core-owned immutable copy | staging mutation不能換掉accepted output | RUNTIME_AND_MODULES / D2 / AT-071 |
| PN-072 | WORK W2/B01 | 真實bug fix：實際cwd/source diff/test/evidence/Accept/Open | summary說改了不算真的改；原repo保全 | TEST_PLAN / B01 / AT-072 |
| PN-073 | WORK W2/B01 | failure→retry/recovery及real process-tree cancel/timeout | helper flag或PID存在判定不能替代owned effect證據 | TEST_PLAN / B01 / AT-073 |
| PN-074 | BASE WP-28/29 | 故障注入、政策/秘密/timeout/security回歸 | 不以放寬assertion/retry睡眠掩蓋flaky | TEST_PLAN / T2 / AT-074 |
| PN-075 | GOV, Human current | portable repo identity、exact checkpoint、single writer/fresh reviewer | 不以本機路徑或未push候選作跨機正式truth | EXECUTION_CONTRACT / PREP / AT-075 |
| PN-076 | Human current | 有界批次開發、自動同範圍修復/重驗、集中例外 | 不逐GOAL要Human，亦不自行擴scope/費用 | EXECUTION_CONTRACT / ALL / AT-076 |
| PN-077 | Human current, BASE acceptance | 全功能技術驗證＋繁中操作手冊＋最後Human UAT | AI rehearsal不是Human acceptance | UAT_AND_RELEASE / DELIVERY / AT-077 |

## 每列的實作與證據記錄

開工後每個PN-ID在執行ledger新增：source refs、design section、implementation files/commit、candidate/source digest、test IDs與實際command、expected oracle、actual outcome/exit、fixture/live、review ref、applicability predicate、limitation、status。初次可引用既有accepted evidence作歷史基線，但必須標HISTORICAL；受影響或release-required tests須對final candidate重新執行。

不能為提高完成率刪PN列、改原requiredness、把未測target改N/A，或以AT案例名稱存在代替測試。Source coverage與test coverage分開計算；本表不宣稱所有原子條款已獨立驗收。
