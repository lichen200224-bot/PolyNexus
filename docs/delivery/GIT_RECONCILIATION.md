# Git / GitHub 整併、保全與接續

Task: PREP-FULL-DELIVERY-01
Active preparation: planning/full-delivery-design-consolidation
Canonical repository: lichen200224-bot/PolyNexus
Product base: f0c0b986380dc21d103d4e856057cb8ac435a8f9

## 1. 整併範圍

Human授權本次文件/Git前置工作並要求單一接續線。採curated documentation integration：以f0產品tree為基礎，保存Track A正式/凍結、模組/MCF、跨機治理原件，集中PRD/SA/SD/功能scope/測試/批次/UAT文件。這不是未審程式的自動接受，也不以偽merge parents宣稱所有分支已合併。

寫入allowlist：AGENTS.md、DELIVERY_START_HERE.md、docs/37_CURRENT_ROUTING_INDEX.md、docs/delivery/**。其中docs/delivery/checks是前置文件結構檢查helper，不是產品runtime/code變更。原services/apps/extensions/workflows/schemas/scripts/tools及既有tests/migrations/dependencies保持不變。

舊docs/11/12/ADR/正式文件保留原bytes與歷史；當前routing由AGENTS＋docs/37＋delivery/START_HERE給出。來源文件內舊NEXT_GOAL不自行活化。原分支保留追溯，不作多個active Writer。原default/protection未在本次變更，不宣稱平台已強制停用舊Agent。

## 2. 分支及parent關係

完整原refs與SHA见SOURCE_LOCK，全分支逐項處置见BRANCH_DISPOSITION。已檢查：Track A正式線與f0 diverged，merge-base f34e6b29；GOV與產品線diverged，merge-base 86d59390；MCF修復030890b3在f0之後ahead 4/behind 0但仍未接受。

準備分支從f0建立。先前成功保存的未掛branch tree已由aa7a2e398d2116c071b50ced52178756bcf9ae86恢復為SYNC_CHECKPOINT；之後功能scope與source補強用新增子commit接續。新發布SHA在外部receipt回讀，不寫自引用『本commit已push』。

每次ref update皆force=false；父SHA取當前已核對的planning tip。若remote非預期即停止寫入，不能用force把其他人的進度蓋掉。已review candidate不amend/rebase，fix新增commit。

## 3. 語意衝突處置

兩份ADR-013分別用ADR-MOD-013和ADR-ID-013別名＋path/SHA解析；不更動原決議/Golden、不自行升版。舊RuntimeBinding未實作文字保留為source歷史；新entry分開actual source、bounded acceptance與待實作scope。

MCF-02 proposal仍有NOT_STARTED文字，但030890候選已實作；new routing將它列candidate pending independent review。不得把兩種狀態拼成已接受，也不得重新從頭寫掉候選。將來要採用必須exact review＋與generation/lineage/ownership的新契約做semantic integration test；Git textual merge成功不代表接口正確。

四類資料分開：已接受產品source、已接受設計source、本次設計候選、未接受產品候選。Source完整匯入同一文件checkout，不提升其maturity。其他歷史tooling/source refs只在需要時按exact scope重用，不整repo覆蓋。

## 4. 前置檢查與驗證限制

本輪本地Git CLI `git ls-remote --heads https://github.com/lichen200224-bot/PolyNexus.git`實際exit128，DNS無法解析github.com。GitHub connector可讀寫，屬API證據，不偽造成CLI push成功或clean clone完成。

本地已執行FEATURE_SCOPE_MATRIX結構檢查、檢查器正例與四個強制失敗變體；GitHub接受的matrix/validator/selftest blobs與本地byte hash一致。詳見PREPARATION_VALIDATION。這是作者結構自檢，不等whole-repo tests、Windows/live conformance或independent semantic review。

發布後須回讀branch exact SHA、commit parent/tree、changed paths及protected root tree IDs；在PR receipt列實際結果。未執行的clean clone、原子source完整性、全部歷史reference closure仍明示待review，不能靠推送成功轉PASS。

## 5. Codex接續與衝突防止

正式開工先鎖定reviewed docs commit、selected product/integration SHA、既有MCF處置、roles/allowlist/有限resources與target權限。新電腦不能只clone舊default後就猜是當前設計；明確使用本planning branch與receipt。

實機先查repo root、remote、HEAD、staged/unstaged/untracked、worktree list及Agent ownership。原Human dirty lane不checkout/reset/clean/stash；新建隔離工作區。lease/CLEAN/PID不單獨代表安全，owner未知就不派新Writer。

一個active Writer依功能包順序處理shared execution_service、registry、schema與UI shell。Migration從實際head線性新增、測restore；不預占相同revision。每個interface改動有impact与消費者回歸，不用整檔覆蓋或跳過previous contract。

## 6. 回退與最終邊界

若文件候選未被接受，保留branch/commit並停止採用；產品未改，不需rollback user code。修訂用新commit。舊branches、default、accepted source、不可變歷史皆保留，未擅刪。

本次完成的是單一文件接續線與待審前置候選，不是宣稱所有程式分支已merge、所有潛在衝突永久不存在或正式release。最終產品接續仍須獨立設計審查與實機Start Gate。
