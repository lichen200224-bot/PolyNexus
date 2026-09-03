# G30 Cross-machine GitHub Continuation Enablement

## Current disposition

- `STATUS`: `NEED_ACTION / HUMAN_DECISION_REQUIRED`
- `PURPOSE`: make another computer able to obtain the approved PolyNexus
  tracked project over network Git/GitHub and continue development/testing.
- `WRITER`: `Codex` — read-only precheck and documentation only
- `REMOTE_MUTATION`: `NOT_PERFORMED`
- `COMMIT_PUSH`: `NOT_PERFORMED`

## Verified current state

- Current approved local checkpoint/ref:
  `D:/GitBackup/PolyNexus_Backup.git` /
  `feature/g24-g30-development-completion-routing` /
  `2bbcb0cb2cc6bc39e5a5770f91b9c58c03fed762`.
- Current local remotes are `backup` (local bare repository) and `baseline`
  (local bundle). There is no configured GitHub `origin`.
- The `backup` path is not a portable network source for another computer.
- The approved checkpoint contains tracked PolyNexus source and predecessor
  records including WP-19, G21, and browser-companion source/tests.
- The current G30 lane is dirty. G29 operator pack, G29 HTML manual, G30 task
  records, and ignored verification evidence are not present in the approved
  remote checkpoint and must not be silently assumed to be cloneable.
- Primary checkout remains protected and dirty; it is not a source for a
  cross-machine export.

## Required Human decisions before GitHub work

Provide all of the following in one explicit Git Gate:

1. Exact approved GitHub repository clone URL.
2. Confirmation that the repository is the intended private collaboration
   repository and is empty or has a reconciled history.
3. Exact branch/ref to publish; do not infer it from the local backup name.
4. Explicit authorization for remote configuration, the exact staged-file
   allowlist, commit, and push. Remote configuration approval alone does not
   authorize push.
5. Whether the untracked G29/G30 documentation overlay is approved for the
   checkpoint. Ignored `artifacts/` evidence is excluded unless separately
   approved and sanitized.

Do not provide passwords, access tokens, SSH private keys, cookies, or other
secrets to an Agent. Human may authenticate through an approved local Git
credential mechanism without exposing its values.

## Proposed bounded publication surface

After fresh review and explicit approval, the candidate documentation surface is
limited to the following paths; no product/runtime/schema/ADR source is proposed:

- `docs/10_DECISION_LOG.md`
- `docs/11_PROJECT_STATE.md`
- `docs/12_HANDOFF_CURRENT.md`
- `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`
- `docs/33_DEVELOPMENT_PROGRESS_AND_GOAL_EXECUTION_STANDARD.md`
- `docs/GOAL_COMPLETION_CONTROL_PANEL.html`
- `docs/GOAL_COMPLETION_CONTROL_PANEL.md`
- `docs/tasks/G24-G30-DEVELOPMENT-COMPLETION-ROUTING.md`
- `docs/tasks/G29-EXTERNAL-OPERATOR-PROMPT.md`
- `docs/tasks/G29-EXTERNAL-OPERATOR-RUNBOOK.md`
- `docs/tasks/G29-EXTERNAL-REPORT-TEMPLATE.md`
- `docs/tasks/G29-EXTERNAL-TEST-MATRIX.md`
- `docs/tasks/G29-HUMAN-OPERATOR-TEST-MANUAL.html`
- `docs/tasks/G30-FINAL-EXTERNAL-VERIFICATION-AND-100-POINT-RECONCILIATION.md`
- `docs/tasks/G30-CROSS-MACHINE-GITHUB-CONTINUATION.md`

Excluded by default: primary dirty files, `artifacts/`, `.venv/`,
`node_modules/`, `dist/`, databases, browser profiles, raw reports, secrets,
credentials, cookies, tokens, request bodies, headers, and unmasked captures.

## Exact controlled-push sequence after approval

Run only in the isolated G30 lane, after the approved URL and allowlist are
recorded:

```powershell
git remote -v
git remote add origin <APPROVED_GITHUB_URL>
git fetch origin --prune
git ls-remote origin
git status --short --branch
git diff --check
```

If the GitHub repository has unrelated history, stop with
`REMOTE_HISTORY_RECONCILIATION_REQUIRED`; never force-push. After explicit
allowlist approval, stage only named paths, verify cached status, commit the
approved checkpoint, and push only the approved branch. `git push --all` and
force push are prohibited.

## Clean-clone round trip on another computer

The verifier must use a new directory and the approved URL/ref:

```powershell
git clone --branch <APPROVED_BRANCH> <APPROVED_GITHUB_URL> PolyNexus-clean-check
Set-Location .\PolyNexus-clean-check
git rev-parse HEAD
git status --short --branch
git ls-tree -r --name-only HEAD -- docs extensions/browser-companion
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup_dev.ps1
& .\.venv\Scripts\python.exe -m pytest -q services\core
node --test extensions\browser-companion\tests\test_websurface_drivers.mjs
Set-Location .\apps\web
npm test
npm run build
Set-Location ..\..
git diff --check
```

Record exact commands, actual exit codes, passed/failed/skipped, installed
versions, remote/ref, HEAD, clean status, required-file checks, and any
environment failure. Only after the clean clone and applicable checks pass may
the result be called `CROSS_MACHINE_CONTINUATION_READY`.

## Current next action

Human supplies the exact GitHub URL, branch decision, and explicit remote/
commit/push authorization. Until then, use the approved local checkpoint for
tracked source and transfer the sanitized G29/G30 documentation overlay
separately. Do not start G31.
