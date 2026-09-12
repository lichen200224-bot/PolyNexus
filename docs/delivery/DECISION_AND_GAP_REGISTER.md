# 決策、差異與開工 Gate

本表區分已由來源決定的語意、此次文件整理決定、尚需證據的實作/環境 Gate。不把缺測項改成 optional。

| ID | 問題與來源 | 本包處置 | 關閉條件/owner |
|---|---|---|---|
| D01 | 初版與新版分散分支 | 全範圍繼承，B01只是內部 milestone；REQUIREMENTS對應S0/W1-W6及原WP | Fresh Reviewer核對來源無漏項 |
| D02 | ADR-013重號 | 用ADR-MOD-013/ADR-ID-013別名＋exact來源；原件不改 | SOURCE_INDEX唯一解析，無裸ADR-013新增引用 |
| D03 | stale current routing | 此branch的START_HERE唯一入口；舊state/handoff保留source歷史 | 新agent只按本輪task/receipt路由 |
| D04 | candidate與acceptance混淆 | 030890b3列既有待審候選，不直接匯入product | 獨立實作審查及exact integration evidence |
| D05 | CandidateID與generation關係 | 依Frozen REV1：內容ID不包含generation/Run；publication保存exact lineage，重複內容不合併履歷 | SD/DATA_AND_API映射及Golden tests，不發明新canonicalizer |
| D06 | applicability用詞摘要不一致 | 以REV1 requirement、applicability、outcome、validity四軸為權威；N/A顯示需trusted predicate | API/UX/verification同一映射，required不被弱化 |
| D07 | 開發授權與產品Human信任 | 兩個控制面完全分開；批次開發不供給A-LP憑證，不替產品Accept | SECURITY負向案例與execution receipt |
| D08 | RuntimeBinding舊未實作文字 | 原件保留；產品錨點已有0002/0003與binding相關source；不代表所有使用情境通過 | 實機baseline/affected regression與schema實查 |
| D09 | Track A S0與已修BASELINE-DEBT重疊 | 重用已接受ordering/cleanup；另驗FK、CREATED restart、auth/health，不整包重做 | S0 evidence逐項對照，失敗只修差額 |
| D10 | MCF deny-all不等於可真實改碼 | 原candidate的限制保留；live可行性/受控write與config支援單獨Gate | 版本固定、真實cwd/change/cancel/cleanup證據；不得直接關閉permission gate |
| D11 | Native工作副本與external staging差異 | Core managed worktree管理generation；external adapter只取得projected staging；Core驗證import後形成result snapshot | containment、ownership、drift、quiescence正負案例 |
| D12 | Git/default分支與保護未整合 | 只建立文件lane，不改default/protection，不假稱已強制review | 後續integration receipt與實際平台設定或procedural fallback |
| G01 | 獨立設計審查 | NOT_RUN；本作者不可自我獨立驗收 | Fresh AI Reviewer exact-SHA報告、無BLOCKER/MAJOR |
| G02 | clean clone與實機能力 | NOT_RUN；本環境git DNS exit128；API readback不替代 | Codex開工前隔離取得、branch/HEAD/source/test-tool檢核 |
| G03 | 完整逐原子需求/source覆蓋 | 本包需求清單與繼承原件共同構成規格，不能只按列表數量算完整率 | Reviewer逐原件條款覆蓋與例外清單；必做項不可遺漏 |
| G04 | 真實target/API/配額/帳號 | 不在Git保存值；可行性於環境 Gate驗證 | 事先配置可用target與有限預算，Human-only動作列操作清單 |
| G05 | 正式開工 | HOLD；無自動解鎖 | 設計接受與exact bounded execution authorization成立 |

### Change control

本包新增的SQL表名、HTTP路由/DTO、UI呈現、操作參數是依凍結語意提出的實作設計草稿，不是假稱已存在的API，也不擅改Golden身份。Frozen invariant或public RuntimeAdapter/RuntimeBindingSnapshot語意需要改動時，須提出impact與Human決議；正常内部實作選擇可在已接受設計與批次授權內自行決定。

設計審查發現一般文字/映射/缺測問題，回前置文件Writer修正並重新發布，無需讓Human逐條再次批准已同意的產品需求。若涉及實質範圍/信任變更，才集中提交例外決策。
