# First Vertical Slice — Execution Plan

Target: 2026-09-06
Branch: `feature/first-vertical-slice`

## Objective

Create the first real PolyNexus product path without using vendor Web AI or multiple production Runtime integrations.

```text
Project
  -> Review Task
  -> ContextPackage v1
  -> WorkflowDefinition
  -> Reference/Mock RuntimeAdapter
  -> Run Supervisor
  -> Finding + Evidence
  -> Run Result
  -> Persist
  -> Reload History
```

## Work Packages

### WP-01 Domain & IDs — Codex
Project, Task, Run, Actor, Finding, Evidence, Artifact metadata, ContextPackage, RunEvent. Stable IDs and enums.

### WP-02 Repository & Migration — OpenCode
SQLite repositories, SQLAlchemy mappings, initial Alembic migration, temporary test DB fixtures.

### WP-03 Workflow Loader — Codex/OpenCode
Load `workflows/builtin/review-minimal.yaml`, validate against `schemas/workflow.schema.json`, normalize nodes.

### WP-04 Run Supervisor Reference Runtime — Codex
Reference adapter only. Prove lifecycle/status/result/cancel interface without depending on Codex/OpenCode upstream behavior yet.

### WP-05 API — OpenCode
Minimal `/api/v1` project/task/run endpoints and `/health`.

### WP-06 UI — OpenCode
Project list/create, Review action, status/result page. Keep minimal and progressive.

### WP-07 Integration Acceptance — Codex Review + deterministic tests
Fresh DB → run slice → reload result/evidence → actual exit 0.

Antigravity is not mandatory for WP-01～06; reserve it for milestone UI/E2E if browser interaction is valuable.

## Checklist

- [ ] `git status` clean before start.
- [ ] Branch `feature/first-vertical-slice`.
- [ ] Core scaffold tests PASS.
- [ ] Project persistence PASS.
- [ ] Task/Run persistence PASS.
- [ ] Context version persisted.
- [ ] Workflow schema rejects invalid node.
- [ ] AI_OPINION and TOOL_EVIDENCE are distinct types.
- [ ] Reference runtime lifecycle normalized.
- [ ] Cancel path has a test, even if reference runtime is simple.
- [ ] Result can be reloaded after process restart/new DB session.
- [ ] No secret/raw credential in DB or fixture.
- [ ] Update HANDOFF with actual commands/exit codes.

## Not Allowed in This Slice

- ChatGPT/Claude/Gemini DOM work.
- Local model endpoint scale-out.
- 9 workflow templates.
- Dynamic plugins.
- Visual workflow designer.
- Autonomous agent loops.
- Enterprise features.

These begin only after the slice gate is green.
