# PolyNexus Multi-AI Collaboration — Role-first

Status: `HUMAN_APPROVED TRANSITION MODEL` (2026-09-12)

## 1. Roles are authoritative; tools are replaceable

Formal roles:

- `HUMAN_AUTHORITY`: scope/architecture/product/acceptance/integration/release authority.
- `ARCHITECT`: architecture analysis and proposal under Human gate.
- `WRITER`: sole active implementation/documentation writer for one task branch.
- `INDEPENDENT_REVIEWER`: read-only reviewer of the exact candidate; must not be that patch's Writer.
- `SPECIALIZED_VERIFIER`: browser/E2E/security/environment or other bounded specialist.

Codex, OpenCode, Antigravity, Claude, or future tools can fill a role only when the task/routing decision assigns it. Tool name does not imply Git or acceptance authority.

## 2. Recommended defaults, not hard bindings

- Codex: architecture/core/hard root cause/critical review.
- OpenCode: routine implementation/tests/templates.
- Antigravity: browser/UI/E2E/milestone verification.
- Claude: bounded analysis/document work/second opinion.

Task requirements may choose differently. `Writer != Independent Reviewer` always applies.

## 3. Single Active Writer

One task branch has one active Writer. Other agents may inspect or review immutable SHAs but must not modify the same candidate concurrently. Tool switching is sequential unless separate branches/tasks are explicitly authorized.

## 4. Machine/tool-independent Task Start

A new session should need only:

```text
Task ID
Assigned role
Expected branch/checkpoint
```

Then follow the repository Start Protocol: discover repo root, verify canonical remote with `git ls-remote`, fetch exact SHA, verify state, read AGENTS/current routing/task doc, and return START_GATE.

No prompt should require a fixed drive path.

## 5. Context budget

Load `AGENTS.md + docs/37_CURRENT_ROUTING_INDEX.md + current task doc` first. Add relevant ADR/spec/code/tests only when task evidence requires them. Reviewer is SHA/diff-first. Do not redo full-repo analysis merely because the tool or machine changed.

## 6. Checkpoint collaboration

- `SYNC_CHECKPOINT`: Writer may use it for approved cross-machine/tool continuation. It is not PASS.
- `CANDIDATE_CHECKPOINT`: immutable pushed SHA sent to Reviewer. It is not PASS.
- `ACCEPTED_CHECKPOINT`: only after independent review and Human acceptance.

If review returns `NEED_FIX`, Writer creates a new candidate SHA; reviewed commits are not amended/rebased away.

## 7. Routing contract

Every routing decision includes:

- `TASK_ID`
- `ROLE` / `NEXT_OWNER`
- branch + predecessor/candidate SHA
- scope / protected areas
- allowed actions / forbidden actions
- required evidence
- acceptance/stop condition

`NEXT_PROMPT != delegation permission`. Recursive delegation requires a new routing decision.

## 8. Handoff contract

Minimum handoff fields:

```text
TASK_ID
ATTEMPT
ROLE / WRITER / REVIEWER
BRANCH
START_SHA
CURRENT_OR_CANDIDATE_SHA
CHANGED_FILES
TEST_COMMANDS + ACTUAL_EXIT_CODES
ADR_IMPACT
SCOPE_DEVIATION
KNOWN_LIMITATIONS
UNVERIFIED
NEXT_ACTION
NEXT_OWNER
STOP_CONDITION
```

Long logs stay in local/artifact storage; handoff keeps deterministic summary and references. No secret values.

## 9. Review contract

Reviewer verifies the exact pushed candidate SHA, not Writer's local dirty workspace. Reviewer may rerun required deterministic evidence in an isolated clone/worktree. Results are `VERIFIED_PASS`, `NEED_FIX`, `FAIL`, or `NEED_ACTION`.

`NEED_FIX`/`FAIL` must include evidence and bounded remediation scope. Reviewer never silently edits the candidate it is independently reviewing.

## 10. Human boundaries

Routine task-branch SYNC/CANDIDATE commit+push may be pre-authorized in the Task Execution Envelope. Human remains required for:

- architecture/scope expansion;
- secrets, authenticated external actions, production data or irreversible actions;
- acceptance of candidate;
- integration into accepted line;
- release/promotion;
- force/history rewrite/remote configuration/destructive Git.

## 11. Browser / specialized verification

Browser/E2E tasks may route `Writer -> Specialized Verifier -> Independent Reviewer -> Human`. Fixture/mock evidence remains explicitly bounded and cannot be promoted to live vendor/production evidence.

## 12. Evolution rule

New AI tools join by mapping to a role and obeying the same Git/evidence contract. Governance must not require redesign simply because a model, vendor, UI, or local install path changes.
