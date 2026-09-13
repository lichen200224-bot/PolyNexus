# D2a bounded technical checkpoint — 2026-09-13

Role: `CODEX_PRODUCT_D2A_CONTROLLER`

Status: `D2A_TECHNICAL_CHECKPOINT / REAL_TARGET_GATE_BLOCKED / REVIEW_PENDING`

This candidate starts exactly at Human-accepted D1a commit
`4cc88feab4097481fa4725c659521c7431794d46` with tree
`10d0548bcd85310a8686e6e933016274c6840419`. It is isolated in branch
`codex/product-d2a`. No push, merge, tag, release, D1b, B01, or D2b action was
performed.

## Case map

| Area | Implemented / exercised | Result |
| --- | --- | --- |
| FD-05 lifecycle and binding | Existing binding-first transaction and immutable snapshot path retained; private adapter identity binding occurs before workflow dispatch; timeout/cancel cleanup targets remain distinct; `ResumeMode.NONE` rejects resume | Targeted regression pass; native resume is intentionally not claimed |
| FD-05 process ownership | Existing Windows controlled Job Object path exercised with a real root plus retained child; cleanup, late abort isolation, and registry-loss fail-closed cases exercised; child environment is explicitly allowlisted and bounded stdout/stderr/process facts are retained | Pass for the controlled ownership contract |
| FD-05 reconciliation | Existing restart reconciliation path retained; cleanup target hint is applied on restart cleanup; no resubmission path added | Targeted reconciliation regression pass |
| FD-06 static module | `module.codex` is statically registered through the existing `RuntimeModuleBridge` into the existing `RuntimeRegistry`; module disable isolates Codex while reference remains available | D2a contract tests and MCF-01 regression pass |
| FD-07 external envelope | Immutable run/task/project envelope, Core-created per-Run `PROJECTED_STAGING`, independent input/output allowlists, executable/config/policy fingerprints, provider-model vs agent-extension egress declarations, launch/import quiescence, stable output observation, and Core-owned blob import | D2a contract tests pass (`11 passed`, `1 skipped` on Windows symlink privilege) |
| FD-07 negative paths | Traversal/credential-like argument rejection, non-allowlisted source change rejection, output mutation between two import reads rejection | Pass in D2a contract tests |
| FD-08 W2 real target | Feasibility first, then installed `codex` CLI attempt in synthetic managed worktree | Blocked by CLI API transport/network permission before model execution; no real source write or target cleanup evidence |

## Changed source

The fresh implementation is confined to:

- `services/core/src/polynexus_core/runtime/external_contracts.py`
- `services/core/src/polynexus_core/runtime/codex_exec.py`
- `services/core/src/polynexus_core/runtime/composition.py`
- `services/core/src/polynexus_core/runtime/registry.py`
- `services/core/src/polynexus_core/runtime/supervisor.py`
- `services/core/src/polynexus_core/runtime/reconciliation.py`
- `services/core/src/polynexus_core/execution_service.py`
- `services/core/src/polynexus_core/persistence/generation.py`
- `services/core/src/polynexus_core/api/generations.py`
- `services/core/src/polynexus_core/workspace/ownership.py`
- `services/core/tests/test_d2a_external_runtime.py`

The public `RuntimeAdapter` method set, Run schema, migrations, and binding
insert-once behavior were not changed. `PrepareInput.output_paths` is an
optional additive API field so the durable generation record can keep input
and output allowlists distinct; existing callers retain the selected-path
fallback.

## Commands and exits

All commands below ran in the D2a lane unless another cwd is shown.

| Purpose | Command / cwd | Exit |
| --- | --- | ---: |
| Python compile | `D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -m compileall -q services/core/src/polynexus_core services/core/tests` / lane root | `0` |
| D2a contract tests | `...python.exe -m pytest -q --basetemp <lane-temp> tests/test_d2a_external_runtime.py` / `services/core` | `0` (`11 passed`, `1 skipped` on Windows symlink privilege) |
| D1a runtime/module/reconciliation/policy regression | `...pytest -q --basetemp <lane-temp> tests/test_runtime_skeleton.py tests/test_mcf01_static_modules.py tests/test_g16_runtime_selection_policy.py tests/test_g14_runtime_reconciliation.py tests/test_d1a_policy_secret.py` / `services/core` | `0` |
| Ownership and real controlled Job regression | `...pytest -q --basetemp <lane-temp> tests/test_d1a_generation_ownership.py::test_real_owned_tree_retry_late_abort_and_registry_loss tests/test_d1a_generation_ownership.py::test_public_rest_execution_controls_real_job_and_terminal_cancel_is_inert` / `services/core` | `0` (`2 passed`) |
| Failure/timeout cleanup regression | `...pytest -q --basetemp <lane-temp> tests/test_cp06_wp28_failure_injection.py tests/test_wp24_resource_guards.py` / `services/core` | `0` (`10 passed`) |
| Remediation affected regression | `...pytest -q --basetemp <lane-temp> tests/test_d2a_external_runtime.py tests/test_d1a_generation_ownership.py::<real-job cases> tests/test_g16_runtime_selection_policy.py tests/test_mcf01_static_modules.py tests/test_g14_runtime_reconciliation.py tests/test_cp06_wp28_failure_injection.py tests/test_g15_runtime_output_redaction.py` / `services/core` | `0` (all collected cases passed; one symlink case skipped) |
| Codex/runtime regression | `...pytest -q --basetemp <lane-temp> tests/test_wp14_codex_runtime.py tests/test_wp14b_runtime_binding.py tests/test_wp16_runtime_doctor.py tests/test_runtime_skeleton.py` / `services/core` | `0` (all collected cases passed; warnings only) |
| Full Core regression after remediation | `TEMP/TMP=<lane>\\d2a-full-core4-root; ...python.exe -m pytest -q --basetemp <lane>\\d2a-full-core4-root\\pytest tests` / `services/core` | `0` (all Core tests passed; warnings only) |
| Web dependency install | `npm ci --ignore-scripts --no-audit --no-fund --fetch-timeout=15000 --fetch-retries=1 --cache <lane>\\d2a-npm-cache-final` / `apps/web` | `0` (90 packages) |
| Web tests | `npm test -- --run` / `apps/web` | `0` (`4 files`, `94 tests`) |
| Web build | `npm run build` / `apps/web` | `0` |
| START scope validator | `...python.exe checks/validate_feature_scope.py` / `docs/delivery` | `0` (`PASS_PLANNING_STRUCTURE_ONLY`) |
| START validator selftest | `...python.exe checks/selftest_feature_scope.py` / `docs/delivery` | `0` (`PASS`, 27 cases) |
| Initial pytest attempt | incorrect `services/core/tests/...` paths while cwd was `services/core` | `1` (path error; not a test assertion) |
| Initial pytest environment attempt | default pytest temp root under `C:\Users\shawn\AppData\Local\Temp\pytest-of-shawn` | `1` (`PermissionError [WinError 5]` during fixture setup) |

The corrected `--basetemp` rerun removed the environment-temp false failure;
the affected tests then passed as recorded above.

## First independent review and remediation

The first fresh read-only review of commit `9f0f5e1d8c7b86594e715b76e01f1765ae56313a`
returned `FAIL_REVIEW` with eight P1 findings. The current uncommitted revision
addresses those findings as follows: separate input/output scopes and permit an
empty input set with a non-empty approved output set; classify runtime-managed
provider-model egress as external before policy evaluation; build only a
Core-owned projected staging; make envelope mappings/fingerprints immutable and
revalidated; enforce input quiescence at launch/import; pass a non-secret child
environment allowlist; require verified timeout cleanup for runtime-managed
dispatch; and retain bounded argv/cwd/exit/signal/process/stdout/stderr plus
version/auth/provenance evidence. A second independent review is required for
the resulting immutable candidate.

The second fresh read-only review of candidate `e19ff4c555ed03630102502a7108c3f09fd3024d`
returned `FAIL_REVIEW` with P0=0 and P1=4. It confirmed candidate identity,
ancestry, MCF-02 non-adoption, and the static module bridge, while identifying
three implementation gaps in addition to the still-blocking real-target gate:
synthetic rather than resolved effective-config/policy fingerprints, incomplete
nested reparse containment, and acceptance of exit-zero output without parsing
the required `--json` normalized result. It also noted that execution service
was still assigning the same durable selected-path set to both input and output.

The post-review remediation in this lane adds an actual Codex configuration
preflight snapshot (executable/flags/child-environment digests with explicit
`NONE` plugin/MCP/skill state), binds the persisted route-policy audit digest
into the immutable envelope, checks every existing relative-path ancestor for
reparse/symlink escape, adds durable independent `output_paths`, and requires
bounded JSONL terminal-result validation before importing a diff. Malformed,
empty, failed, or drifted results fail closed. A new immutable candidate and a
new fresh independent review are still required.

The fresh review of candidate `144f4534930b455379ddb3fbbd74bfd9e62818c8`
then returned `FAIL_REVIEW` with P0=0 and P1=2. It found that an existing
output-only file was still copied into the projection (write scope therefore
also granted read access), and that projected staging was created outside the
Supervisor boundary, so a pre-launch staging failure could escape before a
truthful terminal Run state.

The follow-up remediation now copies only input bytes and creates empty
Core-owned placeholders for output-only paths; an executor must replace the
placeholder to produce an importable diff. Per-Run staging creation moved into
the adapter `create_run` operation, which is already bounded and lifecycle-
owned by `RunSupervisor`. Only the Codex adapter's explicit projection
preflight proof is treated as verified no-effect cleanup; generic adapter
create failures retain the existing unknown-ownership behavior. The
output-only and pre-launch failure cases are covered by D2a tests. A new
immutable candidate and fresh review remain required, and the Windows reparse
test remains skipped where symlink creation is unavailable.

## Real Codex feasibility evidence

Fixture cwd:
`C:\Users\shawn\OneDrive\文件\PONYNEXUS\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\codex-managed-worktree`

Fixture baseline:

- Git `HEAD`: `99e204e79d27b879b41a8e0d37e51052499d3196`
- Git tree: `ae3cb6f9ce3fee3eec09b7d1fcaad21608141f6d`
- `bug.py` Git blob before/after: `4564ab261c7570752a00bfe7f281a945e5fcf951`
- `bug.py` filesystem SHA-256 before/after: `FFC63EA42518CA28CBB11871A9480F74AD278991E31E421C6AC653747D62F80F`
- post-attempt source status: no tracked source diff; only pytest-generated `__pycache__/` was observed

Baseline command, cwd fixture:

```text
D:\AI學習教材\PolyNexus\.venv\Scripts\python.exe -m pytest -q
exit=1 (expected synthetic assertion: 41 != 42)
```

First CLI command used `--approve-for-me` together with `--sandbox
workspace-write`; Codex rejected the incompatible flag combination before a
turn (`exit=1`). This was retained as a negative command result, not an
executor run.

Second actual executor command, cwd lane root, targeted the managed fixture:

```text
codex exec --ephemeral --ignore-user-config --cd 'C:\Users\shawn\OneDrive\文件\PONYNEXUS\d2a-worktree\artifacts\verification\d2a-20260913\fixtures\codex-managed-worktree' --sandbox workspace-write --json 'Work only in this synthetic repository. Fix the failing test by editing bug.py only so answer() returns 42. Do not modify test_bug.py, .git metadata, or any file outside this repository. Do not access parent directories, credentials, environment secrets, network services, or user repositories. Run the focused test after the edit and report only the changed file, test result, and a concise summary.'
exit=1
```

The CLI created a local CLI thread but failed before model/tool execution on
the `wss://api.openai.com/v1/responses` transport with Windows socket access
denied (`10013`), then its bounded HTTP fallback also failed. It was stopped
with Ctrl-C; no source change, result, cancel proof, timeout proof, or target
child/grandchild cleanup proof was produced. Login credentials were not read or
exported, and no fallback executor was silently used.

Therefore FD-08 real-target acceptance remains `BLOCKED / NOT PASS`.

## Controlled process-tree evidence

The real controlled ownership test recorded two retained process handles per
generation. Generation 1 started PID `33968` (handle `916`) and PID `15252`
(handle `444`), both initially `exit=259, stopped=false`; final cleanup recorded
`exit=1, stopped=true` for both. Generation 2 started PID `32332` (handle
`196`) and PID `17112` (handle `1260`), both initially `exit=259,
stopped=false`; the late-abort observation preserved that state, and final
cleanup recorded `exit=1, stopped=true` for both. Test exit was `0`. This is
evidence for the controlled Job Object/ownership contract, not evidence that
the Codex CLI real target passed W2.

The D2a controlled-child case additionally observed `stdout-observed`,
`stderr-observed`, and `secret-absent` under the explicit child environment
allowlist; this is controlled-process evidence, not a real Codex W2 result.

## Acceptance boundary

This checkpoint is not `D2A_TECHNICAL_PASS`: the required real Codex target
source write, normalized result, cancel, timeout, child/grandchild cleanup,
version/auth/provenance, and real-target negative cases are not all evidenced.
Full Core/Web/build/START verification passed as recorded above. Final
`D2A_TECHNICAL_PASS` remains unavailable until the real-target gate is rerun with
an approved transport and all required real evidence exists, then a fresh
independent read-only reviewer reports no P0/P1 finding. The first reviewer had
P1 findings; it is not reused as the final acceptance reviewer.
