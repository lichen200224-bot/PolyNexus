# PolyNexus 整合產品需求規格

Status: DRAFT_FOR_INDEPENDENT_DESIGN_REVIEW。這是初版＋最後擴充的整合交付視圖，不升產品版本，不宣稱功能已實作。原功能明細由 BASE、FORMAL、FROZEN、WORK、ADR-MOD-013 繼承，代號見 SOURCE_INDEX。

## 1. 產品與範圍

Local-first Multi-AI Collaboration & Validation Workspace。服務個人Developer/Technical Lead、QA/Reviewer、PM與一般文件使用者。第一交付閉環B01針對真實Simple Python Bug Fix及failure→retry/recovery；完整交付仍保留Discuss/Review/Validate、Council、九範本、Web AI、Local AI、兩個深度Runtime、可替換模組與日用維護能力。

Develop是workflow action/role，不新增第四個頂層入口。第一版不變成第三方Agent的薄啟動器：Core持有任務/工作/內容/驗證/接受/接續事實，外部session不是唯一System of Record。

CORE/BASELINE/COMPATIBILITY依初版來源分級。Dynamic marketplace、remote install/update/signing/hot reload、visual workflow designer、distributed scheduler、multi-user/Enterprise IAM、full RAG/knowledge graph、fully autonomous product team不因本次開發AI化而自動加入。MCF僅static/bounded expansion；待批准target保持候選狀態，不偷宣稱支援。

## 2. 使用者可觀察成果

| Journey | 使用者目的 | 完成與失敗行為 |
|---|---|---|
| UJ-01 Discuss/Council | 比較多AI觀點並作決定 | 2–4角色獨立輸入/輸出、Cross Review、共識/分歧/風險/缺資料可追溯；角色失敗明示partial，不虛構投票 |
| UJ-02 Review | 審查程式/文件/需求/SOP | Findings有來源位置、severity、理由、建議；AI Opinion清楚標示，並可進入Validate |
| UJ-03 Validate | 確認exact成果是否符合要求 | 對exact Candidate與validation contract執行可信工具；required失敗/缺漏/stale阻擋，不能由AI投票改PASS |
| UJ-04 Web Decision | 使用ChatGPT/Claude/Gemini Web協作 | launch/fill、人類明確send、capture/association/normalize；失敗改clipboard/manual/launch fallback，不壓垮Core |
| UJ-05 Local-only/Mixed | 控制資料去向 | highest classification與mode決定每步目的地；同一核准流程可串本地及允許外部步驟，Local-only不silent fallback |
| UJ-06 Work generation | 將需求轉成真實修改 | 明選repo baseline/inputs/scope/AC→generation→Run→安全worktree→真實executor→變更；使用者原dirty不受影響 |
| UJ-07 Recover/Retry | 中斷後安全接續 | 顯示identity/Git/ownership/recoverability四軸；未確定清理前不派新writer；Retry新generation，late Abort不影響新輪 |
| UJ-08 Accept/Open | 接受並使用可信成果 | exact view與mandatory evidence符合後Human Accept；可開accepted managed worktree；新編輯顯示Working Copy，不篡改已接受歷史 |
| UJ-09 Portable | 不靠供應商私有session帶走成果 | B01必備P0 accepted package，可verify並重建source；N1完整selected-task portability於後續批次，不阻擋B01 |
| UJ-10 Maintain | 長期使用與更新 | 分層health/Doctor、資源/usage、schema migration、backup/restore、乾淨安裝與可理解的錯誤處理 |

## 3. 需求與優先順序

REQUIREMENTS.md是核銷索引，不取代原件完整條款。P0先完成S0穩定性、工作區/lineage、可行executor、Candidate/verification/Human/accepted source/P0package。之後補齊完整初版及確認擴充的其餘能力。不得用B01 PASS替代全功能完成，也不得因N1不阻擋B01就從後续計畫移除。

原定九範本：Code Review、Release Validation、Bug/Incident Analysis、Technical Design Review、Requirement Review、Change Impact Review、Document Review、SOP Review、Decision/Proposal Comparison。四條Golden flows深驗，其餘範本也須真實可運作及符合schema，不能只存在YAML。

## 4. 產品規則

1. Requirement、input/context、validation contract在generation開始時固定；變更需求/新writer retry建立新generation，不改舊ref。
2. Run完成、Candidate發布、technical verified與Human accepted分開呈現。工具exit0只是證據之一，不能取代oracle或scope檢查。
3. Candidate內容身份由Core依REV1從verified baseline/result snapshots推導。新增evidence不改CandidateID；改source或requirements/validation agreement要新Candidate。
4. Human只能接受符合當下mandatory policy的exact view；沒有Override Accept。Accept不自動Git commit/merge/push/apply/release。
5. Reject僅pre-acceptance；accepted後Revoke/Supersede追加事件；保留當時accepted事實。後續policy drift顯示失效，不偽造Human撤銷。
6. 原Human dirty預設不帶入；明選dirty snapshot才成input。Managed worktree是隔離工作區，非惡意程式sandbox。
7. Credential、execution permission、data-routing policy分開；Local process不等於本地資料不外流。
8. 模組可替換，不可重定義Task/Run/Binding/Evidence/Human authority。Capability宣告與conformance證據分開。

## 5. 非功能完成條件

資料正確性：所有關鍵relation、sequence、CAS/idempotency、immutable references有正負測試；restart不重複launch，legacy不捏造可信provenance。
安全：秘密掃描、來源包含/路徑逃逸、Human/Agent隔離、anti-replay、CSRF/Origin、egress、篡改測試列required。
可操作性：正常流程不用讀log才知道下一步；network/permission/timeout/partial結果有安全動作，UI重連後從durable facts恢復。
效能與成本：有限max rounds/timeout/concurrency/budget；量測啟動、操作latency與資源占用，門檻由OPERATIONS profile記錄。未知usage顯示UNKNOWN，不能當0或估算成真實帳單。
可攜與維護：可乾淨取得/安裝/驗證、可備份還原、P0 source可重建；本機路徑不作產品identity。

## 6. 驗收邊界

完整交付的AI終点為READY_FOR_HUMAN_UAT：本輪required需求對應有效證據、沒有未解BLOCKER/MAJOR、套件與被驗source一致、操作手冊經演練。Human最終檢核用途/操作/成果接受；AI不產生Human Accept。

必要live帳號/明確send保留真實操作邊界，可集中於預先安排的操作清單，但不得以fixture冒充。不能把未完required功能藏成known limitation。原2026-10-18/10-31為來源時程，未重新完成估算前不承諾新的日期。
