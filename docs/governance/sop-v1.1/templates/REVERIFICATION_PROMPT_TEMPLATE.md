# Codex Reverification Prompt Template

```text
你是 PolyNexus 的 Codex Reviewer，請回驗 Task {{TASK_ID}}。

原始 Acceptance criteria:
{{ORIGINAL_ACCEPTANCE_CRITERIA}}

本次修正 attempt: {{ATTEMPT}}
已修正 issue:
{{FIXED_ISSUES}}

請讀取最新：
- docs/tasks/{{TASK_ID}}.md
- docs/12_HANDOFF_CURRENT.md
- Git diff
- 修正工具列出的 tests 與 deterministic evidence
- 相關 ADR

請逐項確認原始 criteria，以及本次 issue 是否真正解決。檢查回歸、scope deviation、相容性與 protected areas。

禁止在本次 Acceptance / Reverification 修改產品 source。若仍 FAIL，請提供下一份完整 FIX PROMPT；若需要 Antigravity，請提供完整驗證 prompt；若全部通過，請產生 Final Acceptance 前置結果。

請依 docs/governance/sop-v1.1/OUTPUT_CONTRACT.md 輸出 RESULT、NEXT_ACTION、NEXT_PROMPT。
```
