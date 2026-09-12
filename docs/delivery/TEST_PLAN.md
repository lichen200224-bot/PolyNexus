# Master Test Plan — 完整功能、SIT、可靠性與證據

Status: TEST_DESIGN_DRAFT / TEST_EXECUTION_NOT_RUN。AT-001–AT-078 是 REQUIREMENTS.md 中的規劃案例ID，不是假稱目前已有這些test functions。原WORK各WP正負案例、REV1 Golden與I-01–I-23仍是必要oracle；此文件整併執行方式，不減少原驗收義務。

## 1. 測試層次與責任

| Layer | 目的/主要範圍 | 負責/環境 | Exit條件 |
|---|---|---|---|
| UT | 純Domain、canonical parsing、policy、state/revision、normalization | Writer；deterministic fixtures | 每個新增行為正負案例；critical oracle不能由同一實作產生expected值 |
| Contract | Runtime/Module、API、DB、Human、Candidate/evidence binding | Writer＋Fresh Reviewer；real local components及controlled process | 依固定契約與版本測試；mock不升為live |
| Component integration | API→Service→DB/artifact/workspace、每個DEV slice | Writer；temporary SQLite/synthetic repo | 正常與主要失敗路徑可連通；新行為不等正式SIT |
| SIT-T1 | UI→Core→real runtime→source/result→Evidence→Decision完整情境 | Independent Verifier；隔離可執行環境 | 必要功能跨模組完成，不靠developer手工改DB/檔案補結果 |
| SIT-T2 | 故障、安全、restart、race、migration、restore、clean install | Independent Verifier；受控故障與指定host | required failure/recovery oracle全滿足；環境缺失不可PASS |
| Live conformance | 指定provider/model/runtime/browser版本的實際能力 | Authorized specialized verifier | 真實版本/操作/副作用證據；Human-only步驟獨立記N/A exit |
| UAT rehearsal | 依繁中手冊從乾淨狀態走操作 | 未寫本patch的AI verifier | 形成READY_FOR_HUMAN_UAT，不產生Human Accept |
| Human UAT | 用途、操作與實際成果接受 | Human | exact delivered candidate與已披露限制由Human判定 |

## 2. Case contract

每個AT案例實作成test spec：case_id、PN refs、source/section、requirement_level、applicability predicate、precondition/seed、固定輸入、操作步驟、expected observable result、forbidden side effects、positive/negative分支、fixture/live/host profile、cleanup及evidence欄位。不能只寫『功能正常』。

Case implementation與oracle分開。REV1的expected IDs固定引用原值；不得用被測canonicalizer動態產生expected後比較自己。Policy/Human/generation負例由Reviewer追加獨立測資；Verifier的workspace可產生test/build cache，但不得修改canonical Candidate bytes或放寬validation contract。合法測試缺陷修正亦需新test/contract版本與受影響重驗，不默默把fail刪除。

## 3. 必要整合Scenario

| Scenario | 需求/層 | 必要操作與oracle |
|---|---|---|
| SIT-01 | PN-001/002/009/010；UT→SIT | Create Project/Task、固定Context/Artifact、restart/reopen；引用及hash相同、foreign refs拒絕 |
| SIT-02 | PN-043–048/064–067 | 新SQLite/FK、CREATED未execute restart；建立g1、並發/不同command啟動，只有一writer lineage；不修改Human dirty |
| SIT-03 | PN-016–021/068–073；LIVE | real synthetic bug repo：固定input→real cwd/change→stop/cleanup→Core import；實際檔案diff/測試結果可重現 |
| SIT-04 | PN-046/047/065/073；real process | g1失敗→安全釋放→Retry g2→late Abort(g1)；g2仍運作、ownership/fence不變；未知owner不重啟 |
| SIT-05 | PN-049–052；Golden＋DB | freeze→exact verification；篡改source/path/mode、missing blob、cross-Candidate EvidenceSet、stale contract全部拒絕 |
| SIT-06 | PN-053–058；API+browser | Human pairing/session/challenge→exact view Accept；Agent token、CSRF/Origin、nonce replay、revoked/expired session、view drift拒絕 |
| SIT-07 | PN-054/059/060；B01 | Open Accepted Managed Worktree→核對source→explicit takeover顯示Working Copy→P0export→乾淨位置重建；原accepted immutable |
| SIT-08 | PN-004–008/013–015 | Council独立初稿→cross review→synthesis、role partial failure、四Golden flows；九範本逐一真實執行 |
| SIT-09 | PN-022/023/027–030 | 三類local endpoints的可用能力與混用workflow；敏感/LOCAL_ONLY外部step被阻，實際route metadata一致 |
| SIT-10 | PN-024–026 | 真實MV3/三vendor Level3A及confirmed send；capture/driver失敗clipboard/manual fallback，Core仍可用 |
| SIT-11 | PN-031–042 | budget/timeout/concurrency、Doctor truthful maturity、兩module交換、不支援capability/unknown version拒絕 |
| SIT-12 | PN-034/035/039/061–063 | 代表性legacy DB upgrade/restore、P0/N1差異、跨路徑重建、REST cursor/WS重連去重、乾淨安裝 |
| SIT-13 | PN-036–038/077 | 按UX所有empty/loading/error/offline/keyboard/focus分支演練；metric來源可定位；無log才能完成的常態工作 |
| SIT-14 | PN-074–076 | 指定owned process故障/斷線/quota/重啟、batch checkpoint恢復、same-scope修復→獨立重驗；不因中斷重跑已接受全部歷史 |

| SIT-15 | PN-078、PN-038及FD-12/19 | [ASSURANCE_CONTRACT §6](ASSURANCE_CONTRACT.md#tests)：三Mode、四Status、快照/衍生/失效/DTO，metric不產生接受事件；每值有P/N oracle |

每Scenario仍細分AT案例，不以SIT-xx一列覆蓋全部細節。B01必須真實完成SIT-02–07適用部分，不能拿SIT-01 reference流程取代。T1/T2對完整交付的required功能核銷，不只B01。

## 4. 邊界與故障注入

Critical permutations：同generation不同command/入口/重連、不同Project共享profile、Abort/Publish/Cleanup競爭、同timestamp事件、paused verifier與晚到Human action、session revoke後challenge、config/binary/plugin drift、cleanup中改artifact、DB commit前後process中斷、migration中斷、缺失sourceclosure、跨平台path/symlink拒絕。

每個故障只作用於owned synthetic fixture；保留before/after hash、child副作用和parent runner結果。Negative child exit 1可是預期拒絕證據，但父測試仍須驗證正確reason與未發生非法效果；不能籠統要求所有child exit0。自然flaky必須找root cause，禁止無限retry、刪assertion或調sleep掩蓋。

## 5. 目前可確認的執行入口與未執行狀態

下列是原repo已有路徑/腳本，供後續隔離環境實際核對後執行，本輪沒有執行。使用明確選定的venv Python，記完整cwd與argv；不要依PATH碰巧選到另一Python。

```text
# repo root
python -B scripts/validate_baseline.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/validate-polynexus-governance.ps1 .
git diff --check

# services/core
python -m pytest --tb=short -rs

# apps/web
npm ci
npm test
npm run build

# repo root
node --test extensions/browser-companion/tests/test_websurface_drivers.mjs
```

`npm test`/`build`依apps/web/package.json；受影響test先針對實際檔名收集，再擴大。Playwright/browser runner須先確認repo當前安裝與可執行入口，缺失時建立於批准test scope，不捏造已存在script。MCF02兩個test檔只在候選branch存在，未整合前不能在f0基線直接當既有command。

## 6. Evidence receipt

每個receipt至少含：task/batch/case/PN IDs、document contract SHA、exact candidate/source tree SHA、Run/generation/publication/Candidate refs（適用）、command與cwd、input/env/fixture版本、tool/runtime/model可見資訊、start/end、actual runner exit及child exit/signal、actual counts/failure names、outcome/validity、artifact path/hash、SKIPPED原因、reviewer context、scope diff與protected checks。

Manual Human/browser操作無OS exit時寫`N/A`並保留操作與觀察證據；tool無回傳exit不能猜0。API HTTP狀態與OS exit分欄。長raw log放artifact，報告保留摘要/必要錯誤；秘密redact在持久化之前。

## 7. Evidence重用/失效規則

歷史accepted evidence可作baseline/變更分析，不冒成本輪新run。新source、dependency/config、schema、oracle/contract、runtime版本或policy變更，按影響圖重跑；Final Candidate的required端到端/安全/migration/包重建證據須與實際交付內容一致。僅更新不影響source的report不能要求每次無意义全庫重跑，但須有明確no-impact判定。

對docs-only本次準備：允許檢查tree/paths/來源blob/JSON/link/DAG；這不是產品tests PASS。Source_blob相同是byte identity，不是原文件所有歷史連結都存在的證明。

## 8. SIT exit / defect loop

所有適用required案例執行、有效/精確綁定、actual exits及oracles符合，無BLOCKER/MAJOR且完整需求核銷才可進UAT rehearsal。Optional skip須理由與影響；required skip/unknown/blocked不轉N/A。既有Windows symlink skip不可在新required security test上自動沿用豁免。

同範圍defect→Writer→new immutable checkpoint→targeted/affected/full-required regression→fresh review→close finding；不逐次找Human授權。若需改scope、frozen trust、不可逆資料或資源上限，依execution exception。測試全部綠不等Human接受或production release。

## 9. F001／F002 修復驗收與結構檢查

PN-078 的11個子項逐一使用[ASSURANCE_CONTRACT §6](ASSURANCE_CONTRACT.md#tests)的AT-078-P01–11／N01–11。PN-038新增AT-038-MP01/MP02/MN01/MN02：合法分歧/去重/UNKNOWN與metric不建立Human acceptance。具體source→子項→primary FD→design→oracle→SIT/HU在[ASSURANCE_TRACEABILITY](ASSURANCE_TRACEABILITY.json)。這26個是後續產品案例規格，不是本輪已執行測試。

本轮planning checker從REQUIREMENTS與matrix動態計數，並比對三份pinned source及七個Assurance值的完整映射；selftest移除各value/mapping/source/owner/oracle或偷偷賦予metric接受權必須fail。它只證明明列結構/引用，不能替代完整semantic review或產品test。舊PREPARATION_VALIDATION.json屬前身1489cd7f作者紀錄，本次結果另見REPAIR_RECORD.md及REPAIR_VALIDATION.json。
