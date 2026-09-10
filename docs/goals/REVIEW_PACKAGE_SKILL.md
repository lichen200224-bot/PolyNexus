# REVIEW_PACKAGE_SKILL — Mandatory external review ZIP

GOAL_STATUS: IN_PROGRESS until post-commit delivery gate PASS; completion state is external delivery.json, bound to exact C.

| Field | Contract |
|---|---|
| GOAL_ID | REVIEW_PACKAGE_SKILL |
| TRACK / PARENT_WP | Track A / PROJECT_LOCAL_GOVERNANCE |
| OBJECTIVE | Bounded NEED_FIX only: correct Operating Model R2 accepted versus pending remote closure status; align REVIEW_READY before Independent Review; explicitly deliver ZIP SHA256 |
| AUTHORIZATION | Current Human Independent Review — Bounded NEED_FIX request, FINDING-01/02 only; new local commit and ZIP; no push. Verbatim HUMAN_REQUEST.txt in package |
| PREDECESSOR_SHA | 79e0b1cf20d4e2e27fad67d4355eff253a11a52b; preserved NEED_FIX review candidate; no amend |
| BRANCH | codex/review-package-skill-r2; isolated document review repository |
| WRITER / OWNER | Codex; alternate Writer only Human authorization; single active Writer |
| MODEL / HARNESS | actual model UNKNOWN; Codex desktop context |
| IN_SCOPE | Current status/navigation, Framework lifecycle, affected Skill/Goal/Review template wording; no schema/helper redesign |
| OUT_OF_SCOPE | Product source/tests/schema/runtime/frontend, formal Scope/PRD/SA/SD/Decision Log/ADR/invariants, R2 redesign, TA-LR-01/F1/S0 execution |
| ALLOWED_FILES | Exact ten-file allowlist in this package CHANGED_FILE_ALLOWLIST.txt: three affected SKILL.md; AGENTS.md; Framework; Current Goal/Handoff; this Goal; Goal/Review templates. No new files or product/formal/historical record changes |
| ACCEPTANCE_CRITERIA | No ZIP means not REVIEW_READY; exact identity/bytes/patch/allowlist; all standard fields; L1/L2/L3 bundle/evidence rules; exits/negative/skipped; safe manifest/split/self-reference; Human final authority; this Goal produces validated ZIP and offline exact-SHA proof |
| POSITIVE_CHECKS | field/schema/template consistency, links, official skill frontmatter, package bytes match C, bundle clone P/C, manifest/CRC, protected-byte hashes |
| NEGATIVE_CHECKS | validator rejects missing START_HERE, wrong hash/bytes/candidate/patch, unexpected file, unsafe path/secret, mandatory skip, incomplete package; child nonzero separate from harness exit |
| ROLLBACK_RECOVERY | Preserve primary dirty bytes and R2 candidate; remove/revert only owned governance delta after checking subsequent edits; no reset/clean/history rewrite |
| FROZEN_INVARIANTS | I-01..I-23 unchanged; no architecture impact |
| INDEPENDENT_REVIEW | Human-designated separate context; Writer package PASS not independent PASS |
| STOP | validated ZIP + final response explicit REVIEW_PACKAGE_SHA256 + Human upload instruction; sidecar internal only; no push or next Goal execution |


## Mandatory review package delivery

依[canonical package skill](../../.agents/skills/polynexus-review-package/SKILL.md)，此contract的動態交付值在C後external delivery.json填實，不修改C以填自己的ZIP hash。未填/未驗證不能REVIEW_READY。

```yaml
REVIEW_LEVEL: L1
REVIEW_PACKAGE_REQUIRED: YES
REVIEW_PACKAGE_FORMAT: ZIP
REVIEW_PACKAGE_PATH: PENDING_EXTERNAL_DELIVERY_RECORD
REVIEW_PACKAGE_SHA256: PENDING_EXTERNAL_DELIVERY_RECORD
REVIEW_CANDIDATE_SHA: PENDING
PACKAGE_VALIDATION_STATUS: NOT_RUN
REVIEW_PACKAGE_MINIMUM_CONTENT: canonical skill standard package
GIT_BUNDLE_REQUIREMENT: canonical skill review-level policy
FRESH_EVIDENCE_REQUIREMENT: candidate-bound actual evidence; historical reference only
ENVIRONMENT_FINGERPRINT_REQUIREMENT: canonical skill environment fields
PACKAGE_COMPLETENESS_CRITERIA: all mandatory payloads and required parts; hashes valid
REVIEW_READY_GATE: NO_REVIEW_PACKAGE = NOT_REVIEW_READY
```
