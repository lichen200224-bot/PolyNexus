# 加強版收斂文件 Fresh Independent Review 契約

Date: 2026-09-15 (Asia/Taipei)
Task: `ENHANCED-DELIVERY-REPLAN-01`
Status: `REVIEW_SPECIFICATION / INDEPENDENT_REVIEW_NOT_RUN`
Writer: ChatGPT planning/documentation context
Review subject: exact remote candidate on `planning/enhanced-runtime-control-plane`
Product version: `UNCHANGED`

## 1. Reviewer role

Reviewer 必須不是本文件 patch Writer。Review mode: `READ_ONLY / EXACT_SHA / REMOTE_TRUTH / SOURCE_TO_DELIVERY`。

Reviewer 不修改受審 candidate、不修改 product source、不替 Writer 修文件、不自造 Human 決議。若發現問題，輸出 finding 給 documentation Writer，修復形成新 SHA 再重驗。

## 2. Remote / ancestry checks

Review 開始時必須重新取得 canonical remote：`lichen200224-bot/PolyNexus`。

驗證：

- review branch exact tip SHA;
- branch base/ancestry from current D1B source `e9538f328f409e2cb7d6868a8b79cc33ba4bdd87`, unless remote truth proves an intentionally documented newer non-product-doc parent;
- candidate changed paths are documentation/governance only; no product source/tests/migrations/dependencies are silently modified;
- no force/history rewrite/default/protection/release side effect;
- current refs used in `CURRENT_PRODUCT_STATE.md` still match remote or drift is explicitly reconciled.

## 3. Mandatory semantic checks

| ID | Required check |
|---|---|
| ER-01 | `CURRENT_PRODUCT_STATE.md` separates accepted, technical-only, rejected and historical planning states without inflating any status |
| ER-02 | D1B `e9538...`, B01 `ca85d22...`, rejected MCF `030890...`, governance/planning refs are correctly characterized against actual source/evidence |
| ER-03 | new plan does not add/redefine PN/frozen product requirements; D2b/D3/D4/T1/T2 map to existing FD responsibilities |
| ER-04 | Strategic Runtime Fleet includes Codex/OpenCode/Gemini CLI/Claude Code/Antigravity but does not claim equal capabilities or unsupported integration surfaces |
| ER-05 | OpenCode/Gemini ACP reuse and Claude/Antigravity multi-transport strategy preserve Core lifecycle/policy/Evidence/Human authority |
| ER-06 | rejected `030890...` MCF candidate cannot be merged/accepted by wording; useful ideas may only be re-derived on current lineage |
| ER-07 | `TaskControlSnapshot` is a non-persistent projection and does not become a second execution/source-of-truth domain |
| ER-08 | Council/Workflow plan reuses existing Council/Run/Context/Artifact/Evidence contracts; no duplicate AgentSession/AgentMessage/Handoff authority introduced |
| ER-09 | Runtime capability/maturity model is truthful: `UNKNOWN/UNSUPPORTED/ENVIRONMENT_BLOCKED/ResumeMode.NONE` remain valid outcomes |
| ER-10 | no silent runtime fallback or post-dispatch rebinding; actual Run binding remains immutable |
| ER-11 | Codex sole Writer/Test Executor and ChatGPT independent Product Acceptance roles are unambiguous; Codex self-PASS cannot promote a candidate |
| ER-12 | automatic continuation after ChatGPT PASS is bounded to already approved scope and does not authorize architecture/security/scope/release exceptions |
| ER-13 | Human intervention target of one final UAT is compatible with Human-only trust/auth decisions; provider login/architecture exceptions remain explicit conditional gates |
| ER-14 | final UAT covers Control Plane, five-runtime Fleet visibility, multi-agent Golden flows, failure/retry, Candidate/Human exact-view, B01 closure and restore/P0 without converting technical rehearsal into Human acceptance |
| ER-15 | WebSocket/dynamic router/plugin marketplace and other deferred items are not silently required unless authoritative source already requires them |
| ER-16 | START_HERE/AGENTS/docs37/GOAL_PLAN/EXECUTION_CONTRACT/CODEX_HANDOFF/RUNTIME/UX/UAT all route consistently to the new task/branch and do not reactivate stale PREP routing |
| ER-17 | no product version bump, frozen Golden rewrite, acceptance-history rewrite or security weakening is introduced by documentation wording |

## 4. Existing source/frozen closure

This replan is a delivery/routing delta, not a rewrite of `FEATURE_SCOPE_MATRIX`, frozen Track A, formal requirements or historical evidence. Reviewer must sample/trace the affected existing responsibilities:

- FD-06/07/08/19 for Runtime Fleet;
- FD-15/16 for Council/Workflow;
- FD-18 for Control Plane/UX;
- FD-21/22 for SIT/Delivery/Governance;
- FD-10/12/13/14 where policy/Evidence/Human semantics are referenced.

If new wording changes a frozen semantic instead of changing execution order/presentation, that is a MAJOR/BLOCKER and requires repair/change control.

## 5. Mechanical checks

When environment permits, record actual commands/exits for:

- remote branch/ref verification;
- exact base..candidate name-status/stat;
- `git diff --check`;
- protected product-tree comparison;
- internal relative-link existence for newly/modified entry documents;
- grep/check for stale active routing phrases that now conflict with the new entry path.

Planning validators may be run, but their PASS is only structural evidence and cannot replace semantic review.

## 6. Verdict

Allowed verdicts:

- `ENHANCED_REPLAN_FRESH_REVIEW_PASS` — no BLOCKER/MAJOR and the candidate is safe to use for the bounded G0/Codex start gate;
- `NEED_FIX` — documentation defects are repairable within approved direction;
- `HOLD / HUMAN_EXCEPTION_REQUIRED` — source conflict or an actual new architecture/security/scope decision is required.

A PASS authorizes preparation of the product `G0` start receipt; it does **not** itself accept B01, start Codex product writes, release software or constitute final Human product acceptance.

## 7. Required review output

Include:

```text
TASK_ID
ROLE
REVIEWED_BRANCH
REVIEWED_SHA
BASE_SHA / ANCESTRY
REMOTE_FACTS
CHANGED_PATHS / PRODUCT_TREE_PRESERVATION
ER-01..ER-17 RESULTS
ACTUAL_COMMANDS_AND_EXITS
FINDINGS
NOT_RUN / ENVIRONMENT_LIMITS
VERDICT
G0_START_GATE_RECOMMENDATION
```
