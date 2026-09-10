# Review packet and independent verdict

依 [Framework](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md) §4–5。Writer 在 REVIEW_READY 停寫；Reviewer review exact SHA。以下第一段由 Writer 填，第二段由獨立 Reviewer 填，不得以 self-check 冒充獨立 verdict。

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
PARENT_WP: REQUIRED
REVIEW_CANDIDATE_SHA: REQUIRED
PREDECESSOR_SHA: REQUIRED
BRANCH: REQUIRED
WRITER: REQUIRED
HARNESS: REQUIRED
MODEL: UNKNOWN
CHANGED_FILES: []
DIFF_SUMMARY: REQUIRED
ACTUAL_TEST_COMMANDS: []
ACTUAL_EXIT_CODES: []
NEGATIVE_TESTS: []
SKIPPED: [] # each reason, requirement, blocking
EVIDENCE_REFS: [] # source SHA / file hash, argv/cwd/start/end/output/hash
FROZEN_INVARIANT_MAPPING: []
OUT_OF_SCOPE_CHANGE: NONE
KNOWN_LIMITATIONS: []
ENVIRONMENT_FINGERPRINT: {}
HANDOFF_STATUS: REQUIRED
REVIEW_READY: NO
GOAL_STATUS: IN_PROGRESS # set REVIEW_READY only after validated ZIP
AUTHORIZED_SCOPE: REQUIRED
OUT_OF_SCOPE: REQUIRED
REVIEW_LEVEL: REQUIRED
CREATED_FILES: REQUIRED
MODIFIED_FILES: REQUIRED
DELETED_FILES: REQUIRED
UNEXPECTED_CHANGED_FILES: REQUIRED
FROZEN_INVARIANTS_APPLICABLE: REQUIRED
IMPLEMENTATION_SUMMARY: REQUIRED
OPEN_FINDINGS: REQUIRED
ARCHITECTURE_CONFLICT: REQUIRED
SECURITY_IMPACT: REQUIRED
MIGRATION_IMPACT: REQUIRED
ROLLBACK_RECOVERY: REQUIRED
ENVIRONMENT_FINGERPRINT_REF: REQUIRED
GIT_BUNDLE_REF: REQUIRED
CROSS_MACHINE_STATUS: REQUIRED
REQUESTED_VERDICT: REQUIRED
PUSH_RECOMMENDATION_REQUEST: REQUIRED
```

```yaml
GOAL_ID: REQUIRED
REVIEW_CANDIDATE_SHA: REQUIRED
PREDECESSOR_SHA: REQUIRED
SCOPE_REVIEWED: REQUIRED
ACTUAL_TEST_RESULT: REQUIRED
ACTUAL_EXIT_CODES: REQUIRED
NEGATIVE_TEST_RESULT: REQUIRED
SKIPPED: REQUIRED
EVIDENCE_STATUS: REQUIRED
FROZEN_INVARIANT_CHECK: REQUIRED
OUT_OF_SCOPE_CHANGE: REQUIRED
KNOWN_LIMITATIONS: REQUIRED
BLOCKERS: REQUIRED
VERDICT: PASS / NEED_FIX / HOLD
PUSH_RECOMMENDATION: APPROVE_TO_PUSH / DO_NOT_PUSH
```

每 finding 附 severity、file/line、actual evidence、bounded FIX_PROMPT 與實際適用 commands。Mandatory SKIPPED/missing/stale/wrong-SHA/unknown-exit/untrusted oracle 不能 PASS；optional skip 記限制不自動 FAIL。Mock/simulator 只能證明相應範圍；real executor gate 必有真實 process/changes/cleanup。NEED_FIX 新 SHA 重 review，保留舊 packet。不把 Reviewer recommendation 當 Human push authority。

Acceptance closure依[Framework §5](../governance/POLYNEXUS_TRACK_A_GOAL_EXECUTION_FRAMEWORK.md#5-acceptance-receipt--cross-machine-closure-finding-01)：C已review且Human接受，remote C verified後才能建立R。R不含自身literal SHA/hash；SELF_RECEIPT由固定R解釋，R proof外部保存/接方重驗，避免第三層循環。WIP不產R。Next Goal intake同時保存(R,C)，routing不授權執行；目前next proposed TA-LR-01未執行。

## Receipt payload manifest (metadata only)

```yaml
goal_id: REQUIRED
reviewed_product_sha: FULL_C
acceptance_receipt_sha: SELF_RECEIPT
parent_rule: DIRECT_SINGLE_PARENT_C
checkpoint_type: ACCEPTED
independent_review: {path: REQUIRED, sha256: REQUIRED, size: REQUIRED, target: FULL_C}
human_decision: {path: REQUIRED, sha256: REQUIRED, size: REQUIRED, target: FULL_C}
remote_c_proof: {path: REQUIRED, sha256: REQUIRED, size: REQUIRED, local_sha: FULL_C, remote_sha: FULL_C}
handoff: {path: REQUIRED, sha256: REQUIRED, size: REQUIRED}
changed_files: [] # exact C..R paths, subset of preapproved allowlist
payload_manifest: [] # every other changed payload path/size/SHA-256; self excluded
reviewed_scope_hashes: {} # bound by independent review + Human decision, not self-chosen by R
next_goal: REQUIRED
next_goal_record: {path: REQUIRED, sha256: REQUIRED, size: REQUIRED}
next_governance_predecessor: SELF_RECEIPT
next_reviewed_result: FULL_C
next_goal_authorized: false
```

R manifest不是Human authenticity證明；Verifier先核對C的批准來源/allowlist再驗payload hashes。RI-01..RI-10逐項輸出assertion/expected/actual/command/exit；任何FAIL或UNKNOWN不能push R。R後的integrity與remote proof保存closure log，不改R自身。

本模板的Writer packet欄位投影自[canonical skill schema](../../.agents/skills/polynexus-review-package/references/package-fields.json)；所有packaging rules見[skill](../../.agents/skills/polynexus-review-package/SKILL.md)。不得另建不同REVIEW_PACKET schema。FIRST READ ZIP root START_HERE.md；無validated ZIP不能REQUEST Independent Review。
