# G21 browser evidence harness commands

Timestamp: 2026-09-02 Asia/Taipei. The final run used Chrome 152.0.7977.65 in an
isolated headless profile and a loopback HTTPS synthetic fixture with a SAN
certificate for 127.0.0.1 and localhost. No live vendor
traffic, login, credential, cookie, token, cloud request, or external send was
used.

The journey and failure matrix rows are in-process assertions and therefore use
`exit_code: "N/A"`. The harness itself preserves an aggregate process exit code;
the final run returned `0`.

| Exact command / check | Actual result | Exit code |
|---|---|---:|
| `node --test extensions/browser-companion/tests/test_websurface_drivers.mjs` | 9/9 tests passed | 0 |
| `node artifacts/verification/g21-browser-20260902/run-g21-browser-evidence.mjs --artifact=C:\\Users\\hikar\\.codex\\visualizations\\2026\\09\\01\\01a05dc0-65d4-7db3-98f4-f2d2c6fbd525\\g21-isolated\\artifacts\\verification\\g21-browser-20260902 --extension=C:\\Users\\hikar\\.codex\\visualizations\\2026\\09\\01\\01a05dc0-65d4-7db3-98f4-f2d2c6fbd525\\g21-isolated\\extensions\\browser-companion --pfx=C:\\Users\\hikar\\AppData\\Local\\Temp\\pn-g21-browser-20260902\\fixture.pfx --port=9252` | 3/3 golden, 28/28 failure assertions, HTTPS fixture, actual service-worker listener dispatch, observed external requests 0, cleanup PASS | 0 |
| `git diff --check` | no whitespace errors | 0 |
| protected-path/scope allowlist validator (read-only PowerShell; changed files restricted to G21 harness, artifacts, task, handoff, and project-state paths) | allowlist PASS | 0 |
| `C:\\temp_pn_venv2\\Scripts\\python.exe scripts/validate_baseline.py` in sandbox | process creation blocked by environment | 1 |
| `C:\\temp_pn_venv2\\Scripts\\python.exe scripts/validate_baseline.py` under approved elevation | 11 required files; workflows and MV3 manifest valid | 0 |
| `powershell -NoProfile -ExecutionPolicy Bypass -File .\\tools\\validate-polynexus-governance.ps1 .` | governance files, manifest, JSON, and protected-path exclusions valid | 0 |

The native browser-loaded MV3 service-worker target was unavailable in the
stable lane. Required message coverage was therefore executed through the
actual `extensions/browser-companion/src/service-worker.js` listener loaded in
an isolated equivalent extension-dispatch shim; native browser-worker dispatch
remains `UNVERIFIED`.
