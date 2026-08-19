# Human Approval Gate Template

```text
Codex Final Acceptance 已完成。

TASK_ID: {{TASK_ID}}
FINAL_ACCEPTANCE_REPORT: {{REPORT_PATH_OR_REFERENCE}}
COMMIT_SCOPE:
{{COMMIT_SCOPE}}

必要 Gate:
{{GATE_RESULTS}}

受保護範圍檢查:
- FVS-01: {{STATUS}}
- FVS-02: {{STATUS}}
- ADR-001 至 ADR-010: {{STATUS}}

未驗證項目／殘餘風險:
{{UNVERIFIED_ITEMS_AND_RISKS}}

目前狀態: HUMAN_APPROVAL_REQUIRED

若你同意指定 scope 的 Commit，請只回覆：

APPROVED_FOR_COMMIT
TASK_ID={{TASK_ID}}
COMMIT_SCOPE={{COMMIT_SCOPE}}
EXCEPTIONS={{NONE_OR_EXPLICIT_EXCEPTIONS}}

未收到上述明確回覆前，不得 Commit、Push、建立 PR 或修改其他 Task。
```
