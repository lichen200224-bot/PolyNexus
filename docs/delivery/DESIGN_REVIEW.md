# 前置文件獨立設計審查契約

Status: REVIEW_SPECIFICATION / INDEPENDENT_REVIEW_NOT_RUN
Writer: ChatGPT preparation context
Review subject: exact published planning/full-delivery-design-consolidation commit

## 1. 角色與輸入

必須由未撰寫本patch的fresh AI context審查。先取得canonical remote實際SHA並比對publication receipt，再讀AGENTS、START_HERE、SOURCE_LOCK、GIT_RECONCILIATION、FEATURE_WORK_PACKAGES、FEATURE_SCOPE_MATRIX及相關原規格。f0c0b986是保留產品前身；後續文件commit以實際parent鏈為準。

Reviewer只讀受審candidate，驗證資料放隔離位置；不得改產品/原refs/已接受契約、自造Human批准、用作者摘要取代source-to-design核對。作者自檢與結構validator PASS都不是獨立語意審查。

## 2. 必要審查項目

| ID | Required check |
|---|---|
| DR-01 | branch/commit/parent與source locks正確，產品目錄未暗改，原refs沒有被force/rewrite/delete |
| DR-02 | 初版＋正式增量＋模組方向逐條繼承；每PN有唯一primary工作包、子功能、scope、限制、設計與測試，77行不是全原子覆蓋證明 |
| DR-03 | ADR-MOD-013與ADR-ID-013唯一引用，Golden及原byte保留，舊routing不得活化 |
| DR-04 | I-01–I-23逐一定位無矛盾，尤其generation/Run/Candidate/publication、same-lineage、Model B、canonical authority |
| DR-05 | Candidate quiescence/freeze、exact verification與EvidenceSet、四軸requiredness/applicability/outcome/validity不混淆 |
| DR-06 | Human-only principal/session/challenge、exact view、anti-replay/idempotency、CSRF/Origin、append-onlyhistory、D11-C fallback成立 |
| DR-07 | S0在真實工作前、generation/workspace先於launch、binding-before-effect、取消/timeout/cleanup與crash recovery無重複副作用 |
| DR-08 | MCF候選不冒accepted、staging/worktree責任一致、deny-all不當可改碼、live/config/權限設計有可行路徑 |
| DR-09 | 3入口/九範本/Council/Web/Local/兩深度Runtime/UX/Doctor/維護保留；B01不縮成完整產品範圍 |
| DR-10 | SQL/API/事件/併發/冪等/相容/遷移有實作契約，未知schema/API明示proposed，legacy不造可信資料 |
| DR-11 | 每項required有positive/negative oracle；test plans分fixture/live/host，required skip不自動waive，Case名稱不等已存在test |
| DR-12 | 操作/clean install/restore/P0source重建可落地；N1/WS保持階段與scope，不變成cloud sync |
| DR-13 | execution contracts可減少人工micro-gates但不冒充產品Human；預算/targets/ownership具備有效start條件 |
| DR-14 | 功能包依賴圖無循環；共享路徑單一寫入；integration順序和舊候選处置明確；source閉包/リンク/版本一致 |

## 3. Source closure與精確引用

作者文件所有實際relative link要解析。引用原件保留原byte，因此其historical連結可能指舊proposal；不得宣稱全部連結閉包天然成立。逐項分類normative/historical/external。Normative缺原文/Golden/接受依據即設計阻擋，先找exact source補齊，不能從摘要推定。

Source受審接受receipt的scope獨立記錄；不需要重做全部已接受歷史，但不能擴張該接受到新功能。本包版本仍Draft，沒有自動升版或正式freeze。

## 4. 機械檢查

有可執行Git的環境，對exact parent/candidate做diff --name-status、diff --check、protected path/tree comparison、remote SHA及clean checkout核對；不可只看Writer dirty working tree。解析SOURCE_LOCK/FEATURE_SCOPE_MATRIX，檢查PN唯一分配、所有功能子項有UT/SIT/UAT對應、DAG無循環、文件完整、來源blob相同。保留命令和actual exits。

原baseline/governance validators僅驗原有範圍；不能把其成功當本完整設計PASS。GitHub REST成功、local CLI exit、產品tests、Windows/live實驗分開記錄。無可用環境就標NOT_RUN/ENVIRONMENT_BLOCKED，不補造exit0。

## 5. 結果與修復

VERIFIED_PASS只在所有mandatory review項通過且无BLOCKER/MAJOR；NEED_FIX列可修缺陷；HOLD用於缺來源/授權/實機條件。Finding至少含id/severity、file/section、權威依據、影響PN/包、建議修復及可重驗oracle。

修復交前置Writer產生新SHA；Reviewer按impact重新檢查。文件作者可修，不得把自己的修復評語貼為independent verdict。若問題不是既有範圍內修正而是改Frozen/安全/產品承諾，集中Human change-control。

## 6. 輸出

reviewed documentation SHA/parent、source coverage、17+文件範圍的實際清單、PN/功能包/AT覆蓋、invariants、findings、命令/actual exits、not-run/限制、scope/ADR impact、VERDICT、是否滿足Codex啟動条件。最後只能推薦READY_FOR_CODEX_START_GATE，不以review報告直接啟動產品Writer或發布release。
