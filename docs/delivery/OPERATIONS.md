# 環境、資源、安裝、備份與可攜交付

Status: OPERATION_DESIGN_DRAFT；操作命令與profile要在指定實機重現。此文件不是已執行的clean install、Windows/live conformance或新授權。

## 1. 環境指紋與Start Gate

記錄OS/architecture、Git、Python/venv、Node/npm、browser與automation runner、SQLite/Alembic、Runtime binary/protocol/model、lockfile hashes、專案root/working lane、ports與sanitized配置來源。不要列出所有環境變數、credentials或私人目錄內容。

Repo location由git rev-parse發現；跨機身份是canonical remote＋exact SHA，不是D槽路徑。讀取remote refs再fetch/check exact expected base；local origin cache不是remote truth。Working/staged/untracked/worktrees及原Agent ownership先確認，dirty原lane保留不動；新建隔離worktree/clone，不以reset/stash/clean解衝突。

前置清單：Python可執行、repo-declared依賴可安裝、前端package-lock可npm ci、指定browser可受控啟動、temp/evidence dir可寫、loopback端口無衝突、可用測試repo/DB隔離、real target已配置合法使用方式、runtime/profile版本與config來源可驗。缺少任一必需環境報ENVIRONMENT_BLOCKED，不重寫產品安全規則。

## 2. 輸入與工作區

提供小型synthetic bug repository、乾淨baseline、合成dirty/staged/untracked資料、預期patch與獨立test oracle、temporary SQLite新舊資料fixtures。產品內worktree/staging依SD/MCF建立；開發Codex的working repo與被產品操控的test repo不得混成同一個source root。

Project path/local URI只作locator；portable manifest用相對路徑與content reference。Output/DB/log/venv/browser profile不混入Git。所有cleanup只針對本批建立且ownership已安全釋放的temporary資源；不盲prune全部worktree/process。

## 3. Execution profile（開工時要有實值）

| Profile field | 規則 |
|---|---|
| max_active_coding_writers | 1，不可用並行工具繞過 |
| readonly_reviewer_slots | 按實機能力有限值；reviewer不可寫受審patch |
| provider/model/runtime allowlist | 指定已可用target與版本，禁止自行切昂貴方案/另開帳戶 |
| token/cost/quota envelope | 每批有限上限、來源/幣別/usage可見性；未知不可當0或無限 |
| wall-clock / inactivity bounds | 每Run與batch有限值；超時先安全checkpoint/cleanup，不盲重啟 |
| repair_limit | 同根因預設兩次bounded修復再升級root-cause review；總批次亦受資源上限，不無限模型互審 |
| network/destination / effect allowlist | 指定dev依賴下載與產品live測試目的地；secrets不寫profile |
| file/process/temporary storage limits | 有限數值按代表性fixture和host訂定；不把Golden示例L當產品檔案上限 |
| evidence retention/output root | 本機或批准artifact store，repo只存小型sanitized摘要/refs |

本文件不虛構使用者剩餘額度或可用API Key。具體profile可由前置環境盤點形成，付費/外传權限不足才集中請Human決策。已授權的正常消耗與小範圍修復不再逐次詢問。

## 4. 啟動與health

Start先確認schema head/integrity及auth配置，再起Core/UI；只綁核准loopback。Health分process alive、schema/DB、API/auth、UI client、artifact store、runtime readiness各層。HTTP200不等所有能力可用；端口衝突/缺schema/無runtime要可診斷。

UI pairing bootstrap與Human Accept enrollment分開；沒有Human-only principal不能因API已連線就允許Accept。UI重連用durable query，不重送launch副作用。Core shutdown先管理owned work，無法安全停止必須保留diagnostic/recovery facts。

## 5. Migration/Backup/Restore Runbook

1. 取得exclusive maintenance boundary並停止新write/launch；只操作核准測試DB或另授權real DB。
2. 記錄source schema、integrity/FK/relation audit、artifact closure和版本，建立consistent backup並核hash。
3. 在backup副本/temporary fixture演練Alembic upgrade，檢查原資料、immutable refs與legacy labels，測reopen和interrupted migration。
4. 說明可否lossless downgrade；不能則使用tested restore，不自動drop歷史。
5. Restore後驗schema/integrity、artifact hashes、accepted source/decision history、查詢和新工作能力，才宣告完成。

備份不包含普通export中的secret、session/challenge實值；必要security備援須另屬OS/security-store方案及Human明確權限，不混入P0/N1。資料異常先read-only audit，禁止自動删除dangling資料為了讓測試通過。

## 6. P0 Minimal Portable Accepted Package

P0屬B01必要成果。套件必須含足以重建/驗證exact accepted result的manifest、canonical profile/version、baseline/result source closure、ChangeSet/Candidate與Requirement/ValidationContract snapshots、選定publication/lineage provenance、必要EvidenceSet/Verification與acceptance record、artifact bytes/refs及hash、必要工具/環境說明和可執行verify/reconstruct步驟。

具體identity/closure完全採Frozen REV1 §19與Work W6，不另設一套hash演算法。光有manifest/外部Git指標而缺source不能算可攜。至少在另一乾淨目錄重建並對照source hash，離開provider private session也能完成驗證。刪一個blob、改bytes、惡意path/重複entry/錯contract必須拒絕。

P0公開/分享前先判定scope/classification；秘密、Human credentials、cookie/browser profile、供應商私有session不進包。含Human歷史的export僅提供來源事實，import不得自動建立本機已登入Human、批准新operation或信任未驗證principal。

## 7. N1/後續可攜

N1為selected-task history/context/continuation/full selected artifacts及namespace導入等完整可攜，依Frozen分階段於D4-NEXT交付，不阻B01。保留selected scope、來源、schema/contract、import collision/namespace與授權隔離；native session不可攜時標NONE/MANAGED，不假NATIVE。WebSocket亦為後續目標，REST durable first仍可完成B01。

## 8. 發佈與驗證資產

Repo存source/tests/design/sanitized receipts，小型execution ledger；大型JUnit/log/screenshots/ZIP放批准artifact位置並留下hash/index。不要為了跨機共享將browser auth/private logs推到public GitHub。

Clean install必須由所交付source/locks和手冊完成，不借Writer隱藏venv/global配置。最終安裝包/來源包/手冊/驗證報告記各自hash與對應Candidate，明確支援host/版本與限制，不由branch名推導production readiness。

本準備環境Git CLI DNS受阻，實際exit128；API取得/發布的commit可供後續clean clone，但本文件未替使用者電腦確認clone、driver或所有Agent已停止。

## 9. Assurance／human override 遙測的操作限制

PN-078 assessment的mode/profile/target引用及失效理由需可追溯，但不當新權限；詳[ASSURANCE_CONTRACT](ASSURANCE_CONTRACT.md#data-api)。PN-038的human override唯一含義是[§5](ASSURANCE_CONTRACT.md#metric)定義的人機建議分歧：合法audit事件單向消費、去重、coverage不足UNKNOWN。export/replay/重算指標不恢復Human session、不產生AcceptanceRecorded、不改变eligibility；AT-038-MN02與HU-12驗此邊界。
