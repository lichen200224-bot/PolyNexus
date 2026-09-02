# G22 — RC hardening, cross-machine verification, and delivery closeout

> **Post-task terminal note (2026-09-02):** G23 subsequently reconciled this
> checkpoint at exact SHA `0eb56a986e97a45854bd6ddd419c114845ce51f4`,
> and the Human explicitly returned `G23_DECISION=ACCEPT`. G22 remains
> `PASS / CHECKPOINTED`; its residual limitations remain active and unchanged.

## Current result

`PASS / CHECKPOINTED` for bounded RC hardening and delivery closeout.

G22 continues from the approved G21 checkpoint
`ada5e9c8b4873aad4c53c74198171740d376d926` on branch
`feature/g22-rc-hardening-cross-machine-delivery-closeout`. The independent G21
review reported `BLOCKER=0`, `MAJOR=2`. The encoded-loopback traversal finding is
remediated in this lane; provenance and evidence documents are synchronized;
independent re-review and clean-clone proof passed for the bounded scope.

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
validated product checkpoint `532ce8f1c479a3c593c990ede89b5b75e810762f` was
verified by clean clone `g22-clean-20260902`, which contains the required paths,
has clean Git state, and passed baseline, targeted Core, browser-companion, and
Web install/test/build checks. The later independently reviewed evidence-state
tip `9a17716f87e4df14def5086bafee6d86d3484596` was verified by final clean clone
`g22-clean-final-20260902`; its required paths, manifest, and baseline checks
also exited `0`. The current final branch tip is resolved from the approved
remote and published in the completion result, not embedded in this
self-referential task document.
Therefore:

- `CROSS_MACHINE_CONTINUATION_READY` is claimed for the bounded delivery scope.
- `NEXT_GOAL_READY=G23` is recorded.
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
STATUS: CHECKPOINTED
RESULT: PASS (bounded RC hardening and delivery closeout)
NEXT_ACTION: G23 final reconciliation and Human acceptance packet.
NEXT_OWNER: Codex G23 lane
BLOCKERS: Fresh G22 CDP browser rerun remains NEED_ACTION; no broad vendor claim is made.
HUMAN_ACTION_REQUIRED: NO for bounded remediation; final Human acceptance remains G23.
ADR_IMPACT: NONE
SCOPE_DEVIATION: NONE
```
