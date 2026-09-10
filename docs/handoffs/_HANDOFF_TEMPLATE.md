# Checkpoint handoff template

依 [Framework](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) §5–7。送方停寫後接方取得 ownership。未知值如實記錄；WIP 不成為 accepted。記錄檔名使用 exact SHA 或明確 WIP-ID；自引用限制見 Framework §4。

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

PROJECT: PolyNexus
TRACK: Track A V1
WORK_PACKAGE: REQUIRED
EPIC_GOAL: REQUIRED
GOAL_ID: REQUIRED
TASK_ID: REQUIRED
ATTEMPT: REQUIRED
TASK_DOC: REQUIRED
HANDOFF_DOC: REQUIRED
CHECKPOINT_TYPE: REVIEW_CANDIDATE # or ACCEPTED / WIP / INTEGRATION
BRANCH: REQUIRED
COMMIT_SHA: REQUIRED
REMOTE: REQUIRED
REMOTE_BRANCH_SHA: UNVERIFIED
PREDECESSOR_SHA: REQUIRED
STATUS: REQUIRED
WRITER: REQUIRED
REVIEWER: UNASSIGNED
HARNESS: REQUIRED
MODEL: UNKNOWN
COMPLETED_SCOPE: []
FILES_CHANGED: [] # complete including untracked; separate pre-existing excluded inventory
TESTS_RUN: []
ACTUAL_EXIT_CODES: []
NEGATIVE_TESTS: []
SKIPPED: [] # reason + blocking per item
EVIDENCE: [] # path/hash/candidate/time
KNOWN_LIMITATIONS: []
OPEN_FINDINGS: []
FROZEN_INVARIANTS: []
PROTECTED_AREAS: []
ADR_IMPACT: NONE
SCOPE_DEVIATION: NONE
UNVERIFIED_ITEMS: []
ANTIGRAVITY_STATUS: NOT_REQUIRED # reason, or actual route/fixture/result/artifact/blocker
NEXT_GOAL: REQUIRED
NEXT_ALLOWED_SCOPE: []
DEPENDENCIES: []
INTEGRATION_DEPENDENCIES: []
ENVIRONMENT_FINGERPRINT: {} # Framework required fields, env names only
HANDOFF_TIMESTAMP: REQUIRED
WRITER_RELEASE_CONFIRMATION: NOT_CONFIRMED
WRITER_TRANSFER_AUTHORITY: NONE
RECEIVER_ACQUISITION: NOT_ACQUIRED
HANDOFF_INTAKE: NOT_RUN
NEXT_ACTION: REQUIRED
NEXT_OWNER: REQUIRED
NEXT_PROMPT: REQUIRED # never delegation permission
STOP_CONDITION: REQUIRED
```

Receiving evidence：fetch command/exit、expected/actual branch/SHA、safe lane、HEAD/index/dirty/untracked、可讀 governance/Goal/refs、lock hashes/dependency checks、writer transfer。任一 identity/ownership 缺失 FAIL / DO_NOT_START_IMPLEMENTATION。WIP 必加 NOT_ACCEPTED / NOT_REVIEWED / DO_NOT_MERGE；accepted 必附 independent verdict + Human decision + verified remote refs。

Acceptance closure依[Framework §5](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md#5-acceptance-receipt--cross-machine-closure-finding-01)：C已review且Human接受，remote C verified後才能建立R。R不含自身literal SHA/hash；SELF_RECEIPT由固定R解釋，R proof外部保存/接方重驗，避免第三層循環。WIP不產R。Next Goal intake同時保存(R,C)，routing不授權執行；目前next proposed TA-LR-01未執行。

Review delivery引用[canonical package skill](../../.agents/skills/polynexus-review-package/SKILL.md)；handoff應引用validated ZIP、SHA256及C，不能以handoff文字取代Review Package或C/R accepted remote gate。
