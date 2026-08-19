# Task Handoff Template

```markdown
# {{TASK_ID}} - {{TASK_TITLE}}

## Task metadata

- Status: `TASK_CREATED`
- Owner / Writer: `OpenCode`
- Reviewer: `Codex`
- Optional verifier: `Antigravity`
- Created at: `{{CREATED_AT}}`
- Base commit: `{{BASE_COMMIT}}`

## Goal

{{TASK_GOAL}}

## Non-goals

{{NON_GOALS}}

## Acceptance criteria

1. {{ACCEPTANCE_CRITERION_1}}
2. {{ACCEPTANCE_CRITERION_2}}

## Allowed scope

{{ALLOWED_SCOPE}}

## Protected scope

- FVS-01 completed product implementation and related files.
- FVS-02 completed product implementation and related files.
- ADR-001 through ADR-010.
- Any file not explicitly included in Allowed scope.

## Required evidence

{{REQUIRED_EVIDENCE}}

## Required commands

```text
{{TEST_COMMANDS}}
```
## Handoff rule

OpenCode 完成後必須提供完整 `NEXT_PROMPT_FOR_CODEX`，並回覆 `RESULT: READY_FOR_CODEX_ACCEPTANCE`。不能直接要求 Human Commit。
```
