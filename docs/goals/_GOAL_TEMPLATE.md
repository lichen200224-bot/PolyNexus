# Goal contract template

依 [Framework](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md)。PLANNED 不授權執行；authorization 前所有影響 scope/safety/AC 的 UNKNOWN 必須解決。普通 implementation choices 由 Writer 處理。

```yaml
REVIEWED_PRODUCT_SHA: UNASSIGNED # C, exact independent-review/Human target
ACCEPTANCE_RECEIPT_SHA: UNASSIGNED # R after closure; in R use SELF_RECEIPT
GOVERNANCE_PREDECESSOR_SHA: UNASSIGNED # accepted R for next Goal, not product C
REVIEWED_PREDECESSOR_SHA: UNASSIGNED # C from predecessor receipt
ONE_BOUNDED_ACCEPTANCE_RECEIPT_CLOSURE: NOT_AUTHORIZED
RECEIPT_EXACT_ALLOWLIST: [] # Human-approved exact metadata paths; Framework 5.2
REVIEWED_SCOPE_HASHES: {} # protected result bytes; not retroactively excluded
RECEIPT_PARENT_RULE: DIRECT_SINGLE_PARENT_C
RECEIPT_INTEGRITY: NOT_RUN
REMOTE_C_PROOF_REF: NONE
REMOTE_R_PROOF_REF: NONE # external after R; receiver independently verifies remote R
CROSS_MACHINE_CHECKPOINT: NOT_READY

GOAL_ID: REQUIRED
TRACK: Track A V1
PARENT_WP: REQUIRED
EPIC_GOAL: REQUIRED
GOAL_STATUS: PLANNED
OBJECTIVE: REQUIRED
WHY: REQUIRED
CURRENT_STATE: REQUIRED
TARGET_STATE: REQUIRED
INPUT: [exact source paths and identities]
PREDECESSOR_CHECKPOINT: {sha: UNASSIGNED, acceptance_ref: REQUIRED, remote_ref: REQUIRED}
IN_SCOPE: []
OUT_OF_SCOPE: []
ALLOWED_FILES: [] # exact files; empty means no permission
NEW_FILE_RESPONSIBILITY_RULE: NONE # bounded directory, purpose, exclusions
EXPECTED_FILE_AREAS: [] # planning only
FROZEN_INVARIANTS: [I-01 through I-23; relevant mapping and source]
DEPENDENCIES: []
INTEGRATION_DEPENDENCIES: []
GOAL_OWNER: CODEX
PREFERRED_IMPLEMENTATION_WRITER: CODEX
AUTHORIZED_IMPLEMENTATION_WRITER: NONE
WRITER_AUTHORIZATION_SOURCE: NONE
ACTIVE_WRITER_SCOPE: NONE
WRITER_MACHINE_CONTEXT: UNASSIGNED
OWNERSHIP_ACQUIRED_AT: NOT_ACQUIRED
OWNERSHIP_RELEASE_TRANSFER_REF: NONE
RECOMMENDED_REASONING_MODEL: SOL MEDIUM
MODEL_FALLBACK: bounded routine only; see Framework
MODEL_ESCALATION_RULE: uncertainty to SOL; trust/architecture/migration to ASTRA; unavailable required model HOLD
ACTUAL_HARNESS_MODEL: UNKNOWN
EXECUTION_MODE: SEQUENTIAL_REQUIRED
BRANCH_STRATEGY: independent managed branch; exact branch assigned before authorization
AUTHORIZED_BRANCH: NONE
CROSS_MACHINE_HANDOFF_REQUIRED: YES
REMOTE_CHECKPOINT_REQUIREMENT: Human-approved exact reviewed SHA verified at remote, then clean intake
POSITIVE_TESTS: [] # behavior + oracle + commands once real paths exist
NEGATIVE_TESTS: [] # injected outcomes distinct from runner exit
FAIL_CLOSED_CONDITIONS: []
ACTUAL_EXIT_CODE_REQUIREMENT: exact argv/cwd/time/exit/signal per command; UNKNOWN is not PASS
EVIDENCE_REQUIREMENT: hashes, exact candidate, environment, output refs, requirement/oracle provenance
ROLLBACK_RECOVERY: preserve Human bytes and failed evidence; bounded non-destructive rollback
REVIEW_CANDIDATE_REQUIREMENT: immutable local commit; no push; exact SHA review
COMPLETION_CRITERIA: []
INDEPENDENT_REVIEW: Human-designated ChatGPT Review Context; writer != reviewer
PUSH_RECOMMENDATION: DO_NOT_PUSH until independent verdict
HUMAN_ACCEPTANCE_REF: NONE
PUSH_AUTHORIZATION_REF: NONE
SKIPPED: [] # each requirement and blocking classification
NEXT_GOAL: REQUIRED
```

Batch authorization 另列 batch ID、每 Goal exact scope/branch/writer、dependency-safe 判斷與最大並發，不取代逐 Goal review/acceptance。Integration Goal 必須列 accepted A/B SHAs、預期 C、衝突處理與 affected regression。

Acceptance closure依[Framework §5](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md#5-acceptance-receipt--cross-machine-closure-finding-01)：C已review且Human接受，remote C verified後才能建立R。R不含自身literal SHA/hash；SELF_RECEIPT由固定R解釋，R proof外部保存/接方重驗，避免第三層循環。WIP不產R。Next Goal intake同時保存(R,C)，routing不授權執行；目前next proposed TA-LR-01未執行。
