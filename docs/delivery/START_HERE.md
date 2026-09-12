# 完整初版＋新版擴充：文件與開工入口

Date: 2026-09-12 (Asia/Taipei)
Task: PREP-FULL-DELIVERY-01
State: DOCUMENTATION_CANDIDATE / INDEPENDENT_DESIGN_REVIEW_REQUIRED
Product implementation: HOLD
Product version: UNCHANGED

## 1. 已授權與尚未授權

Human 已同意完整文件先行、AI 負責正常開發/測試/審查/修復、最後由 Human 檢核，並明確授權 ChatGPT 處理本次前置文件及 Git/GitHub。這個授權不是模擬或 Agent 自行核准。本輪可在專用分支新增/整理文件、保存來源、commit、non-force publish、建立 draft PR；不得順帶接受 MCF-02 程式、改寫凍結契約或執行產品程式變更。

完整目標 = Git 定稿初版功能 + 已確認的新版增量 - 有明確來源的取代項。B01 第一條真實閉環只是里程碑，不是完整產品終點。P0/N1 與 CORE/BASELINE/COMPATIBILITY/FUTURE 保持來源分級；不得用分批執行之名刪掉 required 功能。

## 2. 單一導航，分開記錄事實

| 閱讀目的 | 文件 |
|---|---|
| 來源/接受邊界 | [SOURCE_INDEX](SOURCE_INDEX.md)、[SOURCE_LOCK](SOURCE_LOCK.json) |
| 分支狀況/整併/回退 | [GIT_RECONCILIATION](GIT_RECONCILIATION.md) |
| 已作出的設計梳理及未通過 Gate | [DECISION_AND_GAP_REGISTER](DECISION_AND_GAP_REGISTER.md) |
| 完整需求/驗收追溯 | [PRD](PRD.md)、[REQUIREMENTS](REQUIREMENTS.md) |
| 系統分析 | [SA](SA.md) |
| 系統設計及資料/API | [SD](SD.md)、[DATA_AND_API](DATA_AND_API.md) |
| 使用介面 | [UX_SPEC](UX_SPEC.md) |
| 安全/Runtime | [SECURITY](SECURITY.md)、[RUNTIME_AND_MODULES](RUNTIME_AND_MODULES.md) |
| 測試/非功能/操作 | [TEST_PLAN](TEST_PLAN.md)、[OPERATIONS](OPERATIONS.md) |
| AI 分批執行 | [GOAL_PLAN](GOAL_PLAN.md)、[EXECUTION_CONTRACT](EXECUTION_CONTRACT.md) |
| 獨立設計驗證 | [DESIGN_REVIEW](DESIGN_REVIEW.md) |
| 最後交付給 Human | [UAT_AND_RELEASE](UAT_AND_RELEASE.md) |

引用的詳細原件保存在 `references/`，以原 blob 重用；原件是有範圍的設計/歷史權威，不代表其舊 routing 或測試結果仍是本輪狀態。原主庫文件不大量覆寫，避免摧毀既有驗收履歷；本目錄是這次新文件基線的唯一工作入口。

## 3. 狀態不能混在一起

- 產品保留 SHA：f0c0b986380dc21d103d4e856057cb8ac435a8f9。
- Track A 正式文件接受來源：43aa27c8b7a1b950645acc0d41234ec7679b653e；TA-F4 receipt 記錄接受，不代表本輪重新獨立驗收。
- Track A 凍結詳細來源：fe2eb2318dc6558afe1aa6c5361756b082c90c74。
- 新治理來源：1ea8ce3df9bf6b1fc0899fcafaedeba2f4052af4；與產品線尚非同一合併基線。
- MCF-02 修復候選：030890b30160f1063ac2cef1d36705a9ea70bddb；READY_FOR_FRESH_INDEPENDENT_REVIEW / IMPLEMENTATION_ACCEPTED=NO。既有候選不是 NOT_STARTED，也不是已接受。
- G24–G30 100/100 僅是原 bounded acceptance；OVERALL_PROJECT_COMPLETION=NOT_DEFINED。

## 4. 進入正式實作的必要條件

本文件包須先完成 exact-SHA 的 fresh independent design review、來源/需求/契約/測試對照、乾淨取得與工具可行性檢查；所有 design-blocking finding 必須關閉。之後由 Human 一次確認實際設計/授權範圍及資源預算，或留下同等明確的有條件開工授權 receipt，Codex 才可啟動 GOAL_PLAN。不得把「同意規劃」或建立本分支自動當成未來所有安全/遷移/外傳操作的授權。

文件作者不能自我聲稱獨立設計驗收完成。Remote read-back 成功不等於 clean clone、Windows 實測、產品測試、live conformance 或 Human UAT。
