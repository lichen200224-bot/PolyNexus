# G21 browser verification commands

Timestamp: 2026-09-02 Asia/Taipei. All browser commands used Chrome 152.0.7977.65 with a temporary profile outside this artifact directory and an HTTPS fixture host-mapped to `127.0.0.1`. No live vendor traffic, login, cookie, token, user data, or external send was used.

| Command / check | Result | Exit code |
|---|---|---:|
| `git ls-remote D:\\GitBackup\\PolyNexus_Backup.git refs/heads/feature/g20-web-reproducible-dependency-test-build-gate` | exact G20 SHA `48062f1cae608785a39539e1a7bfca5d6726a92e` | 0 |
| isolated clone + `git switch -c feature/g21-wp21-real-browser-journey-failure-path` | clean lane from exact G20 SHA | 0 |
| fresh Chrome launch with `--load-extension` and host mapping | Chrome CDP ready; MV3 service worker target observed | 0 |
| `node artifacts/verification/g21-browser-20260902/run-g21-browser-evidence.mjs ...` | 3/3 golden journeys; 22/22 failure paths; 0 pages after cleanup | 0 |
| `node --test extensions/browser-companion/tests/test_websurface_drivers.mjs` | 9/9 passed | 0 |
| `npm ci` in G21 `apps/web` using default npm cache | OS cache/registry `EPERM`/`EACCES`; not a product failure | 1 |
| `npm ci` in G21 `apps/web` using task-specific cache | registry fetches denied with npm `Exit handler never called` | 1 |
| `npm test` in G21 `apps/web` with lockfile-matched restored dependency tree from G20 clean clone | Vitest 4.1.10; 80/80 passed | 0 |
| `npm run build` in G21 `apps/web` with the same restored dependency tree | Vite 8.2.0; 23 modules transformed; production assets emitted | 0 |
| `C:/temp_pn_venv2/Scripts/python.exe scripts/validate_baseline.py` | launcher process creation blocked in sandbox | 101 |
| same baseline command under approved elevation | 11 required files; workflows valid; MV3 valid | 0 |
| `powershell -NoProfile -ExecutionPolicy Bypass -File .\\tools\\validate-polynexus-governance.ps1 .` | governance files, manifest, JSON, protected exclusions valid | 0 |
| `git diff --check` | required final diff hygiene check | 0 |

The temporary certificate, npm cache, browser profiles, and Chrome process trees were removed after verification. The authoritative artifact inventory and hashes are in `SHA256SUMS.txt`.
