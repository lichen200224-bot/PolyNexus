# D2a final-gate evidence — 2026-09-13

This file records the exact final-gate invocations for the D2a candidate. It
is intentionally separate from the checkpoint narrative so an independent
reviewer can inspect command, cwd, selected actual stdout, exit code, and
preconditions without relying on abbreviated placeholders.

## Candidate and evidence boundary

- Candidate before this evidence-only documentation commit: `25cd76071ec2fc200ff658ac07bf44d404d335a4`.
- Candidate tree before this evidence-only documentation commit: `5452c924de7803af24f78284147a40a16b958fa4`.
- Parent: `d59acb292e4327e975d018d23c92dd8023b21d90`.
- Lane: `C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree`.
- Branch: `codex/product-d2a`.
- The source-affecting remediation was committed in `25cd760...`; the
  subsequent commit containing this file and the checkpoint cross-reference
  is documentation-only.
- All commands below used explicit temporary roots. The relevant
  `--basetemp` paths were checked absent before their runs; no default
  `pytest-of-*` root was used by these final gates.

## 1. Targeted D2a contract gate

Command:

```text
D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B -m pytest --override-ini addopts= -q --disable-warnings -rA --basetemp C:\Users\shawn\AppData\Local\Temp\d2a-review-targeted-20260913 C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests\test_d2a_external_runtime.py
```

cwd:

```text
C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core
```

Selected actual stdout:

```text
.......s......                                                           [100%]
13 passed, 1 skipped, 1 warning in 3.80s
```

Exit: `0`.

The skipped case is the Windows symlink/reparse-point case; the test reports
that symlink creation is unavailable in this environment. The static
fail-closed path remains covered by the passing cases, while the privileged
OS capability itself is recorded as environment-unverified.

## 2. Affected regression gate

Command:

```text
D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B -m pytest --override-ini addopts= -q --disable-warnings --tb=no --basetemp C:\Users\shawn\AppData\Local\Temp\d2a-review-affected-compact-20260913 C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests\test_d2a_external_runtime.py C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests\test_d1a_generation_ownership.py::test_real_owned_tree_retry_late_abort_and_registry_loss C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests\test_d1a_generation_ownership.py::test_public_rest_execution_controls_real_job_and_terminal_cancel_is_inert C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests\test_g16_runtime_selection_policy.py C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests\test_mcf01_static_modules.py C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests\test_g14_runtime_reconciliation.py C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests\test_cp06_wp28_failure_injection.py C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests\test_g15_runtime_output_redaction.py
```

cwd:

```text
C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core
```

Selected actual stdout:

```text
.......s................................................................ [ 71%]
.............................                                            [100%]
100 passed, 1 skipped, 2 warnings in 8.68s
EXIT=0
```

Exit: `0`.

The eight exact inputs cover the D2a external runtime, D1a generation
ownership and terminal control, runtime selection policy, Static Module
registration, reconciliation, failure injection, and output redaction
surfaces.

## 3. Full Core regression gate

Command:

```text
D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B -m pytest --override-ini addopts= -q --disable-warnings --tb=no --basetemp C:\Users\shawn\AppData\Local\Temp\d2a-review-full-core-20260913 C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core\tests
```

cwd:

```text
C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\services\core
```

Selected actual stdout:

```text
........................................................................ [  8%]
........................................................................ [ 16%]
........................................................................ [ 24%]
........................................................................ [ 32%]
........................................................................ [ 40%]
........................................................................ [ 48%]
........................................................................ [ 56%]
........................................................................ [ 64%]
........................................................................ [ 72%]
........................................................................ [ 80%]
........................................................................ [ 88%]
........................................................................ [ 96%]
....................................                                     [100%]
886 passed, 1 skipped, 194 warnings in 105.85s (0:01:45)
```

Exit: `0`.

## 4. Web tests and build gate

Precondition: `apps/web/node_modules` existed (`Test-Path=True`) before the
final gate. An install was not needed and no package-install mutation was
performed during this gate.

cwd for both commands:

```text
C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\apps\web
```

Test command:

```text
npm test -- --run
```

Selected actual stdout:

```text
Test Files  4 passed (4)
Tests       94 passed (94)
Vitest      4.1.10
Duration    21.12s
```

Exit: `0`.

Build command:

```text
npm run build
```

Selected actual stdout:

```text
vite v8.2.0 building client environment for production...
✓ 27 modules transformed.
dist/index.html
dist/assets/index-wk6WkSGu.css
dist/assets/index-CtT5yrvK.js
✓ built in 94ms
```

Exit: `0`.

## 5. START validation gate

cwd for both commands:

```text
C:\Users\shawn\.codex\visualizations\2026\09\13\01a09a2c-5bc2-7111-89e6-574235e7cbf9\d2a-worktree\docs\delivery
```

Scope validator command:

```text
D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B checks/validate_feature_scope.py
```

Selected actual stdout:

```text
{"result":"PASS_PLANNING_STRUCTURE_ONLY","packages":22,"rows":78,"functional_subitems":257,"planned_pn_groups":156,"matrix_sha256":"2b56038cf278fe6a7ce80d1323d8d8005101b565d7c87cc175dbdcab5b0fb733","matrix_blob_sha256":"fb146c081a88d45f3eb0c113e0ed570edecf70b2"}
```

Exit: `0`.

Selftest command:

```text
D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B checks/selftest_feature_scope.py
```

Selected actual stdout:

```text
{"result":"PASS","case_count":27,"all_cases_matched":true,"product_tests":"NOT_RUN","independent_review":"NOT_RUN"}
```

Exit: `0`.

## Evidence interpretation

- The final gates above are real executions on the isolated D2a lane, not
  simulator-only substitutions.
- The one skipped Core case is explicitly retained as an environment
  limitation; it is not converted into a pass claim.
- The full Core run produced warnings but no failing test; warning details
  remain available from the exact command and are not treated as hidden
  failures.
- The final evidence commit is documentation-only relative to the tested
  source candidate. A fresh independent read-only reviewer must still verify
  this file and the resulting immutable candidate before D2A technical pass
  is declared.
