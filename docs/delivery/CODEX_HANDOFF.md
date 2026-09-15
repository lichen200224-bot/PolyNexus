# Codex 交接與安全啟動

Date: 2026-09-15 (Asia/Taipei)
Task: `ENHANCED-DELIVERY-REPLAN-01`
Status: `GATED_HANDOFF / HUMAN_DIRECTION_APPROVED / PRODUCT_START_AFTER_FRESH_DOC_REVIEW`
Product version: `UNCHANGED`

本文件是正式產品 Controller/Writer 的入口。Human 已批准後續加強版方向與「Codex 全開發測試 -> ChatGPT 獨立驗收 -> PASS 自動續行」模式，但本 docs patch 仍需 fresh independent documentation/design review；在該 review PASS 前不得開始新的產品修改。

## 1. Canonical entry

Repository: `lichen200224-bot/PolyNexus`

Documentation branch for this replan:

`planning/enhanced-runtime-control-plane`

Start by reading in this order:

1. `AGENTS.md`;
2. `docs/37_CURRENT_ROUTING_INDEX.md`;
3. `docs/delivery/START_HERE.md`;
4. `docs/delivery/CURRENT_PRODUCT_STATE.md`;
5. `docs/delivery/STRATEGIC_RUNTIME_FLEET.md`;
6. `docs/delivery/GOAL_PLAN.md`;
7. `docs/delivery/EXECUTION_CONTRACT.md`;
8. relevant existing FEATURE/REQUIREMENTS/source/frozen contracts for the assigned unit;
9. exact fresh documentation review receipt.

Do not route from stale PREP/HOLD/NEXT_GOAL text in historical copied files.

## 2. Current product facts that must be reverified remotely

Expected known refs at the time this plan was written:

```text
current D1B/default product route:
  e9538f328f409e2cb7d6868a8b79cc33ba4bdd87

B01 technical candidate:
  codex/product-b01-tech
  ca85d22c44062d2856ab037a1ee1556ea26c70cc

rejected old MCF-02 candidate:
  feature/mcf-02-opencode-acp-runtime
  030890b30160f1063ac2cef1d36705a9ea70bddb
```

These values are expected inputs, not permission to skip remote read-back. If remote truth differs, report exact drift before writing.

## 3. First product unit — G0

Before D2b, perform read-only reconciliation of B01/current product state.

Required outcome:

- exact remote SHA / ancestry / diff;
- verify B01 technical evidence and fresh engineering-review receipt;
- verify no unexpected product-source drift;
- select exact safe technical base;
- preserve the distinction between D1B Human-accepted bounded scope and B01 `PENDING_FINAL_HUMAN_UAT`;
- confirm rejected `030890b3...` is not adopted.

If B01 needs ordinary same-scope repair, Codex may repair it after the start receipt and publish a new candidate. Do not ask Human for a normal bugfix approval.

## 4. Product execution order

After G0 acceptance:

```text
D2B-01 OpenCode ACP
D2B-02 Gemini CLI ACP
D2B-03 Claude Code structured/headless
D2B-04 Antigravity headless
D2B-05 Runtime Fleet Doctor
D3 Multi-Agent Council/Workflow
D4 Unified Work Control Plane
D4-NEXT source-required remainder only
T1 Functional Golden SIT
T2 Failure/Security SIT
DELIVERY
READY_FOR_HUMAN_UAT
```

Detailed target contracts are in `STRATEGIC_RUNTIME_FLEET.md` and `GOAL_PLAN.md`.

## 5. Role contract

You are Codex when operating as product Writer:

`SOLE_PRODUCT_WRITER + TEST_EXECUTOR`

You may, inside the approved unit:

- inspect current code/contracts/tests;
- derive exact changed-file allowlist from the approved FD responsibility;
- implement product source/tests/migrations/docs delta;
- run UT/contract/SIT/build/live bounded target tests;
- fix ordinary same-scope defects;
- create immutable candidate commits;
- non-force push the candidate branch;
- record actual commands/cwd/exits/hash/evidence/limitations;
- hand off exact candidate to ChatGPT independent Product Acceptance Center.

You may NOT:

- final-accept your own candidate;
- weaken an oracle to make a failure pass;
- use fixture evidence as real runtime conformance;
- silently change frozen scope/security/Human trust;
- merge the rejected `030890b3...` candidate wholesale;
- force push/history rewrite/change default/protection/release/deploy;
- extract/replay vendor cookies/tokens/private sessions;
- create a second Core lifecycle/Evidence/Human authority.

## 6. ChatGPT acceptance loop

After every immutable candidate, provide an exact handoff containing:

```text
TASK_ID / UNIT
BASE_SHA
CANDIDATE_BRANCH
CANDIDATE_SHA
PARENT_SHA
CHANGED_FILES
SOURCE_SCOPE
ACTUAL_COMMANDS_AND_EXITS
TARGET/LIVE_OR_FIXTURE_EVIDENCE
NEGATIVE_EVIDENCE
SKIPPED / NOT_RUN / ENVIRONMENT_BLOCKED
KNOWN_LIMITATIONS
NEXT_UNIT
```

ChatGPT independently verifies remote truth, exact source/diff/ancestry/evidence. Do not rely on your own `PASS` claim.

- ChatGPT `PASS` + next unit already approved -> expect `AUTHORIZED_TO_CONTINUE_WITHIN_APPROVED_SCOPE`; proceed without Human response.
- ChatGPT `NEED_FIX` -> repair only the finding scope, produce a new SHA, rerun required/affected tests and resubmit.
- ChatGPT `BLOCKED/HUMAN_EXCEPTION_REQUIRED` -> preserve exact state; only the blocked action stops unless dependency forces a broader stop.

## 7. Runtime-specific constraints

### OpenCode / Gemini ACP

Build/reuse one generic bounded ACP transport. Vendor adapters remain thin and declare only observed capabilities. No arbitrary plugin/MCP/remote-skill enablement by default.

### Claude Code

Use only supported structured/headless execution or independently justified supported bridge. Preserve Core workspace/policy/result/Evidence authority.

### Antigravity

Use supported headless machine-readable output. Outer exit `0` or vendor `SUCCESS` does not prove work completion; validate expected postcondition/result before import.

### All targets

No silent fallback or runtime rebinding. `ResumeMode.NONE`, `UNSUPPORTED`, `UNKNOWN` and `ENVIRONMENT_BLOCKED` are valid truthful outcomes.

## 8. Human exception rules

Do not stop for ordinary bugs. Request Human only when the next action requires:

- official provider login / Windows Hello that cannot be safely reused;
- frozen semantic/new authority/security boundary change;
- unsupported/private vendor integration or credential/session takeover;
- material new payment/egress/data exposure;
- production DB action outside approved UAT/migration path;
- force/history/default/protection/release/deploy action;
- resolution of an actual ambiguous product requirement that changes outcome.

Expected normal remaining Human involvement is one concentrated final UAT.

## 9. Final output

Your product development endpoint is:

`READY_FOR_HUMAN_UAT`

Do not claim `HUMAN_ACCEPTED`, `RELEASED` or `PRODUCTION_READY`.

Final Human scenarios are in `UAT_AND_RELEASE.md`. UAT defects in the same approved scope return to Codex for repair -> new candidate -> ChatGPT re-review; only the affected Human scenario needs rerun.
