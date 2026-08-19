# PolyNexus SOP v1.1 Protected Areas

## 1. 絕對保護範圍

下列範圍不屬於本治理套件的修改目標：

1. 已完成的 FVS-01 product implementation、tests、fixtures、configuration、data model 與相關文件。
2. 已完成的 FVS-02 product implementation、tests、fixtures、configuration、data model 與相關文件。
3. `ADR-001`、`ADR-002`、`ADR-003`、`ADR-004`、`ADR-005`、`ADR-006`、`ADR-007`、`ADR-008`、`ADR-009`、`ADR-010` 的既有檔案與內容。
4. 任何未被當前 Task 明確授權的 product source、API、database schema、migration、dependency、lockfile、secret、CI/CD 或 deployment 設定。

由於建立本套件時沒有 PolyNexus checkout，實際 FVS 路徑與 ADR 路徑未能現場列舉；這一點是 `[待驗證]`，不能用本檔案取代目標 repo 的 diff 檢查。

## 2. 套件本身的保護證據

本 ZIP 僅包含：

- `docs/governance/sop-v1.1/**`
- `tools/validate-polynexus-governance.ps1`

本 ZIP 不包含：

- `src/**`、`app/**`、`packages/**`、`tests/**`、`test/**`、`migrations/**`
- 任何以 `FVS-01` 或 `FVS-02` 作為路徑名稱的檔案
- 任何以 `ADR-001` 至 `ADR-010` 作為路徑名稱的檔案
- lockfile、`.env`、credentials、CI/CD workflow 或 deployment config

文件內容提到受保護名稱，是為了形成治理規則與檢查提示，不代表套件攜帶或修改那些產品檔案。

## 3. 目標 repo 套用後的必要檢查

在目標 repo 執行：

```powershell
git diff --name-status
git diff -- . ':!docs/governance/sop-v1.1/**' ':!tools/validate-polynexus-governance.ps1'
Get-ChildItem -Recurse -File | Where-Object { $_.Name -match 'FVS-01|FVS-02|ADR-00[1-9]|ADR-010' } | Select-Object FullName
```

若第二個命令有輸出，必須逐一確認是否為套用前就存在的未提交變更；不能直接假定是本套件造成。若發現受保護檔案被修改，立即停在 `BLOCKED`，不要 Commit。
