# FIX PROMPT Template

```text
你是 {{TARGET_TOOL}}，負責修正 PolyNexus Task {{TASK_ID}}。

目前狀態: {{STATE}}
Attempt: {{ATTEMPT}}
Reviewer: Codex

## Failed issues

{{ISSUES_WITH_EVIDENCE}}

## Allowed scope

{{ALLOWED_SCOPE}}

## Protected scope - MUST NOT TOUCH

- 已完成的 FVS-01 產品實作與相關檔案
- 已完成的 FVS-02 產品實作與相關檔案
- ADR-001 至 ADR-010
- 未在 Allowed scope 中列出的檔案

## Required fix

{{REQUIRED_FIX}}

## Acceptance after fix

{{ACCEPTANCE_AFTER_FIX}}

## Required verification

{{VERIFICATION_COMMANDS_AND_EVIDENCE}}

若遇到需求衝突、缺少來源、權限不足或需要超出 Allowed scope 的架構變更，請停止並回覆 `BLOCKED` 或 `NEED_ACTION`，不要自行擴大修改。

完成後必須提供：
- modified files
- fix summary
- tests and exit codes
- evidence
- known issues
- scope deviation
- protected-area check
- RESULT: READY_FOR_REVERIFICATION 或 BLOCKED / NEED_ACTION
- NEXT_ACTION: CODEX_REVERIFICATION 或 BLOCKED / NEED_ACTION
- NEXT_PROMPT_FOR_CODEX_REVERIFICATION：完整可直接複製的回驗提示詞
```
