# Development Preparation Checklist

Baseline: Development Baseline v1.0 + preparation patch v1.0.1

## A. Files / Repository
- [ ] Clone from Git bundle into the final PolyNexus folder.
- [ ] Confirm baseline commit/tag.
- [ ] Keep only one physical working tree for sequential Codex/OpenCode/Antigravity use.
- [ ] Rename/remove the bundle remote before adding an approved real remote.

## B. Required Environment
- [ ] Git for Windows available.
- [ ] Python 3.12+ available.
- [ ] Node 22.12+ available.
- [ ] npm available.
- [ ] Codex access verified.
- [ ] OpenCode access verified.
- [ ] Antigravity can open the same repo and see `.agents/rules` + `.agents/skills`.

Run:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1
```

## C. Install Dependencies
Run from repository root:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_dev.ps1
```

After the first successful install, review newly created dependency lock files before committing them.

## D. Readiness Gate
Run:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_dev_ready.ps1
```

Expected minimum evidence:
- baseline validation exit 0
- Core pytest exit 0
- frontend build exit 0
- frontend Vitest exit 0
- git diff --check exit 0

## E. AI Shared Memory / Rules
Every new tool session reads only:
1. `AGENTS.md`
2. `docs/11_PROJECT_STATE.md`
3. `docs/12_HANDOFF_CURRENT.md`
4. task-relevant specification/files

Do not preload all docs/logs/repo history.

Before switching tools:
- [ ] Run targeted tests.
- [ ] Update `docs/12_HANDOFF_CURRENT.md`.
- [ ] Record actual commands and exit codes.
- [ ] Check `git diff --stat` and `git status`.
- [ ] Commit a safe checkpoint when appropriate.

## F. Git Safety
- Single Active Writer.
- Feature branches are named by scope, not AI tool.
- Never use `git reset --hard`, force push, or clean unknown files without explicit human confirmation.
- Secrets, runtime DB, raw artifacts, screenshots and logs must not be committed.

## G. Open First Development Branch
Only after readiness gate is green:
```powershell
git switch develop
git pull --ff-only   # only if an approved real remote is configured
git switch -c feature/first-vertical-slice
```

Then follow `docs/20_FIRST_VERTICAL_SLICE_PLAN.md`.

## H. Tool Routing for First Vertical Slice
- Codex: Domain/Contracts/Run Supervisor/Workflow core/high-risk review.
- OpenCode: Repository/migration/API/UI/tests/routine implementation.
- Antigravity: reserve for milestone UI/E2E and browser-heavy verification.
- Deterministic test evidence decides PASS/FAIL.
