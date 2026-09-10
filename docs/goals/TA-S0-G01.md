# TA-S0-G01 — SQLite connection FK enforcement 與 backup-first audit

[Framework](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) · [Template](_GOAL_TEMPLATE.md) · [Work Package criteria](../reviews/POLYNEXUS_TRACK_A_IMPLEMENTATION_WORK_PACKAGES.md) · [Formal Change Plan](../reviews/POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md)

## Contract

| Field | Value |
|---|---|
| GOAL_ID | TA-S0-G01 |
| TRACK | Track A V1 |
| PARENT_WP | S0 |
| EPIC_GOAL | Stability Foundation |
| GOAL_STATUS | PLANNED / NOT AUTHORIZED |
| OBJECTIVE | SQLite connection FK enforcement 與 backup-first audit |
| WHY | 消除 S0 前置缺口，形成可獨立審查的 bounded checkpoint，不把 WP 當巨大 coding prompt |
| CURRENT_STATE | 已知 FK 初始化缺口；本輪未修 |
| TARGET_STATE | 所有SQLite連線FK有效，既有資料audit失敗不自動修 |
| INPUT | Freeze Record / REV1 / Work Packages / Formal Change Plan；canonical design/read f34e6b29ae9e7326d1d44b9b03756b450809928f |
| PREDECESSOR_CHECKPOINT | UNASSIGNED；TA-F4 accepted formal checkpoint + separate S0 authorization + legacy decisions resolved；授權前填 accepted exact SHA/remote/decision refs，不能用設計SHA冒充 |
| IN_SCOPE | SQLite connection FK enforcement 與 backup-first audit |
| OUT_OF_SCOPE | 其他WP、scope擴張、未批准public runtime/binding/identity/trust變更、真實資料破壞 |
| ALLOWED_FILES | NONE；PLANNED不授權寫入，按下列責任與predecessor diff形成exact allowlist後再Human授權 |
| EXPECTED_FILE_AREAS | persistence/database.py、相關 approved audit/fixture tests；不改WAL/DB品牌、不操作真實DB repair |
| FROZEN_INVARIANTS | 全部適用；重點 I-01/12/13/15/17/20/21/23；原文 authority為Freeze Record §3與REV1 §24 |
| DEPENDENCIES | TA-F4 accepted formal checkpoint + separate S0 authorization + legacy decisions resolved |
| INTEGRATION_DEPENDENCIES | sequential accepted predecessor；若批准平行拆分，另需accepted integration SHA |
| GOAL_OWNER | CODEX |
| PREFERRED_IMPLEMENTATION_WRITER | CODEX；其他Writer須Human明確批准 |
| AUTHORIZED_IMPLEMENTATION_WRITER | NONE |
| WRITER_AUTHORIZATION_SOURCE | NONE |
| ACTIVE_WRITER_SCOPE | NONE |
| RECOMMENDED_REASONING_MODEL | SOL MEDIUM |
| MODEL_FALLBACK | routine formatting/classification可LUNA MAX；架構/trust/migration decision不得降級 |
| MODEL_ESCALATION_RULE | uncertainty→SOL；Frozen/security/migration→ASTRA MEDIUM，required Astra不可用則HOLD |
| EXECUTION_MODE | SEQUENTIAL_REQUIRED |
| BRANCH_STRATEGY | 新獨立managed scope，功能命名；AUTHORIZED_BRANCH=NONE，授權前指定；不沿用dirty主工作區 |
| CROSS_MACHINE_HANDOFF_REQUIRED | YES |
| REMOTE_CHECKPOINT_REQUIREMENT | Human批准exact reviewed SHA及remote，驗證local/remote match；intake需要可取得governance/receipts |
| POSITIVE_TESTS | new/pool reused connections FK=ON；invalid insert 實際拒絕；clean audit；fixture backup/restore hash |
| NEGATIVE_TESTS | non-SQLite/普通.db不以filename誤判；dangling/application relation mismatch 報failure、資料不刪 |
| FAIL_CLOSED_CONDITIONS | 缺授權/exact predecessor/安全ownership/required evidence；或Framework exceptional HOLD |
| ACTUAL_EXIT_CODE_REQUIREMENT | 每個實際command記argv/cwd/time/output/exit；fault subprocess與runner分開；本Goal全部[未執行] |
| EVIDENCE_REQUIREMENT | criterion→oracle→actual output/hash→exact candidate；environment fingerprint、before/after、SKIPPED blocking分類 |
| ROLLBACK_RECOVERY | 保留Human工作與歷史；只回退可歸屬本Goal內容；migration須approved backup/restore rehearsal，未知資料不自動repair |
| REVIEW_CANDIDATE_REQUIREMENT | 授權後local immutable candidate commit→packet/handoff→STOP WRITING；不push |
| COMPLETION_CRITERIA | 本contract正負criteria全部有fresh evidence，required skip不可PASS；scope/invariant自查；REVIEW_READY交獨立review；不宣稱Working Product完成 |
| INDEPENDENT_REVIEW | Human-designated ChatGPT Review Context；writer != reviewer；正式F4為獨立文件consistency gate |
| PUSH_RECOMMENDATION | DO_NOT_PUSH；需獨立PASS/recommendation及Human exact SHA批准 |
| NEXT_GOAL | TA-S0-G02；需其本身授權，不從NEXT推permission |

## Authorization-time elaboration

此為具體行為與責任拆分，尚非實作授權。讀 predecessor actual files 後填 exact branch/SHA、allowlist/new-file責任、現存runner及測試command、必需fixtures、owner/成本/外部權限。不存在的test不捏造命令；未解關鍵欄位不得AUTHORIZED。普通實作配置不必逐步Human確認。S0 aggregate criteria以Work Packages S0完整正負例為準。
