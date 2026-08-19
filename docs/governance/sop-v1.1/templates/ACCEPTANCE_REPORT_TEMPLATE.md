# Codex Acceptance Report Template

```markdown
# Codex Acceptance Report - {{TASK_ID}}

- Result: `{{PASS_FAIL_OR_NEED_ACTION}}`
- State: `{{STATE}}`
- Attempt: `{{ATTEMPT}}`
- Base commit: `{{BASE_COMMIT}}`
- Reviewed at: `{{REVIEWED_AT}}`

## Sources read

- `docs/tasks/{{TASK_ID}}.md`
- `docs/12_HANDOFF_CURRENT.md`
- Git diff: `{{DIFF_REFERENCE}}`
- Evidence: `{{EVIDENCE_REFERENCES}}`
- ADR: `{{ADR_REFERENCES_OR_NONE}}`

## Acceptance criteria

| ID | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| AC-01 | {{CRITERION}} | PASS / FAIL / NEED_ACTION | {{EVIDENCE}} |

## Protected-area check

- FVS-01: `{{NOT_TOUCHED_OR_ISSUE}}`
- FVS-02: `{{NOT_TOUCHED_OR_ISSUE}}`
- ADR-001 to ADR-010: `{{NOT_TOUCHED_OR_ISSUE}}`

## Issues

{{ISSUES_OR_NONE}}

## Unverified items and residual risks

{{UNVERIFIED_ITEMS}}

## Next action

`{{NEXT_ACTION}}`

## Next prompt

```text
{{NEXT_PROMPT}}
```
```
