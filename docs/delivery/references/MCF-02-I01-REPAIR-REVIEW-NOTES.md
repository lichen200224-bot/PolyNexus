# MCF-02-I01 repair — independent review notes

## Status and authority

- TASK_ID: `MCF-02-I01-OPENCODE-ACP-EXTERNAL-RUNTIME-FOUNDATION` / F001–F005 repair.
- STATUS: `WRITER_REPAIR_CANDIDATE`; independent acceptance remains pending.
- BRANCH: `feature/mcf-02-opencode-acp-runtime`.
- Architecture predecessor: `b317e5d70b2be385f6cf45cdbb8fe21d788f3b02`.
- Historical NEED_FIX implementation: `18fab2b092911d9dd1f95eccda29b52dfaedff7d`; retained unchanged in ancestry.
- Human subsequently authorized the bounded repair approach: existing Core policy may authorize its own allowed routes; Human-required routes stay denied under D11 Option C. This does not introduce verified Human attribution.
- Target remains OpenCode ACP v1 only. No live execution, vendor authentication, canonical promotion, migration, second target, or plugin platform work.

## Finding-to-evidence map

| Finding | Implementation | Independent reproduction in focused tests |
|---|---|---|
| F001 | Registry stores `ExternalRuntimeDefinition` and factory only. ExecutionService calls `prepare_external` with the actual Run/Task/ContextPackage, creates a fresh staging root, and commits the descriptor's envelope digest through the existing snapshot `adapter_version` before constructing the adapter. Prepared state lives transiently in ExecutionService, keyed by Run. | `test_same_profile_two_runs_two_projects_have_durable_isolated_envelopes` runs two real ExecutionService paths against SQLite, for both same-project and different-project contexts. A separate DB connection verifies committed bindings before factory calls; cross-project staging substitution is rejected. |
| F002 | Operator policy pins the expected resolved-config digest in the envelope. Readiness observes the exact executable through `debug config`, in ACP's cwd/environment, compares strict normalized output and revalidates the envelope. Source inspection runs before and after the production resolver. Raw resolver output stays in memory; only the digest is exposed as observation. | `test_default_resolver_uses_bound_binary_and_identical_cwd_environment`, `test_unknown_source_inventory_does_not_launch_resolver`, `test_source_inventory_rejects_expansion_before_resolver`, `test_final_resolver_expansion_denies_readiness_and_launch`, and malformed/duplicate/oversize output tests. |
| F003 | Removed `provider_model_approved`. `RunScopedPolicyAuthorization` correlates Run, Task, Project, destination, envelope, expiry and a policy decision reference. Dispatch recomputes D05 policy. An authorization record cannot upgrade APPROVAL_REQUIRED. Evidence says `CORE_POLICY_ALLOWED`, never `HUMAN_APPROVED`. | `test_policy_authorization_is_run_scoped_and_never_infers_human_approval`: other Run/Task/Project/destination/envelope, missing reference, expiration, boolean and confidential/Human-required policy all deny before ACP launch. |
| F004 | Option B: `permission_requests=False`; resolved permission policy is exactly deny-all. Incoming JSON-RPC requests are distinguished from responses and rejected even when the id equals the active request id. No runtime permission decision is auto-approved. | `test_option_b_incoming_permission_request_never_becomes_response`: allow/reject options, stale session and malformed params all fail closed and permit cleanup. No permission callback ALLOW is claimed. |
| F005 | A successful turn must stop owned work before reporting COMPLETED. Failed cleanup retains the process reference and goes through supervisor failure cleanup. Artifact import happens only after quiescence, validates containment/size/hash/re-read, then creates a Core-owned read-only content copy and hashes it again. | `test_artifact_changed_during_process_cleanup_rejects_original_claim`, `test_artifact_mutation_after_first_read_is_rejected`, `test_imported_artifact_storage_is_core_snapshot_not_staging`, plus existing cleanup/orphan tests. |

Tests are in `services/core/tests/test_mcf02_external_runtime_contract.py` and `services/core/tests/test_mcf02_opencode_acp_runtime.py`. Fake processes/resolver fixtures prove boundary behavior, not live OpenCode conformance. Reviewers should inspect assertions and rerun the candidate, rather than accept these descriptions as PASS evidence.

## Effective-config support and limits

Official OpenCode documentation describes merged remote, global, custom, project, `.opencode`, inline and managed sources; managed settings override inline settings. This is why the repair does not treat `OPENCODE_CONFIG_CONTENT` alone as proof. Source: [OpenCode config documentation](https://opencode.ai/docs/config/), inspected 2026-09-12.

The official resolver command prints its resolved config through `debug config`: [OpenCode debug config source](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/cli/cmd/debug/config.ts), inspected 2026-09-12. These moving upstream sources are research references, not a pinned live compatibility certificate.

Production preflight currently implements a deliberately closed config surface:

- Only explicit deny-all permissions, empty plugins/MCP/agents/commands/instructions/skill sources, and disabled updates/sharing/snapshots/LSP/formatters pass the exact parser.
- An isolated per-Run home is used; operator login stores and remote-configuration credentials are not copied. Parent/project and managed sources are rejected before resolver execution. Global config/plugin/MCP/auth state in the isolated home is rejected.
- Windows and Linux have source-location inspection. Unknown platforms, including unimplemented macOS managed-preference resolution, remain not ready.
- Additional resolved fields, runtime-generated state, missing fields, unsupported resolver output and unknown sources deny readiness. A real OpenCode release may therefore be rejected. No supported version/model/provider configuration has been live-accepted in this repair.
- Test injection of a resolver is an internal deterministic seam, not an operator bypass or public API. Production uses the bound executable; fixtures do not prove a real installation's source inventory or behavior.

## D11 preservation and future development

`policy_decision_ref` is an audit correlation hash, not a signature, Human attestation or authentication token. Its inputs are Core composition policy inputs; vendor messages cannot issue or override it. Existing D05 policy is recomputed at dispatch. A caller cannot turn a confidential, LOCAL_ONLY, restricted, untrusted or side-effect route into approval merely by supplying a reference.

Under D11, a Human evidence record/reference alone still cannot authorize dispatch. `HUMAN_DECISION` and `APPROVAL_REQUIRED` remain pending/denied. This repair does not add another governance authority or claim that the chat's development/push authorization approves a product Run.

Future work can continue through the following existing seams:

1. Runtime compatibility work pins one executable version and validates its actual resolved config/source inventory against explicit policy. Any expansion of model/provider/auth/config support needs its own focused safety evidence; it must not loosen the parser silently.
2. Human approval work defines an approved principal/attestation boundary in Core. It can then supply a verified, scoped decision to the dispatch gate; registry ownership, Run identity, envelope materialization and immutable snapshot semantics need not be replaced.
3. ACP permission callbacks remain disabled until explicitly implemented through that Core authorization boundary. No fake callback acceptance should be counted as future live evidence.

This keeps native/deterministic Core development independent of external workspaces. It does **not** promise that Human-dependent live milestones have no dependency or delay. First live acceptance must state whether it requires Human approval, credentials, tools or config fields outside this bounded slice before scheduling execution.

## Validation record

Fresh results and actual exits are recorded in `docs/12_HANDOFF_CURRENT.md`. Full Core includes existing migration tests against temporary SQLite only; no schema/migration was changed. Earlier NEED_FIX candidate results remain historical and are not reused as this repair's evidence.

Required commands, with an isolated writable pytest basetemp under TEMP:

```text
python -m pytest services/core/tests/test_mcf02_external_runtime_contract.py services/core/tests/test_mcf02_opencode_acp_runtime.py
python -m pytest services/core/tests/test_runtime_skeleton.py services/core/tests/test_mcf01_static_modules.py services/core/tests/test_wp14b_runtime_binding.py services/core/tests/test_wp14_codex_runtime.py services/core/tests/test_wp15_opencode_runtime.py services/core/tests/test_wp16_runtime_doctor.py
cd services/core
python -m pytest -rs
cd ../..
python -B scripts/validate_baseline.py
powershell -NoProfile -ExecutionPolicy Bypass -File tools/validate-polynexus-governance.ps1 .
git diff --check
```

The independent reviewer owns finding closure and implementation acceptance. Writer publication fixes a review checkpoint only.
