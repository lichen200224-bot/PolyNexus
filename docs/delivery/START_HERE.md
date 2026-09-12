# 完整初版＋新版擴充：唯一文件與開工入口

Date: 2026-09-13 (Asia/Taipei)
Task: PREP-FULL-DELIVERY-01
State: DOCUMENTATION_CANDIDATE / INDEPENDENT_DESIGN_REVIEW_REQUIRED
Active branch: planning/full-delivery-design-consolidation
Product implementation: HOLD_PENDING_START_GATES
Product version: UNCHANGED

Human已授權ChatGPT補齊前置文件、Git/GitHub發布與文件整併，正式產品開工交Codex；正常開發/UT/SIT/review/fix由AI處理，Human最後檢核。新增要求是各功能開發範圍、限制、子項及依賴必須事先清楚。本文件包實現這個規劃，不縮減Git定稿初版＋確認的新版增量。

## 閱讀順序與單一來源

| 目的 | 入口 |
|---|---|
| 每個功能做什麼/不能做什麼 | [FEATURE_WORK_PACKAGES](FEATURE_WORK_PACKAGES.md)、[FEATURE_SCOPE_MATRIX](FEATURE_SCOPE_MATRIX.json) |
| PN來源、完整功能與AC | [REQUIREMENTS](REQUIREMENTS.md)、[PRD](PRD.md)、[TARGET_AND_TEMPLATE_CONTRACTS](TARGET_AND_TEMPLATE_CONTRACTS.md) |
| 來源身份與接受範圍 | [SOURCE_LOCK](SOURCE_LOCK.json)、[SOURCE_INDEX](SOURCE_INDEX.md) |
| 全分支處置與衝突 | [BRANCH_DISPOSITION](BRANCH_DISPOSITION.md)、[GIT_RECONCILIATION](GIT_RECONCILIATION.md) |
| 系統分析/設計 | [SA](SA.md)、[SD](SD.md)、[DATA_AND_API](DATA_AND_API.md) |
| UX、Runtime、安全 | [UX_SPEC](UX_SPEC.md)、[RUNTIME_AND_MODULES](RUNTIME_AND_MODULES.md)、[SECURITY](SECURITY.md) |
| 測試/安裝/備份/可攜 | [TEST_PLAN](TEST_PLAN.md)、[OPERATIONS](OPERATIONS.md) |
| 批次執行及既有成果 | [GOAL_PLAN](GOAL_PLAN.md)、[EXECUTION_CONTRACT](EXECUTION_CONTRACT.md)、[IMPLEMENTATION_LEDGER](IMPLEMENTATION_LEDGER.md) |
| 本次修復與驗證 | [REPAIR_RECORD](REPAIR_RECORD.md)、[REPAIR_VALIDATION](REPAIR_VALIDATION.json)、[DECISION_AND_GAP_REGISTER](DECISION_AND_GAP_REGISTER.md) |
| F001／F002逐值契約 | [ASSURANCE_CONTRACT](ASSURANCE_CONTRACT.md)、[ASSURANCE_TRACEABILITY](ASSURANCE_TRACEABILITY.json) |
| 獨立審查與Codex交接 | [DESIGN_REVIEW](DESIGN_REVIEW.md)、[CODEX_HANDOFF](CODEX_HANDOFF.md) |
| 最後交Human | [UAT_AND_RELEASE](UAT_AND_RELEASE.md) |

22功能包/78 PN/257規劃子項是可追溯分解，不是已完成產品或已通過全部原子source審查。每包包含allowed areas、forbidden、inputs/outputs、deps、正負SIT、UAT，每PN另有細部分解與limits；原frozen義務不因摘要刪除。

## 來源與狀態分離

產品保留SHA為f0c0b986380dc21d103d4e856057cb8ac435a8f9。Track A正式增量與TA-F4接受receipt來自43aa27c8b7a1b950645acc0d41234ec7679b653e，Frozen REV1/Work Packages來自fe2eb2318dc6558afe1aa6c5361756b082c90c74；GOV來源1ea8ce3df9bf6b1fc0899fcafaedeba2f4052af4。選定原件以exact blob保存，不直接覆蓋最新產品tree或舊接受歷史。

MCF-02候選030890b30160f1063ac2cef1d36705a9ea70bddb仍待獨立review、未接受且未合入產品碼。原G24–G30 bounded100/100不是整個PolyNexus完成。兩個歷史ADR-013以ADR-MOD-013及ADR-ID-013消歧，不改原text/Golden。

## 發布與開工邊界

前置docs的commit與non-force發布已獲授權；整併為一條文件接續線不等於盲merge全部未審程式。原分支/default與產品source保留。原件內過期NEXT_GOAL/NOT_STARTED/95分是歷史，不是本branch的routing。入口為AGENTS＋docs/37＋本頁。

作者可報結構self-check、actual exits、GitHub API publication；不可自行Independent PASS。正式開工先達設計審查、source closure、實機ownership/clean取得、target/安全/有限資源及有效start receipt。已具Human條件授權者不逐GOAL重問；缺不可委派條件者集中報例外。

B01-TECH是內部技術里程碑，不縮小全功能或冒Human接受。必要Human-only UAT在最後集中完成；Agent credentials、fixture principal、Git授權不能替代真正Human決定。

## 修復與實際驗證範圍

前身1489cd7f的Human轉交獨立審查為NEED_FIX（F001 MAJOR、F002 MINOR、F003 OBSERVATION）；本次是原Writer同範圍修復，不能自判independent closure。PN-078恢復Assurance、PN-038澄清human override遙測。新評估與驗證結果見REPAIR_RECORD/REPAIR_VALIDATION；PREPARATION_VALIDATION.json是前身作者自檢歷史，SOURCE_LOCK原source pins及references不變。

本次planning validator/selftest對已驗byte的文件子集執行；不是完整Git clone，也不是產品測試或獨立審查。Git CLI DNS仍受阻exit128，API發布/readback另記，不能冒CLI push/clean-clone PASS。exact新Candidate/tree/parent以PR publication receipt為準。修復後仍須fresh Reviewer按新SHA完整DR-01–14重審，不只看兩項修正。產品HOLD不變。
