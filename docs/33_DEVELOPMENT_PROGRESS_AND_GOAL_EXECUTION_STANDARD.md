# PolyNexus Development Progress and Goal Execution Standard

## Current routing override — G29 external work deferred to G30 (2026-09-03)

By the current Human instruction, G29 performs no live external vendor run.
Its sanitized operator materials and preflight evidence are carried forward to
G30, where authorized Human-operated WP-20 verification must occur before the
final 100-point reconciliation. The historical G29 external-verification
procedure below remains the evidence standard for that deferred work; it does
not authorize starting G30, login, credential handling, automatic send, or Git
operations. `G29_STATUS=HANDOFF_COMPLETE / DEFERRED_TO_G30`; current accepted score remains
`95/100` until valid WP-20 evidence is accepted.

## 1. Decision status

- Status: `HUMAN_CONFIRMED / READY_FOR_CHECKPOINT`
- Decision date: 2026-09-02 (Asia/Taipei)
- Program: G24–G30 development completion and acceptance reconciliation
- Recommended Codex profile: `gpt-5.6-luna`, reasoning effort `high`
- Starting accepted product SHA:
  `0eb56a986e97a45854bd6ddd419c114845ce51f4`
- Current accepted development progress: `59/100`
- Architecture impact: `NONE`
- Scope deviation: `NONE`

This standard governs development progress accounting and the G24–G30 goal
program. It does not alter Domain models, Runtime Contracts, workflow semantics,
evidence types, persistence schemas, ADR-001–011, or product maturity claims.

## 2. Development-only 100-point model

Competition preparation and delivery are not required PolyNexus development
progress. Competition material is retained as a separate Human-owned note track:

```text
COMPETITION_TRACK=NOTE_ONLY_NON_SCORING
DELIVERY_OWNER=HUMAN
PROJECT_PROGRESS_IMPACT=NONE
```

The development denominator remains 100 by reallocating the former five
competition points to unfinished product work. Historical accepted points are
not removed and no unfinished work gains points solely from reallocation.

| Checkpoint | Weight | Item allocation |
|---|---:|---|
| CP-00 Governance and baseline | 8 | Existing accepted baseline: 8 |
| CP-02 First Vertical Slice | 22 | Existing accepted FVS: 22 |
| CP-03 Core Runtime | 27 | WP-11: 4; WP-12: 5; WP-13: 5; WP-14: 5; WP-15: 5; WP-16: 3 |
| CP-04 Local, Policy, and Web | 20 | WP-17: 4; WP-18: 4; WP-19: 4; WP-20: 5; WP-21: 3 |
| CP-05 Product Completion | 13 | WP-22: 3; WP-23: 2; WP-24: 2; WP-25: 1; WP-26: 2; WP-27: 3 |
| CP-06 RC and Delivery | 10 | WP-28: 2; WP-29: 2; WP-30: 2; WP-31: 1; WP-32: 3 |
| **Total** | **100** | Competition excluded |

Current accepted score:

| Checkpoint | Earned / weight | Accepted basis |
|---|---:|---|
| CP-00 | 8/8 | Baseline and governance |
| CP-02 | 22/22 | First Vertical Slice |
| CP-03 | 14/27 | WP-11, WP-12, WP-13 |
| CP-04 | 3/20 | WP-21 bounded browser evidence |
| CP-05 | 2/13 | WP-23 backup/restore/migration |
| CP-06 | 10/10 | G19/G20/G22/G23 bounded RC and delivery closeout |
| **Total** | **59/100** | 41 points remain unaccepted |

## 3. Independent item ledger

Every scored WP is managed independently. Its record must contain:

- `WP_ID`
- `CHECKPOINT`
- `POINT_WEIGHT`
- `STATUS`
- `IMPLEMENTATION_REF`
- `REVIEW_REF`
- `ACCEPTANCE_REF`
- `CHECKPOINT_SHA`
- `TEST_COMMANDS_AND_EXIT_CODES`
- `ARTIFACT_REFS`
- `KNOWN_LIMITATIONS`
- `UNVERIFIED`
- `ADR_IMPACT`
- `SCOPE_DEVIATION`

Allowed status sequence:

```text
PLANNED
IMPLEMENTING
IMPLEMENTED_PENDING_REVIEW
READY_FOR_INDEPENDENT_REVIEW
NEED_ACTION | FAIL
VERIFIED_PASS_PENDING_HUMAN
HUMAN_ACCEPTED
CHECKPOINTED
```

Only `HUMAN_ACCEPTED` or `CHECKPOINTED` earns the item's full point weight.
Partial test success, source presence, historical logs, AI opinion, or a Goal
PASS that does not identify the WP acceptance boundary earns zero for that WP.
An item may be accepted with disclosed limitations only when the acceptance
criteria explicitly allow the bounded maturity label.

Whenever a WP changes status, the same Goal must update:

1. its task document;
2. `docs/11_PROJECT_STATE.md`;
3. `docs/12_HANDOFF_CURRENT.md`;
4. `docs/28_MASTER_DEVELOPMENT_ROADMAP.md`;
5. compatibility and limitation documents when maturity changes;
6. `docs/GOAL_COMPLETION_CONTROL_PANEL.md`;
7. `docs/GOAL_COMPLETION_CONTROL_PANEL.html`;
8. the checkpoint subtotal and project total.

## 4. Goal autonomy and Human boundary

For G24–G30, the Human authorizes Codex to continue within the Goal until the
final Goal gate. Within the exact scope, Codex may without intermediate Human
approval:

- read repository files and current evidence;
- create an isolated branch/worktree/clone from the approved exact predecessor;
- make bounded implementation and documentation changes;
- install repository-declared dependencies in the isolated lane when required;
- run deterministic tests, validators, builds, and local controlled fixtures;
- remediate findings and rerun affected gates;
- request one bounded read-only independent review context when Writer !=
  Reviewer is required;
- update the progress ledger and control panels truthfully.

This authorization does not include:

- force push, history rewrite, destructive reset/clean, branch deletion, or
  remote reconfiguration;
- access to or recording of credentials, cookies, tokens, or secret values;
- automatic external send, upload, publication, purchase, or submission;
- migration of real user data;
- new Product Scope, Domain entity, persistence boundary, or ADR decision;
- self-authentication of a Human decision under D11 Option C;
- recursive delegation to a new Goal or runtime.

If an action crosses one of these boundaries, Codex must stop that action,
preserve completed safe work, and report one exact `HUMAN_ACTION_REQUIRED`
packet. Ordinary implementation choices must not be bounced to the Human.

## 5. Single final Human gate per Goal

Codex owns analysis, implementation, testing, remediation, independent review
routing, progress updates, and preparation of the Git allowlist. The Human is
asked only at the final gate unless a non-delegable external/architecture/secret
boundary is encountered.

Required final decision block:

```text
GOAL_ID:
GOAL_RESULT: PASS | FAIL | NEED_ACTION | HUMAN_DECISION_REQUIRED
PREDECESSOR_SHA:
OUTPUT_SHA_CANDIDATE:
GOAL_SCORE_DELTA:
NEW_PROJECT_SCORE:
WP_STATUS_CHANGES:
EXACT_CHANGED_FILES:
TESTS_AND_ACTUAL_EXIT_CODES:
INDEPENDENT_REVIEW:
KNOWN_LIMITATIONS:
UNVERIFIED:
ADR_IMPACT:
SCOPE_DEVIATION:
PROPOSED_COMMIT_MESSAGE:
PUSH_REMOTE_REF:
HUMAN_FINAL_DECISION_REQUIRED:
  ACCEPT_AND_COMMIT_PUSH
  REJECT
  NEED_ACTION
```

`ACCEPT_AND_COMMIT_PUSH` is a single explicit final authorization for the listed
allowlist, commit message, branch, and non-force push target only. It does not
authorize additional files, a force push, another Goal, or remote changes. After
that decision, Codex must commit, non-force push, verify the remote exact SHA,
perform final clean-clone verification, and publish the immutable `OUTPUT_SHA`.

## 6. Start gate for every new Codex conversation

Every Goal runs in a new Codex conversation configured for `gpt-5.6-luna` with
reasoning effort `high`. Each conversation must:

1. read `AGENTS.md`, `docs/11_PROJECT_STATE.md`,
   `docs/12_HANDOFF_CURRENT.md`, this standard, and the G24–G30 routing file;
2. read only the directly relevant specifications, task files, source, tests,
   and evidence after that;
3. For G25–G30, resolve the predecessor ref from the approved remote and verify
   it equals the exact predecessor SHA recorded by the prior terminal handoff.
   G24 is the explicit exception: receive the exact planning-package SHA as
   `G24_START_SHA` in the verified planning completion result/new-task input,
   then resolve and verify that SHA against the approved remote;
4. inspect branch, HEAD, working tree, and staged state before writing;
5. preserve the protected primary dirty lane;
6. stop with `START_GATE_FAIL` if the ref/SHA/status/required files disagree.

The planning package must itself be checkpointed before G24 starts. The planning
commit does not embed its own self-referential SHA. After the exact planning
commit is non-force pushed and clean-clone verified, publish that immutable
remote SHA in the completion result and new-task input as `G24_START_SHA`; that
SHA is G24's predecessor. Until then, `G24_START_SHA` and `G24_OUTPUT_SHA` remain
pending and the G24 prompt remains `WAIT`.

## 7. Writer, reviewer, and retry rules

- One active writer at a time on the canonical continuation chain.
- Other Goal conversations may perform read-only inventory only when their start
  gate explicitly allows it.
- The writer may not label its own review independent.
- A bounded independent reviewer receives the diff, directly affected contracts,
  acceptance criteria, and targeted evidence—not an unrestricted repository dump.
- BLOCKER or MAJOR findings must be remediated and independently re-reviewed.
- Deterministic failure gets at most two bounded remediation attempts unless the
  task file defines a different limit. After repeated identical failure, report
  `NEED_ACTION` with root cause and the smallest next action.
- Never rerun completed expensive suites merely to create activity. Rerun when
  evidence is stale, affected, missing, or required by final acceptance.

## 8. Verification and score-award rules

Every scored item requires:

1. directly relevant deterministic tests with actual exit codes;
2. affected regression tests;
3. baseline and governance validation;
4. `git diff --check`;
5. scope/protected-path verification;
6. independent review when required;
7. Human final acceptance;
8. exact allowlist commit and approved non-force push;
9. remote exact-SHA verification and clean-clone verification.

No score is awarded before the Human decision. If a final push or clean clone
fails, the WP remains accepted by the Human but not `CHECKPOINTED`; the project
score ledger must explicitly state which policy determines whether accepted but
uncheckpointed points are shown. For this program, displayed formal points
require the final checkpoint, so a Git failure leaves the score delta pending.

## 9. External verification standard

Authenticated external Web verification is intentionally deferred to G29 so
internal development can reach `95/100` first. G29 is the only planned Goal that
normally requires external operator involvement.

The external operator—not Codex—owns account login and every real send action.
Codex supplies a sanitized runbook, test data, communication prompt, and report
schema. No credential value may enter chat, Git, logs, screenshots, artifacts,
or evidence.

Required G29 matrix per vendor:

- target/vendor and test-account type;
- browser and extension versions;
- live or controlled-fixture route;
- login/readiness observation;
- launch, detect, fill, user-confirmation, send, capture, normalize;
- clipboard/manual fallback;
- login expired, selector mismatch, cancelled send, timeout, and capture failure;
- external request observation;
- sanitized screenshot/trace refs;
- cleanup result;
- actual result and blocker.

Required external report:

```text
TEST_TARGET:
TEST_ACCOUNT_TYPE:
OBSERVED_AT:
EXIT_CODE: 0 | 1 | N/A
BROWSER_VERSION:
EXTENSION_VERSION:
ROUTE:
FIXTURE_OR_LIVE:
LOGIN_STATUS:
LAUNCH_RESULT:
DETECT_RESULT:
FILL_RESULT:
HUMAN_CONFIRMED_SEND:
CAPTURE_RESULT:
NORMALIZE_RESULT:
FALLBACK_RESULT:
FAILURE_PATH_RESULTS:
EXTERNAL_REQUESTS:
CLEANUP_RESULT:
SCREENSHOT_REFS:
TRACE_REFS:
SECRETS_REDACTED:
ACTUAL_RESULT:
BLOCKERS:
```

For a Human-operated observation with no local process exit code, write
`EXIT_CODE: N/A`; never invent `0` or `1` for a manual observation.

If no authorized external operator or account is available, return:

```text
G29_RESULT=NEED_EXTERNAL_ACTION
PROJECT_PROGRESS=95/100
INTERNAL_DEVELOPMENT_COMPLETE=YES
LIVE_VENDOR_VERIFICATION=BLOCKED
```

This does not invalidate accepted internal development.

## 10. G24–G30 ordered program

| Goal | Scope | Score delta | Expected total | Start gate |
|---|---|---:|---:|---|
| G24 | Development ledger and evidence reconciliation | 0 | 59 | Planning checkpoint |
| G25 | WP-14/15 Runtime adapters and WP-16 Doctor | +13 | 72 | G24 checkpoint |
| G26 | WP-17 Local, WP-18 Policy, WP-19 WebSurface | +12 | 84 | G25 checkpoint |
| G27 | WP-22 Workflow, WP-24 Guards, WP-25 Metrics | +6 | 90 | G26 checkpoint |
| G28 | WP-26 UX and WP-27 deterministic feature freeze | +5 | 95 | G27 checkpoint |
| G29 | WP-20 authenticated external Web verification | +5 | 100 | G28 checkpoint |
| G30 | Final 100-point release reconciliation | 0 | Confirm 100 | G29 checkpoint |

Formal writer sequence is strictly G24 → G25 → G26 → G27 → G28 → G29 → G30.
G29 is deliberately late because it needs the most Human/external involvement.

## 11. Control-panel requirements

Both Markdown and HTML panels must show:

- current accepted score and denominator;
- each WP weight and status;
- each Goal start gate, status, predecessor, output SHA, and score delta;
- current active writer and next Human action;
- external verification deferred to G29;
- competition as note-only/non-scoring;
- residual limitations and maturity labels.

Historical snapshots may remain for provenance, but the newest top block must
state that retained earlier values do not override the current state.

## 12. Model-profile note

The prompts are optimized for `gpt-5.6-luna` with reasoning effort `high`:

- state each instruction once;
- name safe autonomous actions and approval boundaries explicitly;
- preserve exact evidence and required output schemas;
- use deterministic tools for filtering, counts, joins, and validation;
- reserve model judgment for scope, root cause, remediation, and review;
- stop on material ambiguity rather than inventing a SHA, status, score, or
  product claim.

Model choice does not weaken repository governance. If the selected model or
reasoning effort is unavailable, the Goal must report the actual configuration
and ask the Human whether to continue with a different profile; it must not
silently substitute another model.
