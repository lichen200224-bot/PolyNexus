# PolyNexus SOP v1.1 Additive Update Manifest

## Package identity

- Package: `PolyNexus_SOP_v1.1_Additive_Update`
- Version: `1.1.0`
- Created: `2026-08-18`
- Mode: `additive`
- Repository-relative paths: yes
- Existing product checkout available during build: no

## File action policy

`manifest.json` 的 `files` 陣列列出本 ZIP 中的每一個檔案；本次 `updated_files` 為空。套用時的預期動作只有 `add`：

- `docs/governance/sop-v1.1/**`
- `tools/validate-polynexus-governance.ps1`

若目標 repo 已有同名檔案，應先做檔案級比對並由 Human 決定，不得把碰撞當成可自動覆蓋的許可。

## Protected areas

下列範圍明確未被本套件攜帶或修改：

- FVS-01 completed product implementation and related files
- FVS-02 completed product implementation and related files
- ADR-001 through ADR-010
- 未被 Task 授權的 product source、tests、migrations、lockfiles、secrets、CI/CD、deployment 設定

## Verification status

- Package file list: 已由建立流程檢查。
- ZIP layout: 已驗證，20 個檔案均為 repository-relative paths，且沒有 package wrapper 目錄。
- Target repo protected-area diff: `[待驗證]`，因建立時沒有 PolyNexus checkout。
- Product behavior: `[待驗證]`；本次沒有產品 source 可執行或測試。

## Rollback

套件沒有刪除或重命名既有檔案。回滾只可針對 manifest 列出的 package-owned paths，且必須先確認沒有後續人工修改；詳見 `INSTALL_AND_ROLLBACK.md`。
