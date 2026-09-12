# Codex 完整交付批次與依賴

Status: DRAFT_FOR_INDEPENDENT_DESIGN_REVIEW / PRODUCT_START_HOLD
Primary scope: [FEATURE_WORK_PACKAGES](FEATURE_WORK_PACKAGES.md)及[FEATURE_SCOPE_MATRIX](FEATURE_SCOPE_MATRIX.json)。原PN、WORK S0/W1–W6/B01與frozen invariants保持；批次代號不是新產品版本，也不是每個都需Human批准。

## 1. 正常接續順序

| Unit | 工作範圍 | 技術完成與下一步 |
|---|---|---|
| PREP | ChatGPT整合文件/source/Git；FD-22 | exact docs checkpoint、fresh independent design review與一次性有界start receipt；未達不開產品 |
| D0 | FD-01、FD-20.MIG基礎核對；WORK S0 | FK、CREATED restart、schema/auth/health正負測試；不重做已接受ordering/cleanup |
| D1a | FD-02/03/04、FD-10.BASE、FD-18.BASE及必要migration | Project/input/context/generation/lineage/ownership、REST最小操作、政策/秘密邊界 |
| D2a | FD-05/06/07/08的第一核准target；WORK W2 | 先feasibility，再真cwd/change/cancel/cleanup/output；MCF候選先獨立審查再按責任整合 |
| D1b | FD-11→FD-12→FD-13→FD-14；WORK W3–W6 | Candidate/verification/Assurance assessment/Human協議/accepted result/P0；可用fixtures驗局部但不冒live |
| B01-TECH | FD-21.B01 subset | 小型真bug fix與failure/retry的技術鏈；Human-only尚未做標PENDING_FINAL_HUMAN_UAT，不稱B01_HUMAN_ACCEPTED |
| D2b | FD-08其餘required深度Runtime、FD-09、FD-06剩餘相容性 | 完整原定Codex/OpenCode/Local能力，逐target證據，不互借PASS |
| D3 | FD-15/16、FD-10.MIXED、FD-12 workflow gates | Council、九範本、完整workflow、安全雲地混用、真實證據 |
| D4 | FD-17/18、FD-19、FD-20.OPS及FD-02/03生命週期差額 | Web/UX/Doctor/guards/metrics/backup/clean install日用能力 |
| D4-NEXT | FD-18.WS、FD-20.N1 | 按原scope交付後續live通知與selected-task可攜，不變cloud sync/Enterprise |
| T1 | FD-21功能SIT | 全required正常情境，UI→Core→target→資料/證據完整串接 |
| T2 | FD-21可靠性/安全SIT | failure/race/ownership/egress/secret/migration/restore/clean-install等required evidence |
| DELIVERY | FD-21/22 | 完整PN/子項核銷、繁中手冊、exact套件/證據/限制、AI操作演練 |
| HUMAN_UAT | UAT_AND_RELEASE的HU-01–12 | Human集中完成必要真實操作与最後接受；同scope問題仍交AI修復回歸 |

B01-TECH不變更產品Human接受語意；只是避免開發流程在中途等待每個Human Gate。後續有必要依賴真實Human決定/帳號/外傳的步驟仍不得自動繞過。可以安全獨立開發的功能按依賴繼續。沒有實際Human Accept不能把fixture或test principal算成使用者接受。

## 2. 每批執行協議

每包先固定doc/base/candidate SHA、主責PN和所有子項、input/output、exact file allowlist、protected areas、角色、test profile/commands/oracles、finite resource、stop conditions。當次read-only inventory可解析內部symbol/path與現有可重用成果；不重問已決定的需求。

Writer依設計完成code＋UT＋contract＋integration smoke，request fresh review；finding回Writer修復、新candidate、受影響重驗，再接下一已批准包。所有低風險同scope操作包含於批次授權，不逐GOAL請Human。

JSON deps是技術facet依賴，不是全部UAT接受依賴。共享DB/migration/registry/execution_service/UI入口依FEATURE_WORK_PACKAGES§4由single Writer序列處理；不能因工具不同就平行覆盖。

## 3. 既有成果與Git整合

唯一前置文件線是planning/full-delivery-design-consolidation，從f0產品保留錨點接續。Track A正式/凍結、GOV、MCF文件在同一文件tree可讀；source pins保留原始lineage，不假造全分支merge。

MCF030890是待審程式候選，不能因把文件帶入就算accepted。獨立審查後，在指定integration checkpoint做semantic diff與新generation/ownership/publication契約整合；不能只看textual merge。原已接受成果保留，實作差額與required final tests按影響判定，不從頭重做整個產品。

舊F5/S0/Goal的Human逐項路由不自動活化。本次新start receipt會指定實際Codex base與整批權限，不抹掉舊決議也不由文件作者私自給未具條件的產品開工。

## 4. 接續與完成

Context/quota中斷保存safe SYNC及精簡handoff，record exact refs、已完成/未驗、findings及下一動作。新context重驗remote/owner/branch後接續；没有自动重啟能力就報CONTINUATION_READY，不承諾背景工作。

进度分設計覆蓋、差額實作、有效tests、independent review、Human接受。原100分分母不擴張；B01只是里程碑，不能替全功能交付。最終所有required PN/原條款/子項都要核銷，不能只報執行了多少GOAL。


## 5. F001／F002 的批次補充

PN-078/FD-12在D1b-W4交付Assurance基礎、D3串workflow/Council、D4串UI；依[ASSURANCE_CONTRACT](ASSURANCE_CONTRACT.md)及SIT-15/HU-03/06核銷。PN-038/FD-19在D4完成受限human override metric，SIT-13/06及HU-12驗無接受副作用。這是恢復既定範圍，不新增工作包、不改DAG、不多開coding Writer；修復Candidate仍待獨立重審。
