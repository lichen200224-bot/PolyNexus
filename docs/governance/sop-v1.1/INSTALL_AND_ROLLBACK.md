# SOP v1.1 套用與回滾

## 1. 套用前檢查

在 PolyNexus repository 根目錄執行只讀檢查：

```powershell
git status --short --branch
git rev-parse --show-toplevel
Get-ChildItem -LiteralPath .\docs -Force
Get-ChildItem -Recurse -File | Where-Object { $_.Name -match 'FVS-01|FVS-02|ADR-00[1-9]|ADR-010' } | Select-Object FullName
```

若工作樹已有未提交變更，先保存或由 Human 確認；不要把既有變更與治理套件混在一起判讀。

檢查 ZIP 內容：

```powershell
tar.exe -tf .\PolyNexus_SOP_v1.1_Additive_Update.zip
```

確認所有路徑都在 manifest 列表中，且沒有 `src/`、`app/`、`packages/`、`tests/`、`migrations/`、FVS-01/FVS-02 實作檔或 ADR-001–010 檔案。

## 2. 建議套用方式

先把 ZIP 解壓到暫存資料夾，檢查後再複製到 repository 根目錄。不要直接以未知工具對整個 repository 執行遞迴覆蓋或刪除。

```powershell
$repoRoot = (git rev-parse --show-toplevel).Trim()
$staging = Join-Path $env:TEMP 'PolyNexus_SOP_v1.1_Additive_Update'
New-Item -ItemType Directory -Force -Path $staging | Out-Null
Expand-Archive -LiteralPath .\PolyNexus_SOP_v1.1_Additive_Update.zip -DestinationPath $staging -Force
Get-ChildItem -LiteralPath $staging -Recurse -File | Select-Object FullName,Length
```

完成人工比對後，只複製下列 package-owned paths：

```text
docs/governance/sop-v1.1/
tools/validate-polynexus-governance.ps1
```

若目標 repo 已有同名 `docs/governance/sop-v1.1/`，不要盲目覆蓋；先比較檔案版本、保留現有未提交變更，再由 Human 決定是否更新治理層。

## 3. 套用後驗證

```powershell
.\tools\validate-polynexus-governance.ps1
git diff --stat
git diff --name-status
```

驗收要點：

- validator 回傳 `PASS`。
- diff 只包含 manifest 列出的新增治理檔案。
- FVS-01/FVS-02 實作與 ADR-001–010 沒有 diff。
- 沒有 product source、lockfile、secret、CI/CD 或 deployment 設定被新增或改寫。

## 4. 回滾方式

本套件沒有刪除或重命名既有檔案。若套用後尚未產生其他變更，可由 Human 依 `manifest.json` 逐一移除 package-owned paths，並先確認每個檔案仍與套件 checksum 一致；若檔案已有後續修改，先保留並人工判斷，不要直接刪除。

不要使用下列廣泛命令回滾：

```text
git clean -fd
git reset --hard
```

若 package path 與既有治理檔案發生碰撞，回滾應由檔案級別的 diff 與版本控制操作完成，且不得影響 FVS-01、FVS-02 或 ADR-001–010。

## 5. 本次交付的驗證限制

建立本 ZIP 時沒有可讀取的 PolyNexus repository，因此以上是套用指引，不是對目標 repo 目前狀態的證明。目標 repo 的實際 protected-area diff 必須在套用後由 validator 與 Human 共同確認；任何未確認項目都應標記 `[待驗證]`。
