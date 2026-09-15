# Enhanced Delivery — G0 product continuation start receipt

TASK_ID: G0-CURRENT-B01-RECONCILIATION
ROLE: G0_CURRENT_PRODUCT_RECONCILIATION_CONTROLLER
CANONICAL_REMOTE: https://github.com/lichen200224-bot/PolyNexus.git
DOC_REVIEW: PASS
NORMATIVE_PLANNING_REFERENCE: planning/enhanced-runtime-control-plane@e470d25678941702dcb08301611650c1ee51cf04
G0: PASS
PRODUCT_CONTINUATION_BASE: ca85d22c44062d2856ab037a1ee1556ea26c70cc
PRODUCT_BASE_TREE: 3981c0a526c30ab98ec7b93717eaf5a4fa96e877
PRODUCT_BRANCH: codex/enhanced-delivery-runtime-fleet
NEXT_OWNER: ChatGPT independent Product Acceptance Center for first product-start verification
NEXT_ACTION: independently verify exact remote docs review and G0 receipts, then authorize D2B-01 start within approved scope
HUMAN_EXCEPTION_REQUIRED: NO

This branch was created directly from the exact B01 product SHA. The planning branch is a normative document reference, not a product-source merge base. This receipt is a docs-only checkpoint; no D2B-01 product implementation was started. `PENDING_FINAL_HUMAN_UAT` remains attached to B01 and is reserved for the concentrated final Human UAT. G0 technical PASS does not constitute final Human product acceptance, ChatGPT Candidate acceptance, merge approval, release or deployment.

## Canonical remote and ancestry

Direct canonical `git ls-remote` returned the docs reference above, D1B `codex/product-d1b@e9538f328f409e2cb7d6868a8b79cc33ba4bdd87`, and B01 `codex/product-b01-tech@ca85d22c44062d2856ab037a1ee1556ea26c70cc`; `codex/enhanced-delivery-runtime-fleet` was absent before creation. Earlier read-back confirmed D2a `8d219c999516ce651ac952c38bd31e67d19c54cb`, rejected old MCF-02 `030890b30160f1063ac2cef1d36705a9ea70bddb`, and governance `1ea8ce3df9bf6b1fc0899fcafaedeba2f4052af4`. Remote HEAD resolved to D1B. Local `origin/*` was not used as remote authority.

`git merge-base D1B B01` returned D1B; `git rev-list --count D1B..B01` returned `2`. The B01 commits are `95c879764f0c3772c0b2254c06080b45c66e13c9` (technical harness/evidence) and `ca85d22c44062d2856ab037a1ee1556ea26c70cc` (Web dependency hardening). Actual D1B-to-B01 paths are `apps/web/package.json`, `apps/web/package-lock.json`, `docs/delivery/checks/B01_INDEPENDENT_REVIEW_20260914.md`, `docs/delivery/checks/B01_TECHNICAL_READY_20260914.md`, two synthetic fixture files, `services/core/tests/test_b01_tech.py`, `tools/run_b01_tech.ps1`, and `tools/review_b01_tech.ps1`. No `services/core/src` product source path changed. The old MCF-02 branch is REJECTED/NOT_ADOPTED and is not in this product ancestry.

## Independent B01 evidence finding

The G0 controller inspected the original local raw evidence at `C:\Users\shawn\.codex\visualizations\2026\09\14\01a09fe7-12e2-7c61-aa3e-fcbc0543de45\b01-tech-worktree\artifacts\verification\b01-tech-20260914`. It exists outside Git and remains marked local raw evidence, not remote Candidate content. `run.json`, `real-bug-fix.json`, Codex JSONL, failure/retry, process-tree timeout, and P0 reconstruction JSON were read, then the committed reviewer tool was independently rerun against that root (exit `0`). A receiver must independently inspect raw evidence; this receipt is not a substitute for it.

- Real installed Codex executor was observed as `codex-cli 0.154.0-alpha.6.2`. The original baseline synthetic test exited `1`; the executor child and inner command exited `0`; independent post-test exited `0`. Raw JSONL shows the actual `test_bug.py` command and exit. Only synthetic `bug.py` changed `return 41` to `return 42`; actual after SHA-256 `aecc013c518523ca22b7e3780f87002f5cae13fabc369f2f59a1faf7058f8c76` was separately observed from the surviving file.
- Failure -> cleanup -> Retry used generation `1`/Run `run_8093b7d238d44d0288c0aa23b7286dcb`, then generation `2`/Run `run_4e456a527a9e4fba96c7e53ebade9397`; ownership fence rose `1` to `2`. Both old and new controlled root/child/grandchild handles had end observations and stopped facts. Late Abort of g1 did not change g2 generation or process facts.
- Timeout raw JSON records `TIMED_OUT`, three owned handles stopped with nonzero end observations and `job_terminate`; PID scan and flags were not used as the oracle. The child exit values `1` are negative-path evidence, not runner failure.
- P0 raw JSON records TEST_ONLY principal, offline verification true, equal accepted/reconstructed source hashes, and no provider-private-session dependency. Fresh `test_b01_tech.py` execution also verified P0/reconstruction in the isolated checkout; its generated package was observed at 15,867 bytes with SHA-256 `f29eb5738be54cd7bdee04ffdceecfe7c41ec4528e08878ecb6231ab1b16d278`. The historical P0 zip itself was inaccessible to this sandbox, so that direct historical-byte check is NOT_VERIFIED; it is not represented as PASS.
- The Web dependency delta pins direct/transitive Vitest `4.1.10` to `4.1.11`; clean `npm ci` installed 90 packages, and current moderate-level audit returned zero vulnerabilities. The unchanged sourcemap-codec lock integrity correction is consistent with the documented `EINTEGRITY` remediation. No Core source/contract was changed by dependency hardening.

## Actual verification commands and exits

All fresh product commands below ran in the isolated exact B01 checkout `C:\Users\shawn\OneDrive\文件\PONYNEXUS\g0-b01-review-ca85d22`; Core commands ran from its `services\core`, Web commands from `apps\web`, and browser/reviewer commands from the repo root. Their raw logs are under `C:\Users\shawn\.codex\visualizations\2026\09\15\01a0a4f7-6bcd-7160-930d-22c233db3134`.

| Command | Actual exit | Result / evidence |
|---|---:|---|
| `git diff --quiet D1B B01 -- services/core/src` | 0 | no Core product-source delta |
| `git diff --check D1B B01` | 0 | no diff errors |
| `D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -B -m pytest --override-ini addopts= -q --disable-warnings --tb=short --basetemp <isolated> tests/test_b01_tech.py` | 0 | 3 passed; `g0-b01-targeted-20260915.log` |
| same pytest invocation with B01, D1B Candidate/Human/P0, D1B producer, D1a ownership, CP06 failure injection and D2a external runtime test files | 0 | 50 passed, 1 skipped; `g0-b01-affected-20260915.log` |
| full `pytest ... --basetemp <visualization-root> tests` | 1 | 911 passed, 1 skipped, 3 backup-path failures; `g0-b01-full-core-20260915.log` |
| backup module `pytest ... --basetemp <OS-temp-root> tests/test_wp23_backup_restore_migration.py` | 0 | 4 passed; `g0-b01-backup-temp-correction-20260915.log` |
| full `pytest ... --basetemp <OS-temp-root> tests` | 0 | 914 passed, 1 skipped; `g0-b01-full-core-correct-temp-20260915.log` |
| `npm ci` with default cache | -4048 | EPERM cache access; `g0-b01-npm-ci-20260915.log` |
| `npm ci --cache <isolated-cache>` without network permission | 1 | EACCES registry access; `g0-b01-npm-ci-local-cache-20260915.log` |
| same `npm ci --cache <isolated-cache>` with approved network permission | 0 | 90 packages, 0 vulnerabilities; `g0-b01-npm-ci-elevated-20260915.log` |
| `npm audit --audit-level=moderate --cache <isolated-cache>` | 0 | 0 vulnerabilities; `g0-b01-npm-audit-20260915.log` |
| `npm test -- --run` | 0 | 4 files, 94 tests; `g0-b01-web-test-20260915.log` |
| `npm run build` | 0 | TypeScript/Vite build; `g0-b01-web-build-20260915.log` |
| `node --test extensions/browser-companion/tests/test_websurface_drivers.mjs` | 0 | 10 passed; `g0-b01-browser-companion-20260915.log` |
| `pwsh -NoLogo -NoProfile -NonInteractive -File tools/review_b01_tech.ps1 -EvidenceRoot <historical raw root>` | 0 | reviewer receipt predicates confirmed; `g0-b01-reviewer-rerun-20260915.log` |

The one Core skip is the D2a symlink-creation case: `pytest.skip("symlink creation is unavailable in this Windows test environment")`; it remains SKIPPED, not PASS. The first full suite failures were caused by the controller's `--basetemp` outside `tempfile.gettempdir()`, which the existing backup boundary correctly rejects with `backup_not_isolated`; the initial exit `1` is retained. The fresh rerun used an isolated child of the actual OS temp root and passed without changing product source, tests or oracle. The two initial npm failures were cache/network permission conditions; the final clean install and audit passed in the isolated checkout.

## D2B-01 start envelope and stop condition

The approved next product unit is D2B-01 OpenCode ACP, after ChatGPT independently verifies this exact remote branch/start receipt. Use the normative docs SHA above and the current accepted Core lineage. D2B-01 may add only a bounded generic ACP transport and thin OpenCode adapter on Core-owned RuntimeRegistry/RuntimeModuleBridge/RunSupervisor, immutable binding, PROJECTED_STAGING, input/output allowlists, policy/egress, SecretRef, Artifact/Evidence, Candidate/Verification and Human protocol. The rejected `030890b3` implementation may be read only for source-level comparison; it must not be merged/cherry-picked/copied wholesale. Real OpenCode target evidence and negative containment/timeout/cleanup/postcondition cases are required. No D2B-01 source write, Candidate, ChatGPT acceptance, release or Human final acceptance is claimed by G0.

READY_FOR_D2B01_PRODUCT_START means the technical continuation base and branch are prepared for ChatGPT's first independent product-start verification. Stop here until that verification; `SKIPPED != PASS`, Writer receipt is not acceptance, and only an exact subsequent ChatGPT PASS may allow product implementation.
