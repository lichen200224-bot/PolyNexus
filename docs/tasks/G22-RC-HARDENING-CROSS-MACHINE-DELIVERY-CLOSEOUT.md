# G22 — RC hardening, cross-machine verification, and delivery closeout

## Current result

`IMPLEMENTING / NEED_ACTION_PENDING_GATES`

G22 continues from the approved G21 checkpoint
`ada5e9c8b4873aad4c53c74198171740d376d926` on branch
`feature/g22-rc-hardening-cross-machine-delivery-closeout`. The independent G21
review reported `BLOCKER=0`, `MAJOR=2`. The encoded-loopback traversal finding is
remediated in this lane; provenance and evidence documents are synchronized. A
fresh G22 checkpoint, independent re-review, and clean-clone proof remain open.

## Bounded scope

Allowed files are the browser-companion loopback source and regression test,
G22 task/status/handoff/control-panel documents, and the G22 verification
artifact directory. Core contracts, Domain model, workflow semantics,
persistence/migrations, Product Scope, vendor boundary, ADR-001–010, and
credentialed or external-send behavior are protected and unchanged.

## Remediation

- `validateLoopbackBaseUrl` rejects raw `%2e`, `%2f`, and `%5c` encodings before
  `new URL()` can normalize away traversal evidence.
- Regression coverage includes the five encoded-dot review examples, encoded
  slash/backslash variants, raw traversal, HTTPS, localhost, credentialed
  endpoint rejection, and a valid loopback positive case.
- G21 browser evidence remains bounded predecessor evidence: HTTPS controlled
  fixture, `3/3` golden, `28/28` failure paths, observed external requests `0`,
  cleanup PASS, aggregate harness exit `0`. In-process matrix rows retain
  `exit_code: "N/A"`.

## Current verification

- Full Core suite: exit `0` under the approved controlled Python launcher.
- G22 targeted RC Core tests: `21 passed`, exit `0`.
- Browser-companion regression: `9/9`, exit `0`.
- Web `npm ci`, Vitest `80/80`, and production build: each exit `0` under the
  approved elevated install route.
- Baseline and governance validators: exit `0`.
- Encoded traversal supplementary matrix: 15 unsafe rejected cases plus two
  valid loopback cases, exit `0`.
- A fresh G22 browser harness attempt returned exit `1` because isolated Chrome
  did not expose the requested CDP listener (`ECONNREFUSED`). It is recorded as
  `NEED_ACTION`; it is not a browser PASS.

## Evidence artifacts

The current G22 bundle is
`artifacts/verification/g22-rc-20260902/`:

- `summary.json`
- `journey-matrix.json`
- `failure-path-matrix.json`
- `commands-and-exit-codes.md`
- `environment.json`
- `cdp-trace.json`
- `SHA256SUMS.txt`

The G21 predecessor bundle remains at
`artifacts/verification/g21-browser-20260902/`; its manifest now matches the
checked-out bytes of the tracked harness source after the independent integrity
check found a line-ending hash mismatch.

## Delivery and cross-machine gate

The G22 artifact index records current commands and inherited G21 evidence. The
final delivery gate must still verify an exact-allowlist G22 checkpoint on the
approved remote, a clean clone at that SHA, required paths, clean Git state, and
baseline validation in the clean clone. Until then:

- `CROSS_MACHINE_CONTINUATION_READY` is not claimed.
- `NEXT_GOAL_READY=G23` is not claimed.
- Live ChatGPT/Claude/Gemini behavior, native browser-loaded MV3 worker
  dispatch, credentials, cookies, tokens, and external send remain
  `UNVERIFIED` or prohibited.

## Clean-environment delivery instructions

From a clean clone, use repository-relative paths:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e ".\services\core[dev]"
Push-Location .\apps\web
npm ci
npm test
npm run build
Pop-Location
& .\.venv\Scripts\python.exe -B .\scripts\validate_baseline.py
& .\tools\validate-polynexus-governance.ps1 .
```

The Core dependency declaration is `services/core/pyproject.toml` (`Python
>=3.12`); the Web dependency and Node declaration are
`apps/web/package.json`/`apps/web/package-lock.json` (`Node >=22.12.0`); and
the extension declaration is `extensions/browser-companion/manifest.json`
(Manifest V3). This package is local-only and does not require vendor
credentials, cloud access, or an external connector.

## Routing footer

```yaml
TASK_ID: G22-RC-HARDENING-CROSS-MACHINE-AND-DELIVERY-CLOSEOUT
STATUS: IMPLEMENTING / NEED_ACTION_PENDING_GATES
RESULT: NEED_ACTION_PENDING_GATES
NEXT_ACTION: Run fresh current G22 gates, obtain independent re-review, then checkpoint and clean-clone verify.
NEXT_OWNER: Codex G22 lane
BLOCKERS: Fresh CDP browser rerun unavailable; final checkpoint and cross-machine proof pending.
HUMAN_ACTION_REQUIRED: NO for bounded remediation; final Human acceptance remains G23.
ADR_IMPACT: NONE
SCOPE_DEVIATION: NONE
```
