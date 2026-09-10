# TA-LR-01 — Legacy Open Work Closure & Safe Lane Preparation

DEFINED_NOT_EXECUTED / PLANNED / NOT_AUTHORIZED。本檔不是執行授權。

[Framework](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) · [Legacy register / HD-L1–L3](../governance/POLYNEXUS_LEGACY_OPEN_WORK_RECONCILIATION.md) · [Goal template](_GOAL_TEMPLATE.md)

## Goal contract

| Field | Value |
|---|---|
| GOAL_ID | TA-LR-01 |
| TRACK | Track A V1 |
| PARENT_STAGE / PARENT_WP | GOVERNANCE_REPOSITORY_RECONCILIATION；Operating Model acceptance之後、Formalization之前 |
| EPIC_GOAL | Legacy closure and safe lane proposal |
| OBJECTIVE | 查清relevant legacy工作、逐項分類映射Track A、提出safe lane/exact predecessor及HD-L1/L2/L3最終決策包，完成到REVIEW_READY |
| WHY | 消除第二套legacy派工來源與未知overlay/authority；F1及S0不能靠聊天記憶或dirty工作HEAD開始 |
| CURRENT_STATE | coarse legacy register存在；HD-L1/2/3未Human決定；逐項inventory與safe lane尚未完成；Product HOLD |
| TARGET_STATE | 完整bounded inventory、明確單一目的地、可審exact predecessor/lane proposal、preservation與remote可重現證據、review packet；Human決定前不宣稱已接受 |
| INPUTS / INPUT | current AGENTS/Project State/Roadmap/Handoff、Current Goal、Freeze Record/REV1/Work Packages/Change Plan、legacy register、previous Gxx/WPxx/findings/TODO、Human授權與當前exact Git refs |
| PREDECESSOR_CHECKPOINT | Operating Model accepted pair (R_OM,C_OM)，full SHAs/remote/intake未指定；須授權前驗證。不是b87或僅f34 |
| IN_SCOPE | read-only Git/topology/source比較；governance classification；decision packet；safe lane與exact checkpoint proposal；fresh evidence |
| OUT_OF_SCOPE | 產品實作、F1 exact formal diff、formal sync、架構重開、產品或legacy code stage/commit/push、实际lane操作、真實DB修復 |
| READ_SCOPE | relevant local/approved remote refs、branch topology、tracked/dirty/untracked manifest、previous acceptance與Gxx/WPxx unfinished、formal/source/runtime overlays、unknown findings/TODO及其必要證據。未知敏感內容只記安全metadata/ref，不抄secret |
| WRITE_SCOPE / EXPECTED_FILE_AREAS | 僅Goal-owned governance inventory/decision/evidence/handoff檔案：docs/goals/TA-LR-01.md之execution metadata、docs/reviews/TA-LR-01/、docs/handoffs/TA-LR-01/、必要legacy register disposition；依exact授權allowlist，不改其他scope |
| ALLOWED_FILES | NONE until Human execution authorization；規劃exact proposed outputs見下一節，receipt paths須另在Goal授權中明列 |
| FROZEN_INVARIANTS | 全部I-01..I-23保留；重點I-01/02/14/15/19/21/23；原文在Freeze Record §3，不複製改寫 |
| DEPENDENCIES | Operating Model independent PASS + Human acceptance + C/R remote closure；exclusive governance Writer授權；relevant sources可讀 |
| INTEGRATION_DEPENDENCIES | SEQUENTIAL_REQUIRED；無parallel legacy merger；F1須本Goal accepted receipt及Human HD-L決策 |
| PREFERRED_GOAL_OWNER / GOAL_OWNER | CODEX |
| PREFERRED_IMPLEMENTATION_WRITER | CODEX（此Goal是governance Writer，非產品Writer） |
| AUTHORIZED_WRITER / AUTHORIZED_IMPLEMENTATION_WRITER | NONE |
| WRITER_AUTHORIZATION_SOURCE / ACTIVE_WRITER_SCOPE | NONE / NOT_ACQUIRED |
| RECOMMENDED_REASONING_MODEL | SOL MEDIUM |
| MODEL_FALLBACK | LUNA MAX僅bounded inventory/classification |
| ESCALATION / MODEL_ESCALATION_RULE | 僅architecture conflict、security issue、migration ambiguity、Frozen risk、formal authority conflict升ASTRA MEDIUM；required unavailable HOLD |
| EXECUTION_MODE | SEQUENTIAL_REQUIRED |
| BRANCH_POLICY / BRANCH_STRATEGY | authorization時指定獨立governance review lane/exact branch；保護主dirtytree。safe product lane僅proposal，不自行checkout/merge/push；本Goal candidate只commit approved governance outputs |
| CROSS_MACHINE_HANDOFF_REQUIRED | YES；accepted pair(R,C)與下一F1 routing |
| REMOTE_CHECKPOINT_REQUIREMENT | Human接受本Goal C時可同次批准ONE_BOUNDED_ACCEPTANCE_RECEIPT_CLOSURE；R integrity及remote verified後F1才可intake；不推定已授權F1 |
| POSITIVE_CHECKS / POSITIVE_TESTS | topology/ref可重讀；relevant item有source/hash/classification/單一destination；accepted bounded evidence不被升格；before/after保全；HD-L1/2/3完整options/recommendation/impact；safe SHA/remote/lane proposal可查核 |
| NEGATIVE_CHECKS / NEGATIVE_TESTS | unknown item保留；duplicate/missing/多destination阻completion；stale/missing approval或remote證據不能稱ready；old bounded PASS不成Working Product PASS；b87/f34不默認executable predecessor；不以清理消除未知 |
| FAIL_CLOSED_CONDITIONS | Frozen conflict、destructive need、active writer conflict、authority ambiguity、unrecoverable data uncertainty、無法確認required source/evidence；先完成可獨立查明部分，再交完整decision packet |
| ACTUAL_EXIT_CODE_REQUIREMENT | 每次exact argv/cwd/timestamp/actual exit/bounded output；Git read非測試PASS；UNKNOWN/SKIPPED逐項blocking分類 |
| EVIDENCE_REQUIREMENT | repo/ref/HEAD/index/dirty inventory、safe source refs/hashes、diff statistics與必要hunks、legacy ITEM_ID ledger、decision sources、remote SHA observations、reproducibility proof及unverified限制、environment fingerprint |
| ROLLBACK_RECOVERY | unknown PRESERVE/CLASSIFY/REPORT；只回退本Goal可歸屬governance bytes；保留history/failed evidence；不reset/clean/prune/刪資料 |
| COMPLETION_CRITERIA | 所有15項工作及正負checks有current evidence；每relevant item分類完整、每retained item恰一destination；所有可自行查明內容完成，剩Human choice完整列出；local candidate/packet/handoff → REVIEW_READY。Human批准HD-L及receipt closure是後續acceptance gate，不要求Writer自批 |
| REVIEW_CANDIDATE_REQUIREMENT | authorization後可自行建立local immutable governance C，不含legacy code；exact allowlist比較通過後commit、new SHA、STOP WRITING；不無條件push |
| INDEPENDENT_REVIEW | Human-designated independent ChatGPT Review Context，writer != reviewer；actual exits、preservation、classification、authority/safe-lane proposal與C exact diff |
| PUSH_RECOMMENDATION | DO_NOT_PUSH until independent verdict + Human authorization |
| NEXT_STAGE / NEXT_GOAL | F1；LR accepted/Human disposition前不進F1 |

## Bounded execution and output plan

Human授權時將以下expected outputs轉為exact allowlist：`docs/reviews/TA-LR-01/legacy-items.json`、`decision-packet.md`、`safe-lane-proposal.md`、`evidence-manifest.json`，`docs/handoffs/TA-LR-01/review-ready.md`，必要Goal metadata與legacy register。不允許整個docs目錄blanket write。receipt-only paths按Framework §5預先批准，不包含上述reviewed result bytes。

授權後Codex自行完成：

1. Inspect current Git topology（refs、HEAD、branch、tracking、ownership metadata）。
2. Inventory relevant previous branches；不因發現一條branch逐次問Human。
3. Inventory dirty/untracked overlays；保留原bytes/hash/owner未知狀態。
4. Inspect previous Gxx/WPxx unfinished work。
5. Inspect existing Project State/Roadmap/Handoff，區分歷史與current authority。
6. Identify previously accepted bounded work及其exact evidence範圍。
7. Identify unfinished/ambiguous work，不推定名稱相同即covered。
8. Identify F1相關formal-document overlays（只讀，不產F1 formal diff）。
9. Identify S0–W6相關source/runtime overlays（只比較，不採納）。
10. Identify unknown findings/TODO，保留可追溯source。
11. Map retained work to exactly one current Track A destination。
12. Prepare safe implementation lane proposal及dirty preservation strategy。
13. Prepare recommended exact predecessor SHA與remote/cross-machine reproducibility proof；不建立/checkout/merge/push推薦lane。可用read-only object/ref驗證；尚未clone/intake實測標[待驗證]，不得稱fresh-clone PASS。
14. Prepare HD-L1/L2/L3 final decision packet，先查完所有能自行查明內容。
15. 收集evidence、self-validation、local review candidate與handoff，到REVIEW_READY停止。

## Classification contract and Human decision packet

每個ITEM_ID必有source/ref/hash、過往狀態/evidence、CLASSIFICATION（六選一）、PRIMARY_DESTINATION（恰一）、dependency refs、preservation ref、rationale、uncertainty、decision owner。

CLASSIFICATION: CARRY_FORWARD / ALREADY_COVERED / SUPERSEDED / OBSOLETE / REQUIRES_REVALIDATION / REQUIRES_MIGRATION。
PRIMARY_DESTINATION: F1-F4 / S0 / W1 / W2 / W3 / W4 / W5 / W6 / B01 / N1 / NEXT。
inventory總數必等於分類總數；每relevant item有唯一ID，缺項或多目的地FAIL。跨WP需求拆item或只寫dependency，不給第二primary destination；OBSOLETE也保存歷史，不等於可刪。

RECOMMENDED_HUMAN_DISPOSITION（不是Agent approval）：HD-L1保留G30 historical NEED_ACTION，route NEXT/separate external release verification，不阻B01、不external certify。HD-L2逐項bounded reconciliation，不bulk merge/delete/reset/clean/absorb；未知最後列NEEDS_HUMAN_DECISION。HD-L3 b87 dirty不是實作predecessor，f34只design/read；推薦真正Human-approved remote-verifiable exact checkpoint/lane。

RECOMMENDED_IMPLEMENTATION_PREDECESSOR_SHA: UNASSIGNED / 待本Goal調查；本R2不得編造SHA。
RECOMMENDED_IMPLEMENTATION_BRANCH_LANE: UNASSIGNED / 待本Goal調查與Human批准。
最終packet須填可驗證SHA/remote/ref或明確blocking缺口、dirty保全與跨機重現證據，不能以這兩個placeholder結案為accepted ready。

不允許bulk merge/adopt old branches、destructive checkout、reset、clean、prune、rebase、刪unknown untracked、overwrite dirtytree、auto repair production data或stage/commit/push legacy code。一般比較/分類/修正可自行完成；真正Frozen/安全/authority/不可恢復資料問題才HOLD。

本Goal產生的是decision packet，不是Human決策。Independent review後Human可一次處理HD-L1/2/3與接受C及bounded receipt closure；缺批准維持HOLD，不能把建議當已批准。F1接方先fetch R，讀C與Human disposition，再確認F1本身授權。

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
