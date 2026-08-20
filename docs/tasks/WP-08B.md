# WP-08B — ContextPackage UI Authoring / Selection

## Task status

- **TASK_ID**: `WP-08B`
- **ATTEMPT**: `2`
- **Status**: `ACCEPTED` — Attempt 2 implementation accepted after Codex PASS and Human approval
- **Human authorization**: Human requested the Antigravity development handoff on 2026-08-19
- **Human acceptance**: Confirmed on 2026-08-19
- **Item progress**: 100% — 2/2 points accepted
- **Project progress**: 24/100 = 24%; FVS progress 16/22 = 72.7%
- **Branch**: `feature/first-vertical-slice`
- **Writer**: Antigravity (sole active Writer; implementation complete)
- **Reviewer**: Codex
- **OpenCode**: not active for this task
- **Antigravity**: implementation Writer; Attempt 2 complete (61 tests PASS)

## Goal

Extend the existing React UI so a user can author a ContextPackage through the accepted WP-08A REST command, use the returned real ContextPackage ID for Run creation, or paste an existing ID manually.

## Accepted backend contract — do not change Core

Use the existing endpoint only:

```text
POST /api/v1/projects/{project_id}/context-packages
```

Request body:

```json
{
  "version": 1,
  "instructions": ["..."],
  "constraints": ["..."],
  "project_facts": {"key": "value"},
  "artifact_refs": ["..."],
  "prior_decision_refs": ["..."],
  "memory_refs": ["..."],
  "source_refs": ["..."]
}
```

Response is the direct `ContextPackageResponse` object, not a list wrapper:

```json
{
  "id": "context_...",
  "project_id": "project_...",
  "version": 1,
  "instructions": [],
  "constraints": [],
  "project_facts": {},
  "artifact_refs": [],
  "prior_decision_refs": [],
  "memory_refs": [],
  "source_refs": [],
  "created_at": "..."
}
```

There is intentionally no ContextPackage GET/list endpoint in WP-08A. Selection therefore means either:

1. retain/paste an existing ContextPackage ID; or
2. create a new package and select the exact `id` returned by the POST response.

Do not invent a GET/list endpoint or fabricate an ID.

## In scope

- Add `ContextPackage` and `ContextPackageCreateRequest` TypeScript types to `apps/web/src/api.ts`.
- Add `createContextPackage(config, projectId, body)` using the existing `request()` and `/api/v1` baseUrl convention.
- Preserve injected `getAuthHeaders`; do not add a token, secret, storage, or environment value to the UI.
- Extend `RunPreparation` with a minimal ContextPackage authoring form and existing-ID input.
- Pass the selected project ID from `App.tsx` to the Run Preparation flow as needed.
- On successful create, display the returned package ID/version and populate the Run ContextPackage ID input with that exact returned ID.
- Keep the existing Run creation flow and `CREATED / LOCAL / NONE` display unchanged.
- Keep props-based navigation and the current no-router design.
- Add focused Vitest/jsdom coverage for API request shape, create success, selection, errors, loading/submitting, and accessibility.

### Minimal authoring form

- `version`: required integer, minimum 1.
- `instructions`, `constraints`, `artifact_refs`, `prior_decision_refs`, `memory_refs`, `source_refs`: optional multiline fields; trim entries and omit blank lines.
- `project_facts`: optional `key=value` per line; reject malformed non-empty lines with a local form error rather than sending an ambiguous object.
- Preserve form values after 403/404/422; do not replace the selected ID on failure.

## Explicitly out of scope

- No changes under `services/core/`.
- No new REST endpoint, GET/list command, WebSocket, runtime, process, vendor, browser companion, or plugin logic.
- No changes to `POST /api/v1/tasks/{task_id}/runs` semantics.
- No changes to ADR-001–010, database schema, migration, dependency, lockfile, or Vite proxy.
- No `localStorage`, `sessionStorage`, cookie-based secret, hard-coded token, or production credential handling.
- No fabricated ContextPackage ID, evidence, finding, artifact, run result, or execution state.
- Do not relabel the deferred Browser E2E waiver as a full Browser E2E PASS.

## Required UI states and accessibility

- Create form open/close state.
- Version validation and disabled submit while invalid/submitting.
- Loading/submitting status with `role="status"` where appropriate.
- 403 Authentication required, 404 project/not-found, and 422 validation errors with `role="alert"`.
- Every input/textarea has a visible label, stable `id`, and relevant `aria-describedby`/`aria-required`.
- Existing manual ContextPackage ID path remains usable without authoring a new package.
- Successful create must show the returned ID and version; no client-generated replacement ID.

## Required tests

- API client posts to encoded `/projects/{project_id}/context-packages` and sends the exact manifest shape.
- Create success consumes the returned `id`, shows version, and uses that ID in subsequent Run creation.
- Empty/invalid version blocks or rejects form submission.
- 403, 404, and 422 create errors render accessible alerts and preserve entered values.
- Existing manual ContextPackage ID still creates a Run.
- Loading/submitting/disabled states and back navigation remain correct.
- Accessibility checks cover form labels, alert/status roles, and described fields.
- Existing frontend tests remain green; do not delete or weaken the 41 accepted WP-06 tests.

## Deterministic verification

Run from the repository root unless noted:

```powershell
cd apps/web
npm test
npm run build
cd ../..
git diff --check
```

Expected: all frontend tests pass, build exits 0, and `git diff --check` exits 0. If browser smoke verification is available, report browser/environment, route, journey, failure paths, and screenshot/video artifact references separately; do not claim full Browser E2E certification from Vitest alone.

## Acceptance handoff required from Antigravity

```yaml
RESULT: READY_FOR_CODEX_REVIEW | NEED_ACTION
TASK_ID: WP-08B
ATTEMPT: 2 (or current attempt number)
BRANCH: feature/first-vertical-slice
WRITER: Antigravity
REVIEWER: Codex
ANTIGRAVITY_STATUS: IMPLEMENTATION_COMPLETE | BLOCKED | PARTIAL
CHANGED_FILES: tracked and untracked files, explicitly listed
PROTECTED_AREAS: WP-08A Core contract, ADR-001–010, Run semantics, existing frontend behavior
TESTS: exact command, result, and exit code
ADR_IMPACT: NONE or concrete impact
SCOPE_DEVIATION: NONE or concrete deviation
KNOWN_LIMITATIONS: explicit
UNVERIFIED: explicit, including Browser E2E status (UNVERIFIED/SKIPPED under Human waiver)
NEXT_ACTION: CODEX_REVIEW or NEED_ACTION
FIX_PROMPT: required when NEED_ACTION
```

## Acceptance record

- Codex independent review: `PASS`; no BLOCKER, MAJOR, or MINOR findings.
- Deterministic evidence: 61 frontend tests passed, build passed, and `git diff --check` exited 0.
- Browser E2E remains `UNVERIFIED/SKIPPED` under the accepted Human waiver.

## Next step

Prepare WP-09A execution command API contract proposal and Human/Codex architecture gate. Do not implement execution API semantics before that gate is approved.
