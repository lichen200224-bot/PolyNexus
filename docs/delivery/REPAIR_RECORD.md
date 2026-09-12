# PREP-FULL-DELIVERY-01：F001／F002 文件修復交接

Date: 2026-09-13 Asia/Taipei
Role: PREPARATION_DOCUMENT_WRITER
Status: WRITER_REPAIRED_PENDING_FRESH_INDEPENDENT_REVIEW
Direct predecessor: `1489cd7f7d54800317cc5558c92041a38c229008`
Product preservation base: `f0c0b986380dc21d103d4e856057cb8ac435a8f9`
Branch: `planning/full-delivery-design-consolidation`；PR #1 保持 Draft，不 merge。

## 1. 審查輸入與權限

Human 轉交五份 Reviewer 原件；檔名/byte size/SHA-256及原裁決見[REVIEW_INPUT_RECEIPT](REVIEW_INPUT_RECEIPT.json)。原 Candidate 裁決仍為 NEED_FIX，原 F001=MAJOR、F002=MINOR、F003=OBSERVATION。作者不回寫 Reviewer 報告，不將作者修復當獨立關閉。

本輪沿用 Human 已明確給予的同範圍前置文件/Git/GitHub non-force publication 權限，不從 Reviewer 文件取得額外權限。不更動產品 source/tests/migrations/dependencies、Frozen 原件、Human/security authority、既有 MCF candidate 或產品版本；不啟動 Codex product batch。

## 2. Finding-to-change

| Finding | 作者修復 | 證據／仍需重驗 |
|---|---|---|
| PREP-IDR-F001 | 新增PN-078，由FD-12唯一主責；三Mode、四Status、模式選擇/快照、Status衍生/失效、資料/DTO/UX/legacy及限制，11項子功能；不混成PN-052 | [ASSURANCE_CONTRACT](ASSURANCE_CONTRACT.md)、[ASSURANCE_TRACEABILITY](ASSURANCE_TRACEABILITY.json)、REQUIREMENTS、matrix及各設計/測試引用；Fresh Reviewer須確認語意與來源完整性 |
| PREP-IDR-F002 | PN-038/FD-19補human override受限遙測，合法Human相對AI建議分歧、source event去重、UNKNOWN/0區別；單向讀取，無Override Accept | §5定義及AT-038-MP01/02/MN01/02；負例要求metric無AcceptanceRecorded/eligibility/outcome副作用；產品案例尚未執行 |
| PREP-IDR-F003 | 移除固定77/154等報告計數，依REQUIREMENTS/matrix計數；從3份pinned source核對7個Assurance值與逐項映射，增加刪值/來源/owner/oracle/metric越權反例 | 檢查仍限PLANNING_STRUCTURE_ONLY及明列映射，非完整semantic/source/產品/獨立PASS |

目前計數：22 FD、78 PN、257分號子項；156個P/N命名測試群只是78×2的規劃群數，不是產品test數。新增26個具體產品案例規格（PN-078 11對＋PN-038 4例），尚未實作/執行。[REPAIR_COVERAGE_DELTA](REPAIR_COVERAGE_DELTA.json)只映射原審查3 GAP及1 CONFLICT，均標作者修復待審，不把94 VERIFIED歷史直接搬成新Candidate結論。

## 3. 實際作者驗證與限制

本環境GitHub connector可讀寫，但Git CLI `ls-remote`仍因DNS失敗，actual exit=128。本次在repo外materialize必要文件子集，原文件及3份直接Formal來源逐byte Git blob校驗；新checker對這些檔案執行。**這不是完整clone，也不是使用者Windows工作樹。**

- `python -B docs/delivery/checks/validate_feature_scope.py --requirements docs/delivery/REQUIREMENTS.md`：actual exit=0；22/78/257、DAG與7值明列映射通過。
- `python -B docs/delivery/checks/selftest_feature_scope.py`：actual exit=0；27 cases，1個valid child exit0、26個負例child exit1，且拒絕reason符合。
- `git diff --no-index --check <materialized-parent-docs> <new-docs>`：actual exit=1，沒有whitespace diagnostics。另以equal/clean-different/trailing-whitespace校準，分別exit0/1/3；此結果不冒充完整commit-to-commit `git diff --check`。
- 完整Git clone／exact commit diff --check、Windows/live/account/quota/start gate、產品tests與Human UAT均未由本輪完成；不推定舊環境限制已解除。

Exact argv/cwd/timestamps/exits、input file digests、checker結果見[REPAIR_VALIDATION](REPAIR_VALIDATION.json)。根據前置source lock的22份references保持原blob；發布時產品root tree/refs對照與新commit/tree/parent在PR publication receipt另記，避免self-referential commit循環。

## 4. 下一步

Fresh Independent Reviewer使用新publication receipt的exact SHA，重新查branch/PR/parent/tree、全部base-to-Candidate變更、source pins、DR-01～14，並明確裁決F001/F002及F003修改。不要只讀作者修復表或重用作者exit。

若CLI仍被阻擋，可在隔離目錄從API取得所需文件，逐檔對照新Candidate的blob SHA後執行planning checker；必須標BYTE_VERIFIED_SUBSET，不冒Git clone。不能取得/核實byte就記NOT_RUN/UNKNOWN。

Independent closure: PENDING。
DOCUMENT_DESIGN_VERDICT：等待Fresh Reviewer，作者不給VERIFIED_PASS。
EXECUTION_START_READINESS：HOLD。
PRODUCT_START_AUTHORIZED：NO。
