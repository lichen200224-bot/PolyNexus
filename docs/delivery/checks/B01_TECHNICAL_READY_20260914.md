# B01-TECH technical handoff — 2026-09-14

Status: `B01_TECHNICAL_READY`

Human-only status: `PENDING_FINAL_HUMAN_UAT`

This is a technical checkpoint only. It does not claim `B01_HUMAN_ACCEPTED`,
product acceptance, release, merge, push, deployment, or overall product
completion. The Human repo and the D1B accepted history remain outside this
worktree.

## Source and isolation

| Item | Actual value |
|---|---|
| Canonical remote | `https://github.com/lichen200224-bot/PolyNexus.git` |
| Remote verification | `git ls-remote` exit `0` |
| Default HEAD | `feature/g24-g30-development-completion-routing` → `4cc88feab4097481fa4725c659521c7431794d46` |
| D2a branch | `codex/product-d2a` → `8d219c999516ce651ac952c38bd31e67d19c54cb` |
| D1B branch | `codex/product-d1b` → `e9538f328f409e2cb7d6868a8b79cc33ba4bdd87` |
| D1B tree | `b88c555c15def8ad347b0928ec8aa58e681887b3` |
| B01 branch collision | None returned by canonical `ls-remote` |
| Actual isolated cwd | `C:\Users\shawn\.codex\visualizations\2026\09\14\01a09fe7-12e2-7c61-aa3e-fcbc0543de45\b01-tech-worktree` |
| Local branch | `codex/product-b01-tech` |
| Product HEAD/tree at run | `e9538f328f409e2cb7d6868a8b79cc33ba4bdd87` / `b88c555c15def8ad347b0928ec8aa58e681887b3` |
| Human repo action | Read-only pre/post check; no reset/clean/stash/overwrite |
| MCF-02 | `030890b30160f1063ac2cef1d36705a9ea70bddb` not adopted; no implementation copied |

The first non-elevated real-executor attempt was stopped after the bounded
window because the installed CLI could not reach its API and repeatedly
retried. Its stderr is retained outside this checkpoint as environment
diagnostic evidence; it is not used as a PASS. The final run used the same
synthetic-only scope with the required network-enabled execution permission.

## Implemented B01 harness

- `services/core/tests/fixtures/b01_synthetic_repo/bug.py` and
  `check_bug.py` (copied to the synthetic repo as `test_bug.py`): a real
  bounded repository whose baseline test fails on `return 41` and passes on
  `return 42`; the template name avoids accidental collection by the Core
  suite.
- `services/core/tests/test_b01_tech.py`: real Windows Job Object evidence for
  failure→cleanup→retry, generation/run separation, fence ownership, late
  abort isolation, process-tree timeout, and test-only P0 reconstruction.
- `tools/run_b01_tech.ps1`: bounded runner that initializes a fresh synthetic
  Git repo, invokes the installed Codex executor, captures runner/child/raw
  evidence, independently reruns the test, and runs the Core evidence tests.
- `artifacts/verification/b01-tech-20260914/`: JSON receipts and raw logs for
  the final fresh run.

The process-tree cases retain root, child, and grandchild handles. Cleanup
evidence is based on Job Object/accounting and retained-handle observations
(`stopped=true`, non-zero end observations, `signal=job_terminate`), not a
PID-existence query, a flag, or a sleep delay.

## Final fresh evidence

The durable receipts are under
`artifacts/verification/b01-tech-20260914/`.

| Case | Evidence | Actual result |
|---|---|---|
| Real bounded synthetic bug-fix | actual cwd, Codex child exit, inner test exit, source SHA/blob before/after, exact `bug.py` diff, source closure | PASS; baseline test `1`, Codex child `0`, inner pytest `0`, independent post-test `0`; only `bug.py` changed |
| Failure → retry → recovery | old/new generation and Run IDs, fence `1→2`, three owned handles each, cleanup facts, late abort comparison | PASS; old/new separated; late abort left g2 generation and process facts unchanged |
| Real process-tree timeout | `TIMED_OUT`, root/child/grandchild retained facts, end observation | PASS; `3/3` owned handles stopped, `3/3` had end observations; child exits `1,1,1` |
| Accepted P0 package | test-only protocol, open managed worktree, package verify, fresh offline DB, clean reconstruction, source hash map | PASS; offline verify true; reconstructed hashes equal accepted hashes; private provider session not required |
| Human boundary | fixture principal and protocol | Not Human acceptance; recorded as `TEST_ONLY`, Human UAT remains pending |

The final runner receipt records:

- `real_executor_exit=0`
- synthetic baseline `HEAD/tree`:
  `cc85371f03edfddbe6d7e09de5da51a367925dee` /
  `c127351da3e60f6e1ac50303b3aa64e1defd3518`
- `baseline_synthetic_test_exit=1`
- `post_synthetic_test_exit=0`
- `b01_core_tests_exit=0` (`3 passed`)
- synthetic source SHA-256:
  `bb90d2b315ed538549cd708303971dd03d30dd733928b845504fab3a42eeb914`
  →
  `aecc013c518523ca22b7e3780f87002f5cae13fabc369f2f59a1faf7058f8c76`
- synthetic Git blob:
  `1083d263a12f8ca0b19827526030ed286669b9df`
  →
  `eca386f51bbe9df459d3def8a91f74e99caeab92`
- exact diff: `return 41` → `return 42`

The raw Codex JSONL contains the actual inner command execution with exit
`0`; the wrapper's independent post-test is a separate child process and also
exited `0`.

## Validation commands and exits

All commands below use the isolated B01 cwd unless another cwd is stated.

| Command | Cwd | Exit/result |
|---|---|---:|
| `git ls-remote https://github.com/lichen200224-bot/PolyNexus.git refs/heads/feature/g24-g30-development-completion-routing refs/heads/codex/product-d2a refs/heads/codex/product-d1b refs/heads/codex/product-b01-tech` | initial isolated setup cwd | `0` |
| `D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B -m pytest --override-ini addopts= -q --disable-warnings --tb=short --basetemp <isolated-temp> tests/test_b01_tech.py` | `services/core` | `0` (`3 passed`) |
| `D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B -m pytest --override-ini addopts= -q --disable-warnings --tb=short --basetemp C:\Users\shawn\AppData\Local\Temp\b01-tech-affected-final tests/test_b01_tech.py tests/test_d1b_candidate_evidence_human_p0.py tests/test_d1b_runtime_producer.py tests/test_d1a_generation_ownership.py tests/test_cp06_wp28_failure_injection.py tests/test_d2a_external_runtime.py` | `services/core` | `0` (`50 passed, 1 skipped`) |
| `pwsh -NoLogo -NoProfile -NonInteractive -File tools/run_b01_tech.ps1 -ArtifactRoot <thread artifact root>` | repo root | `0` (`B01_TECHNICAL_READY`) |
| `D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B -m pytest --override-ini addopts= -q --disable-warnings --tb=short --basetemp C:\Users\shawn\AppData\Local\Temp\b01-tech-full-core-20260914 tests` | `services/core` | `0` (`914 passed, 1 skipped`) |
| `npm ci` | `apps/web` | `0` (`90 packages`) |
| `npm test -- --run` | `apps/web` | `0` (`4 files, 94 tests`) |
| `npm run build` | `apps/web` | `0` (Vite/TypeScript build) |
| `node --test extensions/browser-companion/tests/test_websurface_drivers.mjs` | repo root | `0` (`10 passed`) |
| `pwsh -NoLogo -NoProfile -NonInteractive -File tools/review_b01_tech.ps1 -EvidenceRoot artifacts/verification/b01-tech-20260914` | repo root | `0` (`B01_INDEPENDENT_REVIEW PASS`) |

The runner's final fresh evidence includes its exact artifact root and all
child command exits in `artifacts/verification/b01-tech-20260914/run.json`.

Final real-executor synthetic cwd:
`C:\Users\shawn\.codex\visualizations\2026\09\14\01a09fe7-12e2-7c61-aa3e-fcbc0543de45\b01-tech-evidence-20260914-final3\real-bug-fix\synthetic-repo`.

## Negative evidence and limitations

- No fixture principal was used as Human acceptance; no `B01_HUMAN_ACCEPTED`
  state was emitted.
- No MCF-02 code was integrated.
- No merge, tag, release, deployment, commit, or push was performed.
- The real executor requires a reachable API; the first non-elevated attempt
  was environment-blocked and is retained as such. The final technical run
  succeeded only after the permitted network escalation.
- The process-tree evidence proves the controlled synthetic tree and Core
  lifecycle boundary; it does not claim arbitrary provider processes are safe
  outside the owned Job Object.
- Full product delivery and the final Human UAT remain outside this milestone.

## Next owner / next action

Next owner: the product Controller / subsequent delivery batch.

Next action: preserve this candidate/evidence boundary, proceed to the next
approved technical work package, and later run `HU-01`–`HU-12` as the actual
Human-only UAT. Human acceptance must be recorded by the Human against the
exact delivered candidate; this checkpoint does not create that decision.
