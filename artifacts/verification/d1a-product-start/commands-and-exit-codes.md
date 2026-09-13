# D1a final command and exit evidence

This is the compact final receipt for the source fingerprint at HEAD
`1b79c511ec0b7358525d8ca1101d4c07b57551f6`. Paths are sanitized labels; long
raw logs and process details remain in the external evidence bundle. The
browser evidence was collected before repair #26, and #26 changes only the
Core test oracle, so the production and Web trees are identical to the
observed browser fingerprint.

## Final bound runs

| Run | Exact command | cwd | Exit | Observed summary |
|---|---|---|---:|---|
| Repair #26 targeted | `python -B -m pytest -p no:cacheprovider --basetemp <system-temp>\\d1a-repair26-targeted tests/test_baseline_debt_01.py::test_service_cancellation_durable_after_reopen --tb=short -rs` | `<lane>\\services\\core` | 0 | 24 passed |
| D1a affected Core | `python -B -m pytest -p no:cacheprovider --basetemp <system-temp>\\d1a-affected-final <affected-test-selection> --tb=short -rs` | `<lane>\\services\\core` | 0 | 183 passed |
| Policy/security affected Core | `python -B -m pytest -p no:cacheprovider --basetemp <system-temp>\\policy-security-affected-final <policy-security-test-selection> --tb=short -rs` | `<lane>\\services\\core` | 0 | 74 passed |
| Full Core after repair #26 | `python -B -m pytest -p no:cacheprovider tests --tb=short -rs` | `<lane>\\services\\core` | 0 | 873 passed, 193 warnings, 122.25s; pytest temporary files used the system tempfile root |
| Web full | `npm test` (package script: `vitest run`) | `<lane>\\apps\\web` | 0 | 94 passed |
| Web production build | `npm run build` (package script: `tsc -b && vite build`) | `<lane>\\apps\\web` | 0 | build passed |
| Browser probe 1 | `powershell -NoProfile -ExecutionPolicy Bypass -File <evidence>\\start_browser_probe.ps1 -ProbeName cap25-browser -Seconds 110 -DbName browser.db` | `<evidence>` | 0 | Core 200, Web 200, anonymous 403, wrong token 403; owned processes/listeners cleaned |
| Browser probe 2 | `powershell -NoProfile -ExecutionPolicy Bypass -File <evidence>\\start_browser_probe.ps1 -ProbeName cap25-reconnect -Seconds 60 -DbName browser.db` | `<evidence>` | 0 | Core 200, Web 200, anonymous 403, wrong token 403; owned processes/listeners cleaned |
| Browser UI journey | Codex in-app browser via cua_repl at `http://127.0.0.1:5173/` | product/Web at commit above | N/A | OBSERVED_PASS; visible readiness, explicit selection, reconnect, offline Retry, archive boundaries and empty CREATED outputs |

The affected-test and policy/security selections are retained in the
controller's external command records; this file records their exact runner
shape, cwd class, exit and sanitized result without copying large raw argv,
PID or hash payloads.

## Browser observations

The synthetic local-only journey reopened Project
`project_2ff8e3f9109c4aa6b6795bf5139aec59`, Task count 1, ContextPackage count 1,
generation revision 1 and one Run
`run_80d3810197bd43f4ad0149719b33739b` in state CREATED. Generation selection
was explicit; context restored to
`context_ca242ef4198f4442b7ab27c53ccfc725`; no auto-begin, auto-latest
selection, duplicate reconnect Run, runtime-readiness inference, external send
or live provider was observed. The archived Project retained readable history
and exact controls while disabling new work.

## Superseded history

The pre-repair checkpoint's 24 cancellation failures were stale assertions
expecting zero evidence rows. Repair #26 updates the oracle to require one
`runtime.routing_policy` audit and zero non-policy evidence; the final
targeted and full Core runs passed. The earlier three backup failures caused
by a non-system custom basetemp are superseded by the final system-temp-root
run. No raw hash is asserted here for a superseded run.

No command in this receipt performed a remote push, merge, release/tag, D1b
work, MCF adoption, Human product acceptance, production-database migration
or live-provider/external-egress action.
