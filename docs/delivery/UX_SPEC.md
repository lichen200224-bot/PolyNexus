# UI / UX 流程與使用者驗收設計

Status: DESIGN_DRAFT。首頁仍Project→Discuss/Review/Validate；Develop屬動作，不新增頂層入口。Runtime/Model/Policy/Doctor以progressive disclosure展開。

## 1. 畫面與必要狀態

| Screen | 必要內容/主要action | Empty/loading/error與安全行為 |
|---|---|---|
| Workspace/Project | Create/Open/Archive、分類、近期Task與結果 | 無專案提供Create；load/error可重試，Archive不刪accepted歷史 |
| Task setup | mode/template、目的/scope/AC、context/artifact選擇、repo/baseline | 明示缺必填/不相容；未選dirty預設排除，顯示excluded數量而非洩露內容 |
| Run preparation | role/runtime/model、分類/目的地、可用能力、budget、必要批准 | 分開已安裝/health/readiness/policy；not ready不可按Start；無silent fallback |
| Work monitor | generation/Run、4-axis facts、進度、events、cancel/abort、recovery | HTTP accepted顯示準備中，不假RUNNING；連線失敗保留上次observed time並重連查durable |
| Discuss/Council | 各role原稿、cross review、共識/分歧/風險 | partial role失敗可查看已完成輸出；不可杜撰缺失結果 |
| Review findings | artifact/code位置、severity、來源、理由、建議 | 可篩選/定位；AI opinion與tool evidence有不同標籤 |
| Candidate view | exact Candidate/publication、變更摘要/檔案、requirements、validation | 不使用浮動latest替換頁面；switch candidate清除舊challenge |
| Verification | required/optional、applicability、outcome、validity、command/evidence | SKIPPED/ERROR/MISSING/STALE/MISMATCH均可理解；required缺證阻Accept |
| Human decision | exact view＋eligibility、Accept/Reject或Revoke/Supersede | 只有Human session可操作；無Override；stale刷新並再次呈現內容 |
| Accepted result | immutable accepted內容、歷史accepted、current disposition | Open Accepted Managed Worktree；takeover後大字標Working Copy based on Candidate，不冒稱immutable |
| Web handoff | launch/fill/confirm-send/capture/associate | capture失敗明示clipboard/manual/launch-only，不自動再send |
| Settings/Doctor | config來源、versions、capabilities/maturity、routing、resources | 未測UNKNOWN、不具備UNSUPPORTED；敏感設定只顯示reference |
| Export/Backup | P0/N1/backup明確分別、scope、hash/closure結果 | failure不產生看似完整套件；不匯出Human session或secret |

## 2. 主要操作流程

工程：開Project→選Review/Validate與bug-fix workflow action→選乾淨baseline或明選dirty snapshot→確認scope/AC/runtime/route→Begin/Start→監看→freeze→deterministic驗證→查看exact diff→Human Accept→Open Accepted Result→選擇export。這條必須在真實UI測試，不可只用API成功冒充。

一般文件：選Artifact→Review/Discuss模板→選role/AI→查看各自結果與分歧→選Validate所需rules→查看Evidence→保存報告與Decision。流程不要求使用者理解RuntimeBinding或手動編JSON。

Retry：畫面先說明舊generation與原因、舊writer是否安全釋放、選擇續用/變更input；執行後顯示新的g2。舊g1的Cancel/Abort按鈕始終綁其exact target，不能指向最新Run。

## 3. Human decision exact-view

View包含CandidateID、選定publication、source/requirements/validation references、checks/evidence eligibility、當前review/decision revision。前端不得從local storage組合一份不存在於server的accepted view。

使用者選Accept時取得或使用fresh challenge，任何source/policy/evidence/candidate/revision改變立即失效。Server仍需提交時驗證；UI禁用只是UX不是security boundary。Double-click/斷線重送同command回同一receipt；無法確認結果時先GET receipt/decision，不再建新Accept。

Reject只適用未accepted Candidate。accepted後顯示Revoke與選定已有效接受replacement的Supersede；不將舊Accept塗改為Reject。歷史accepted與目前失效/撤銷要同時看得懂。

## 4. 控制與例外

Cancel是Run、Abort是generation，確認對話框列exact target與影響範圍；不以同一『停止全部』偷偷混合。cleanup unknown時標等待安全恢復，不能誘導點Start繞過鎖。

權限/分類/目的地變更呈現差異，若需Human-required approval則真的停在該gate。一般可由既有Core policy允許的local動作不新增多餘確認。產品必要Human gate不受開發批次授權影響。

## 5. 無障礙/防誤用

所有主要action可keyboard操作、具有label與可見focus；modal進出回復focus；錯誤不只靠顏色。長內容分區/搜尋/可展開原始證據，但不把raw secrets/server traceback直接塞畫面。狀態訊息區分working、partial、needs action、verified、accepted，避免以一個綠色Success混淆。

重要action保留idempotency與disabled pending狀態；refresh/back navigation不重送副作用。空/慢/離線/無權限/部分資料/長log皆有驗收例子。螢幕大小與實際browser版本由test profile記錄，不能僅靠單張圖宣稱responsive/無障礙通過。

## 6. UX oracle

UJ-01–UJ-10逐一以測試使用者操作記錄route、輸入、預期/實際、artifact/screenshot與negative path。成功要能從UI→server durable state→evidence交叉確認；screenshot不是內容完整性證據。人工體驗最終由Human UAT接受，AI rehearsal只能說準備就緒。
