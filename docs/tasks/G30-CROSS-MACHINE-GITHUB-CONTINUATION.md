# G30 Cross-machine GitHub Continuation Enablement

## Current disposition

- `STATUS`: `VERIFIED / CROSS_MACHINE_CONTINUATION_READY`
- `PURPOSE`: make another computer able to obtain the approved PolyNexus
  tracked project over network Git/GitHub and continue development/testing.
- `WRITER`: `Codex` — bounded documentation publication and verification
- `REMOTE_MUTATION`: `COMPLETED` — `origin` configured only in the isolated G30 lane
- `COMMIT_PUSH`: `COMPLETED` — documentation-only commit pushed to the approved ref

## Verified current state

- Published approved GitHub checkpoint/ref:
  `https://github.com/lichen200224-bot/PolyNexus.git` /
  `feature/g24-g30-development-completion-routing` /
  `e65c19bc6df8dd0362749d9016feabacf8acf6dc`.
- The predecessor approved local checkpoint/ref remains:
  `D:/GitBackup/PolyNexus_Backup.git` /
  `feature/g24-g30-development-completion-routing` /
  `2bbcb0cb2cc6bc39e5a5770f91b9c58c03fed762`.
- Isolated G30 lane remotes now include the approved GitHub `origin`, in
  addition to local `backup` and `baseline`. Primary remote configuration was
  not changed.
- The `backup` path is not a portable network source for another computer.
- The approved checkpoint contains tracked PolyNexus source and predecessor
  records including WP-19, G21, and browser-companion source/tests.
- The published checkpoint includes the G29 operator pack, G29 HTML manual,
  G30 task records, and cross-machine continuation instructions. Ignored
  verification evidence remains excluded and must not be silently assumed to
  be cloneable.
- Primary checkout remains protected and dirty; it is not a source for a
  cross-machine export.

### Clean-clone evidence

- New clean clone:
  `D:/AI學習教材/PolyNexus/artifacts/verification/g30-cross-machine-clean-clone-20260903`.
- Clone command used the approved GitHub URL and branch; clone completed with
  exit code `0`.
- Clean clone HEAD matched the published ref:
  `e65c19bc6df8dd0362749d9016feabacf8acf6dc`.
- `git status --short --branch` was clean and tracked the approved GitHub ref.
- Required G29/G30 docs, `scripts/setup_dev.ps1`, browser-companion source/tests,
  Core source, migrations, and tests were present.
- Clean-clone deterministic checks: baseline validator exit `0`; governance
  validator exit `0`; browser-companion tests `10 passed / 0 failed / 0 skipped`,
  exit `0`; Core pytest exit `0` with all collected tests passing. The Core run
  emitted only the known non-fatal Windows pytest temp cleanup warning after
  successful completion.

## Historical pre-push Human gate (completed)

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

Cross-machine GitHub continuation is verified. The next owner is the
authorized Human operator for the deferred G30 Level 3A vendor reports; use the
published G29/G30 operator pack and return sanitized reports only. Do not start
G31.
