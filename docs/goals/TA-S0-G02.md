# TA-S0-G02 — CREATED未execute的restart與未知execution隔離

[Framework](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) · [Template](_GOAL_TEMPLATE.md) · [Work Package criteria](../reviews/POLYNEXUS_TRACK_A_IMPLEMENTATION_WORK_PACKAGES.md) · [Formal Change Plan](../reviews/POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md)

## Contract

| Field | Value |
|---|---|
| GOAL_ID | TA-S0-G02 |
| TRACK | Track A V1 |
| PARENT_WP | S0 |
| EPIC_GOAL | Stability Foundation |
| GOAL_STATUS | PLANNED / NOT AUTHORIZED |
| OBJECTIVE | CREATED未execute的restart與未知execution隔離 |
| WHY | 消除 S0 前置缺口，形成可獨立審查的 bounded checkpoint，不把 WP 當巨大 coding prompt |
| CURRENT_STATE | CREATED restart 缺口未修 |
| TARGET_STATE | intent安全保留；未知running不duplicate launch |
| INPUT | Freeze Record / REV1 / Work Packages / Formal Change Plan；canonical design/read f34e6b29ae9e7326d1d44b9b03756b450809928f |
| PREDECESSOR_CHECKPOINT | UNASSIGNED；TA-S0-G01 accepted checkpoint；授權前填 accepted exact SHA/remote/decision refs，不能用設計SHA冒充 |
| IN_SCOPE | CREATED未execute的restart與未知execution隔離 |
| OUT_OF_SCOPE | 其他WP、scope擴張、未批准public runtime/binding/identity/trust變更、真實資料破壞 |
| ALLOWED_FILES | NONE；PLANNED不授權寫入，按下列責任與predecessor diff形成exact allowlist後再Human授權 |
| EXPECTED_FILE_AREAS | runtime/reconciliation.py、execution/startup相關既有責任與tests；不假造binding |
| FROZEN_INVARIANTS | 全部適用；重點 I-01/12/13/15/17/20/21/23；原文 authority為Freeze Record §3與REV1 §24 |
| DEPENDENCIES | TA-S0-G01 accepted checkpoint |
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
| POSITIVE_TESTS | API create→不execute→restart 仍可用；合法bound state reconcile |
| NEGATIVE_TESTS | unbound CREATED不crash整體；unknown running隔離、不duplicate launch；corrupt facts可診斷 |
| FAIL_CLOSED_CONDITIONS | 缺授權/exact predecessor/安全ownership/required evidence；或Framework exceptional HOLD |
| ACTUAL_EXIT_CODE_REQUIREMENT | 每個實際command記argv/cwd/time/output/exit；fault subprocess與runner分開；本Goal全部[未執行] |
| EVIDENCE_REQUIREMENT | criterion→oracle→actual output/hash→exact candidate；environment fingerprint、before/after、SKIPPED blocking分類 |
| ROLLBACK_RECOVERY | 保留Human工作與歷史；只回退可歸屬本Goal內容；migration須approved backup/restore rehearsal，未知資料不自動repair |
| REVIEW_CANDIDATE_REQUIREMENT | 授權後local immutable candidate commit→packet/handoff→STOP WRITING；不push |
| COMPLETION_CRITERIA | 本contract正負criteria全部有fresh evidence，required skip不可PASS；scope/invariant自查；REVIEW_READY交獨立review；不宣稱Working Product完成 |
| INDEPENDENT_REVIEW | Human-designated ChatGPT Review Context；writer != reviewer；正式F4為獨立文件consistency gate |
| PUSH_RECOMMENDATION | DO_NOT_PUSH；需獨立PASS/recommendation及Human exact SHA批准 |
| NEXT_GOAL | TA-S0-G03；需其本身授權，不從NEXT推permission |

## Authorization-time elaboration

此為具體行為與責任拆分，尚非實作授權。讀 predecessor actual files 後填 exact branch/SHA、allowlist/new-file責任、現存runner及測試command、必需fixtures、owner/成本/外部權限。不存在的test不捏造命令；未解關鍵欄位不得AUTHORIZED。普通實作配置不必逐步Human確認。S0 aggregate criteria以Work Packages S0完整正負例為準。

## Mandatory review package delivery

依[canonical package skill](../../.agents/skills/polynexus-review-package/SKILL.md)，此contract的動態交付值在C後external delivery.json填實，不修改C以填自己的ZIP hash。未填/未驗證不能REVIEW_READY。

```yaml
REVIEW_LEVEL: UNASSIGNED # choose L1/L2/L3 by risk before execution
REVIEW_PACKAGE_REQUIRED: YES
REVIEW_PACKAGE_FORMAT: ZIP
REVIEW_PACKAGE_PATH: PENDING_EXTERNAL_DELIVERY_RECORD
REVIEW_PACKAGE_SHA256: PENDING_EXTERNAL_DELIVERY_RECORD
REVIEW_CANDIDATE_SHA: PENDING
PACKAGE_VALIDATION_STATUS: NOT_RUN
REVIEW_PACKAGE_MINIMUM_CONTENT: canonical skill standard package
GIT_BUNDLE_REQUIREMENT: canonical skill review-level policy
FRESH_EVIDENCE_REQUIREMENT: candidate-bound actual evidence; historical reference only
ENVIRONMENT_FINGERPRINT_REQUIREMENT: canonical skill environment fields
PACKAGE_COMPLETENESS_CRITERIA: all mandatory payloads and required parts; hashes valid
REVIEW_READY_GATE: NO_REVIEW_PACKAGE = NOT_REVIEW_READY
```
