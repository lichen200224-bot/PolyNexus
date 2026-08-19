# PolyNexus SOP v1.1 治理層

這是一個可直接放入 PolyNexus repository 的 additive update package。它新增治理文件、狀態機、提示詞、模板、automation schema，以及一個只讀驗證工具；不包含任何產品實作程式碼。

## 這個套件解決的問題

SOP v1.1 將工作流程固定成可追蹤的閉環：

```text
Writer 完成
  -> Codex 獨立驗收
  -> FAIL / NEED_ACTION 時產生可直接執行的 FIX PROMPT
  -> 指定工具修正
  -> 修正工具回報 RESULT + NEXT ACTION + NEXT PROMPT
  -> Codex 回驗
  -> 必要時 Antigravity 驗證並同樣閉環
  -> Codex Final Acceptance Report
  -> HUMAN_APPROVAL_REQUIRED
  -> 人工明確同意後才可 Commit
```

所有 OpenCode、Codex、Antigravity 的完成回覆都必須包含：

```text
RESULT
NEXT_ACTION
NEXT_PROMPT
```

## 目錄

- `POLYNEXUS_SOP_v1.1.md`：正式規範、角色、Gate、禁止事項與完成條件。
- `STATE_MACHINE.md`：狀態、轉移、owner 與 automation 事件契約。
- `OUTPUT_CONTRACT.md`：所有工具共同遵守的輸出介面。
- `PROMPT_LIBRARY.md`：OpenCode、Codex、Antigravity 與人工確認可直接複製的提示詞。
- `templates/`：Task handoff、Acceptance、修正、回驗與人工 approval 模板。
- `schemas/`：可供後續自動化使用的 JSON Schema 與轉移定義。
- `PROTECTED_AREAS.md`：不可由此套件修改的產品與 ADR 保護範圍。
- `INSTALL_AND_ROLLBACK.md`：安全套用、碰撞檢查與回滾說明。
- `manifest.json` / `manifest.md`：套件檔案清單、動作與保護聲明。

## 套用前提

本次建立時的工作目錄沒有 PolyNexus checkout：只有空的 `work/` 與 `outputs/`，且不在 Git repository 內。因此：

- 套件路徑依 PolyNexus 慣例採 repository-relative `docs/` 與 `tools/`。
- `updated_files` 為空；本 ZIP 的所有檔案都是新增檔案。
- 目標 repository 的實際檔案是否與保護清單一致，必須在目標 repo 中執行驗證；此狀態已在 manifest 明確標記為未現場確認。
- 不得因套件中提到 FVS-01、FVS-02 或 ADR-001–010，就把既有產品檔案複製、重建或替換。

## 最小使用方式

1. 在 PolyNexus repository 根目錄檢查 `git status --short`，保留既有未提交變更。
2. 先檢查 ZIP 內容與 `manifest.json`，確認沒有路徑碰撞或超出本套件範圍的檔案。
3. 將 ZIP 內容解壓到 repository 根目錄；只會新增本套件列出的 `docs/governance/sop-v1.1/` 與 `tools/validate-polynexus-governance.ps1`。
4. 執行 `tools/validate-polynexus-governance.ps1`。
5. 由人工查看 `git diff --stat` 與 `git diff --name-status`，確認 FVS-01/FVS-02 與 ADR-001–010 沒有變更。

完整步驟與回滾方式請見 `INSTALL_AND_ROLLBACK.md`。
