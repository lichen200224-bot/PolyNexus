# D1B / D11-A-LP Local Enrollment Issuer — Implementation Evidence

Status: TECHNICAL_VALIDATION_PASS / HUMAN_PRODUCT_ACCEPTANCE_PASS

Evidence date: 2026-09-14 (Asia/Taipei)

This record preserves the implementation source, ref preflight, commands,
exit codes, negative evidence and the completed isolated Human UAT for the
D1B worktree. It does not authorize a commit, push, merge, tag, release,
deployment or formal contract amendment.

## 1. Source and repository preflight

Isolated worktree:

~~~text
C:\Users\shawn\.codex\visualizations\2026\09\13\01a09b25-1b9e-7563-8789-da92fd098193\d1b-worktree
~~~

The following read-only commands were run from that worktree:

~~~powershell
git status --short --branch
# exit 0; ## codex/product-d1b; expected D1B files are modified/untracked
git rev-parse HEAD
# exit 0; 8d219c999516ce651ac952c38bd31e67d19c54cb
git rev-parse 'HEAD^{tree}'
# exit 0; 3fc52b75bdde0a29b8c649205ac6bd3644b5116e
git diff --check
# exit 0; no output
~~~

The isolated HEAD is the D2a technical checkpoint and remains uncommitted;
the D1B implementation is represented by the working-tree diff. The change
set includes the A-LP verifier, trust registry migration `0009`, Core/API
enrollment routes, browser re-pair UX, D1B tests and the delivery records.

Canonical remote preflight:

~~~powershell
git ls-remote --heads 'https://github.com/lichen200224-bot/PolyNexus.git' refs/heads/codex/product-d1b refs/heads/codex/product-d2a refs/heads/feature/g24-g30-development-completion-routing refs/heads/feature/mcf-01-static-module-contract
# exit 0
# 8d219c999516ce651ac952c38bd31e67d19c54cb refs/heads/codex/product-d2a
# 4cc88feab4097481fa4725c659521c7431794d46 refs/heads/feature/g24-g30-development-completion-routing
# f0c0b986380dc21d103d4e856057cb8ac435a8f9 refs/heads/feature/mcf-01-static-module-contract
git ls-remote --exit-code --heads 'https://github.com/lichen200224-bot/PolyNexus.git' refs/heads/codex/product-d1b
# exit 1; no output; expected no remote branch collision
git merge-base --is-ancestor 8d219c999516ce651ac952c38bd31e67d19c54cb HEAD
# exit 0
git merge-base --is-ancestor 4cc88feab4097481fa4725c659521c7431794d46 HEAD
# exit 0
~~~

The forbidden MCF-02 implementation was not adopted. Its object is not
reachable from the isolated branch; a local reachability check returned exit
1 because that commit object is not present locally.

Human repository post-state, checked without changing global Git config:

~~~powershell
git -c 'safe.directory=D:/AI學習教材/PolyNexus' -C 'D:/AI學習教材/PolyNexus' status --short --branch
# exit 0; ## feature/mcf-01-static-module-contract;  M AGENTS.md
git -c 'safe.directory=D:/AI學習教材/PolyNexus' -C 'D:/AI學習教材/PolyNexus' rev-parse HEAD
# exit 0; 86d5939044c1d7ec2a991820f39287481ee9120f
git -c 'safe.directory=D:/AI學習教材/PolyNexus' -C 'D:/AI學習教材/PolyNexus' rev-parse 'HEAD^{tree}'
# exit 0; fff3c8821568f078410b908361f24b48151c3cd2
~~~

No Human-repo file was modified, reset, cleaned, stashed or overwritten.
No remote write command was run.

## 2. Validation commands

Core virtual environment used:

~~~text
D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe
~~~

Targeted A-LP/API/P0 regression, run from the isolated worktree:

~~~powershell
& 'D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe' -m pytest -q --basetemp 'C:\Users\shawn\.codex\visualizations\2026\09\13\01a09b25-1b9e-7563-8789-da92fd098193\d1b-pytest-temp-a-lp-7' services/core/tests/test_d1b_a_lp.py services/core/tests/test_d1b_api.py services/core/tests/test_d1b_candidate_evidence_human_p0.py
# exit 0
~~~

Affected regression, including migration, runtime, D1a compatibility and
WP23 backup tests:

~~~powershell
& 'D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe' -m pytest -q --basetemp 'C:\Users\shawn\AppData\Local\Temp\polynexus-d1b-affected-final' services/core/tests/test_d1b_a_lp.py services/core/tests/test_d1b_api.py services/core/tests/test_d1b_candidate_evidence_human_p0.py services/core/tests/test_d1b_runtime_producer.py services/core/tests/test_baseline_debt_01_migration.py services/core/tests/test_cp06_wp30_clean_install.py services/core/tests/test_d1a_project_context.py services/core/tests/test_d1a_migration_restore.py services/core/tests/test_wp23_backup_restore_migration.py
# exit 0
~~~

Relevant full Core validation:

~~~powershell
& 'D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe' -m pytest -q --basetemp 'C:\Users\shawn\AppData\Local\Temp\polynexus-d1b-full-core-final' services/core/tests
# exit 0; 100% complete; warnings only
~~~

Web validation, run from:

~~~text
C:\Users\shawn\.codex\visualizations\2026\09\13\01a09b25-1b9e-7563-8789-da92fd098193\d1b-worktree\apps\web
~~~

~~~powershell
& '.\node_modules\.bin\tsc.cmd' -b
# exit 0
& '.\node_modules\.bin\vitest.cmd' run
# exit 0; 4 test files, 94 tests passed
& '.\node_modules\.bin\vite.cmd' build
# exit 0; production bundle built
~~~

Additional source hygiene checks from the isolated worktree:

~~~powershell
& 'D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe' -c "import ast; from pathlib import Path; paths=['services/core/src/polynexus_core/security/a_lp.py','services/core/src/polynexus_core/persistence/d1b.py','services/core/src/polynexus_core/persistence/models.py','services/core/src/polynexus_core/api/d1b.py','services/core/alembic/versions/0009_d1b_a_lp_trust_registry.py','services/core/tests/test_d1b_a_lp.py']; [ast.parse(Path(p).read_text(encoding='utf-8')) for p in paths]; print('AST_OK', len(paths))"
# exit 0; AST_OK 6
git diff --check
# exit 0
~~~

## 3. Negative and recovery evidence

The A-LP test vectors and API tests demonstrate the following fail-closed
outcomes:

- HMAC/fixture pairing in LOCAL returns `d1b_fixture_route_disabled` and does
  not elevate the loopback token.
- Wrong WebAuthn signature returns `ecdsa_signature_invalid`.
- Reusing an enrollment challenge returns `enrollment_challenge_replayed`.
- A delayed bootstrap registration cannot create a second principal and returns
  `enrollment_rotation_required`.
- Missing or wrong Origin is rejected; browser JSON aliases are accepted only
  through the strict schema.
- A revoked or retired key cannot create a new pairing; revocation also
  invalidates its grants and sessions.
- The v2 flow records `d11-a-lp-webauthn`, `key_id` and
  `enrollment_challenge_id` in decision protocol evidence while keeping raw
  WebAuthn responses, private keys, pairing tokens and nonce values out of
  durable trust records.
- The v2 session crosses exact Candidate view, decision challenge and nonce
  validation before append-only decision creation.

The first full Core attempt used a worktree-local pytest `--basetemp` and
returned exit 1 only because the existing WP23 backup isolation policy rejects
that location (`backup_not_isolated`). The same four WP23 tests and the full
Core suite were rerun with dedicated directories under the OS temporary root;
both returned exit 0. An earlier targeted run without `--basetemp` also
returned exit 1 during pytest setup with Windows `PermissionError` on the
system temp path; no test body failed in that attempt.

## 4. Human UAT and acceptance evidence

The Human supplied `A_LP_INDEPENDENT_REVIEW_PASS`, which is recorded as a
Human gate declaration. No agent-generated independent-review log is claimed.

Technical implementation and automated validation pass on the isolated branch.
The following local UAT was completed against the isolated temporary runtime
database; the Human repository and canonical remote were not touched.

UAT runtime and candidate:

~~~text
Runtime UI: http://localhost:5173/
LOCAL Core: http://localhost:8765/
UAT database: C:\Users\shawn\AppData\Local\Temp\polynexus-d1b-uat-0914-01\d1b-uat.db
Candidate: sha256:3df8b038b907222091ba2b4ded0a4555b63fa4012ef3de275821ba7d8821213a
~~~

Validation evidence preparation:

~~~text
cwd: C:\Users\shawn\OneDrive\文件\PONYNEXUS
argv: python -c candidate_view_exact_content_validation
check: uat-flow / REQUIRED / APPLICABLE
first malformed runner attempt: exit 1; TypeError before evidence write
corrected runner: exit 0
raw artifact: sha256:5b2e46ee564e031f41908fbf7936f59be75864663cd8b05e662a02e1bb031598
verification API: POST /api/v1/candidates/{candidate_id}/verifications -> HTTP 201
verification: PASS / VALID / acceptance_eligible=true
verification_id: verification_425fc8b649e7c521edf8fc4b1e7edd0a
evidence_set_id: sha256:573c7501ff97da81505dc1e16b70f0c364b8a6b5164bc4a06bb47f3f4781d741
~~~

The verification API call used the explicit TEST-only fixture route solely to
prepare this isolated UAT candidate; its temporary Core process was stopped
after the HTTP `201` result. The Human pairing, session, exact-view challenge
and decision were then performed against the LOCAL Core with browser-mediated
WebAuthn / Windows Hello. No fixture Human proof was used for the Human flow.

Human UAT result:

~~~text
Windows Hello public-key fingerprint shown to Human:
  sha256:4d1500b64950d5a9cf67994028a86d538f5cca3edaa2fb6bfd1b496009ed1b03
auth_method: d11-a-lp-webauthn
challenge view digest:
  sha256:1f8d870bf7131625f7bcff23a5121a1e861dfc795ee4452a977f4f7d58f100ab
server request: POST /api/v1/human/decisions -> HTTP 201 Created
decision_id: decision_17ad029a77172da8ad7d7758133f2e84
acceptance_id: acceptance_c41772c9951efd220e4eccbe4a8a9bcd
accepted-result view digest:
  sha256:1f8d870bf7131625f7bcff23a5121a1e861dfc795ee4452a977f4f7d58f100ab
challenge consumed_at: 2026-09-14 12:10:20.271808
final UI disposition: ACCEPTED
final UI decision revision: 1 / 1
~~~

Read-only post-state database evidence:

~~~text
human_decision_events=1
accepted_results=1
verification_records=1
latest challenge consumed_at is non-null and its candidate/action/view digest
match the accepted decision
Human session status=ACTIVE at verification time
~~~

Negative and recovery evidence observed during the same UAT:

- An expired decision challenge returned HTTP `409` and created no decision
  event; the challenge was cancelled and replaced rather than replayed.
- An unverified candidate returned HTTP `409` with the UI state
  `verification_missing` / `acceptance_eligible=no`; no decision event was
  created. This confirmed the mandatory verification gate before retrying.
- The stale challenge bound to the pre-verification view was cancelled before
  issuing the fresh challenge bound to the verified view digest.
- Raw WebAuthn responses, private keys and nonce values were not written to
  the evidence document or ordinary durable records.

`HUMAN_PRODUCT_ACCEPTANCE=DECLARED` for this isolated D1B Local-Personal /
Windows Hello UAT. This declaration does not authorize commit, push, merge,
tag, release, deployment, production enrollment, or changes to the Human
repository.
