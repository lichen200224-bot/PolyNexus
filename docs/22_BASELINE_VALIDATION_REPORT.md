# Development Baseline v1.0 — Validation Report

Date: 2026-08-17
Result: PASS WITH EXPLICIT SKIPS

This report validates the generated repository scaffold only. It is not a PolyNexus V1 product acceptance report.

## Executed

### Baseline structure / schema
Command:
`python scripts/validate_baseline.py`

Result:
`Baseline validation PASS: 11 required files; workflows valid; MV3 manifest valid`

Exit code: 0

### Core unit/smoke tests
Command:
`cd services/core && python -m pytest`

Result:
`7 passed`

Exit code: 0

Covered baseline assertions:
- `/api/v1/health` responds successfully.
- Development baseline identity is exposed.
- Normal Run lifecycle transitions are accepted.
- Terminal state does not transition back to running.
- Cancel requires the normalized CANCEL_REQUESTED path.
- AI_OPINION and TOOL_EVIDENCE are distinct types.
- Valid built-in workflow YAML passes schema validation.
- Invalid arbitrary-script workflow node is rejected.

### Browser Companion static checks
Executed:
- JSON parse for `manifest.json`.
- `node --check` for MV3 service worker and three placeholder driver modules.

Result: PASS / exit code 0.

## Explicit SKIPS / Not Yet Proven

### Frontend install/build
SKIPPED in the generation environment because `npm install` was not performed against the external registry. Package versions were selected and recorded, but the target Windows machine must run `scripts/setup_dev.ps1`, then `npm run build` / `npm run test` before frontend baseline is considered locally proven.

### Database migration
NOT IMPLEMENTED YET. Alembic/Repository implementation belongs to First Vertical Slice WP-02.

### Real Runtime integration
NOT IMPLEMENTED YET. Codex/OpenCode Runtime conformance begins after the reference/mock runtime proves lifecycle semantics.

### Browser Web AI automation
NOT IMPLEMENTED YET. Only MV3 packaging/driver boundary scaffold exists.

## Gate

Repository scaffold is acceptable to enter `feature/first-vertical-slice` work. Product functionality must not be claimed from this report.
