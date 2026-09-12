# Git / GitHub 整併與衝突處置

## 1. 本輪觀察基準

Canonical repository: lichen200224-bot/PolyNexus。2026-09-12 以 GitHub REST 讀取 refs、trees、commit/compare。原 default branch 為 feature/g24-g30-development-completion-routing；未變更。原 13 branches 的 SHA 保存在 SOURCE_LOCK.json。

本機 `git ls-remote --heads https://github.com/lichen200224-bot/PolyNexus.git` 實際 exit 128，原因為 DNS 無法解析 github.com；不能報成 Git CLI PASS。GitHub connector 的 remote reads/writes 可用，API 結果獨立記錄。沒有存取使用者電腦的工作樹，因此 local dirty/staged/untracked、尚存的 Agent process、clean-clone readiness 均未由本輪證明。

## 2. 已核對的關係

| Source | 相對 f0c0b986 的關係 | 處置 |
|---|---|---|
| feature/mcf-01-static-module-contract | product anchor 本身 | 本次文件 commit 的唯一 parent 起點；產品 bytes 保留 |
| feature/g30-wp20-live-vendor-closure | 同一 f0c0b986 | 保留原 alias，不刪 |
| codex/track-a-formalization@43aa27c8 | diverged；merge base f34e6b29；source ahead 6、behind 10 | 只匯入明確設計原件及接受來源，不能用整條分支覆蓋產品 |
| governance/current@1ea8ce3d | 與產品 diverged；共同祖先86d59390 | 移植治理語意，重建 current routing；不採用過期95/100/IMPLEMENTING |
| feature/mcf-02-opencode-acp-runtime@030890b3 | ahead 4、behind 0；祖先為 f0c0b986 | candidate-only；需獨立審查後才可作產品整合 |
| codex/ta-lr-01@fe2eb231 | 已觀察為以 docs/AGENTS/skills 為主的來源樹 | 非產品完整樹；絕不直接拿來替代產品 checkout |
| 其餘 architecture/tooling/history 分支 | ref 已盤點；未逐一驗收所有內容 | SOURCE_REFERENCE_ONLY，不宣稱無 merge conflict，也不任意清理 |

## 3. 選擇的安全整併方法

在 f0c0b986 的既有 tree 上建立 planning/full-delivery-design-consolidation。只改根 AGENTS、增加 DELIVERY_START_HERE 及 docs/delivery/**。來源原件以 exact blob pin 保存。新 commit 只有 product anchor 一個 parent，不假造其他分支已被 merge 或已接受。後續要整合產品時，使用已審查的明確候選及 integration receipt，不以本次文件 commit 充當產品 merge。

保持 services/**、apps/**、extensions/**、workflows/**、schemas/**、scripts/**、tools/**、dependencies、既有 tests/migrations 與版號不變。以 top-level tree SHA 及 changed-path allowlist 驗證。文件驗證不需要把全部產品 tests 重跑一遍；但是不因此稱產品 regression PASS。

## 4. ADR 與狀態衝突的處理

歷史 ADR-013 有兩份：`docs/34_ADR_013_MODULAR_CORE_EXTENSION_ARCHITECTURE.md` 與 Track A `docs/34_ADR_013_WORK_GENERATION_CANDIDATE_AND_ACCEPTANCE.md`。本包使用 ADR-MOD-013 / ADR-ID-013 語意別名，SOURCE_INDEX 記 exact path/SHA。這是消歧，並非刪除、重新編號、升版或修改 frozen semantics。ADR-014 lifecycle 與 D11-A-LP 各有獨立 authority。

舊 SA/SD 的 RuntimeBinding NOT_IMPLEMENTED、舊 current routing 的95/100、MCF02 NOT_STARTED 屬其來源 checkpoint 的歷史敘述；本包分開記 design authority、observed implementation、acceptance state。不得把舊文件整份覆蓋新狀態，也不得直接把所有 NOT_IMPLEMENTED 改成 PASS。

## 5. 之後的開發接續

開工 receipt 鎖定 documentation candidate、selected product base、reviewed existing candidate 與允許的 task/integration refs。從該組合產生唯一 reviewed integration checkpoint，才派正式 Writer。MCF-02 與 Track A 同時涉及 execution_service/registry/identity 的部分，須在隔離整合 lane 做 semantic diff；不得因 Git 無 textual conflict 就判為契約相容。

普通工作採一條 integration chain、single Writer、immutable review snapshots。必要子分支可用，但每輪都以記錄的 base SHA/reviewed SHA 整合。改動已凍結候選後要新 SHA 與受影響重驗；不能保留舊 PASS 貼在新 tree 上。

新 develop/main、default branch 變更、rulesets/branch protection、merge strategy 平台強制不在本次文件發布內執行。若後續採用，另提供精確設定變更及 fallback；現時不宣稱 GitHub 已強制獨立審查。

## 6. 實機接續與回退

在使用者電腦讀取 remote exact ref 後，先查 `git status --short --branch`、`git diff --cached --name-status`、`git worktree list --porcelain`。dirty lane 不 checkout/reset/stash/clean；新建隔離 worktree，不能假設原 Agent 已停。無法確認 ownership 就禁止派新 Writer。

本包如被拒絕，保留 branch/commit 並停止採用即可；不需回退產品碼。已推送文件修正以新增 commit 處理，不改寫受審歷史。使用者既有分支與檔案未由本次操作删除，不能宣稱所有可能衝突已永久消除。
