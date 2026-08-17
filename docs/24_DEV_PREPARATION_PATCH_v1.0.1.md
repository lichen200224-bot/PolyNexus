# Development Preparation Patch v1.0.1

No architecture ADR changed.

Fixes before target-machine setup:
1. `scripts/test_core.ps1` now resolves the root `.venv` using `$PSScriptRoot`, so it works after changing into `services/core`.
2. Added a minimal frontend Vitest smoke test so `npm run test` has an actual baseline test instead of failing due to no test files.
3. Added `scripts/check_environment.ps1` for Git/Python/Node/npm and optional Codex/OpenCode checks.
4. Added `scripts/verify_dev_ready.ps1` as the consolidated local readiness gate.
5. Added `docs/23_DEV_PREPARATION_CHECKLIST.md` for manual setup and handoff checks.
