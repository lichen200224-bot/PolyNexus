# PolyNexus Formal Contract / ADR Exact Sync Proposal

- GOAL_ID: `TA-F1`
- STATUS: `LOCAL_PROPOSAL / F2_HUMAN_APPROVAL_REQUIRED`
- REVIEW_LEVEL: `L2_HIGH_RISK_GOAL`
- FORMALIZATION_BASE: `f34e6b29ae9e7326d1d44b9b03756b450809928f`
- TA_LR_01_ACCEPTANCE_RECEIPT: `fe2eb2318dc6558afe1aa6c5361756b082c90c74`
- PRODUCT_IMPLEMENTATION: `HOLD`
- FORMAL_DOC_SYNC: `PROPOSAL_ONLY`
- F3: `NOT_AUTHORIZED`
- S0: `NOT_AUTHORIZED`
- S0_PREDECESSOR: `UNASSIGNED`

## 1. Executive scope

This document is the exact, reviewable proposal for the later F3 synchronization of the frozen V1 formal contract. It does not itself amend Scope, PRD, SA, SD, Decision Log, Architecture Decisions, ADR-011, product source, tests, schema, migrations, runtime, frontend, or workflow definitions. F2 must approve the wording and exact F3 allowlist before any target is changed.

The proposal formalizes two already accepted architecture conclusions: `M-IDENTITY / OUTCOME` and `M-HUMAN`. `M-EXECUTION` remains `NOT REQUIRED / IMPLEMENTATION MAPPING ONLY`. The proposal preserves P0/N1, REST plus WebSocket, D11-C fail-closed fallback, fixed workflow vocabulary, historical Human decisions, and the distinction between accepted provenance and fresh verification.

## 2. Authoritative inputs

| Input | Exact source | Use |
|---|---|---|
| Product/formal baseline | `f34e6b29ae9e7326d1d44b9b03756b450809928f` | Current formal wording and product tree |
| TA-LR-01 reviewed candidate | `944711b2d8db956d811e15c550171e268f572a68` | Accepted reconciliation result |
| TA-LR-01 receipt | `fe2eb2318dc6558afe1aa6c5361756b082c90c74` | HD-L1/L2/L3 and F1 activation |
| Architecture Freeze Record | receipt lineage, `POLYNEXUS_TRACK_A_V1_ARCHITECTURE_FREEZE_RECORD.md` | I-01 through I-23 |
| Gate 2 REV1 | receipt lineage, `GATE_2_CONTRACT_ARCHITECTURE_PACKAGE_REV1.md` | Canonical identity, outcome, Human protocol |
| Formal Change Plan | receipt lineage, `POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md` | F1-F4 sequencing and amendment boundaries |
| Work Packages | receipt lineage, `POLYNEXUS_TRACK_A_IMPLEMENTATION_WORK_PACKAGES.md` | F-before-S0 dependency and W1-W6 mapping |
| Current formal documents | the seven f34 files named in §3 | Current authoritative sections |
| TA-LR legacy ledger and decision packet | accepted receipt lineage | Overlay classification and preservation |

Authority order is the current Human instruction, Frozen I-01..I-23, accepted architecture/governance records, then current f34 formal text. Chat memory and dirty files are not authority.

### 2.1 Frozen invariant coverage index

| Invariant | F1 treatment |
|---|---|
| I-01 | Uses exact f34 design/read and formalization base; preserves dirty/untracked and Git history. |
| I-02 | Preserves local-personal, Single Human, Single Active Writer, managed-worktree boundary. |
| I-03 | Separates TaskID, WorkGenerationRef, RunID and CandidateID; operations bind exact identities. |
| I-04 | New generation for retry; generation/Run ownership references are not Task/Candidate identity. |
| I-05 | Model B; Core-derived identity from snapshots, never caller/display diff. |
| I-06 | References REV1 canonical bytes/hash and Golden authority; no local redefinition. |
| I-07 | Writer quiescence, Candidate freeze and exact verification; modification requires a new Candidate. |
| I-08 | Separates requirement, applicability, outcome and validity; trusted predicate governs N/A. |
| I-09 | Evidence, verification and Human decision bind exact Candidate; AI opinion is not verified evidence. |
| I-10 | Human Accept requires current mandatory policy and fresh exact view; no Override Accept. |
| I-11 | Append-only Human decisions; post-acceptance Revoke/Supersede, not ordinary Reject. |
| I-12 | Human principal/Agent credential separation and bounded protocol security controls. |
| I-13 | Does not freeze TTL, restart re-pairing or storage; preserves equivalent security outcomes. |
| I-14 | Preserves identity/Git observation/ownership/recoverability separation. |
| I-15 | Preserves primary dirty input and immutable accepted-artifact boundary; no auto-adoption. |
| I-16 | Accept does not auto commit/merge/push/release/apply; accepted result remains immutable. |
| I-17 | Durable facts/events remain truth; REST delivery and WebSocket target are preserved. |
| I-18 | P0 accepted package/source reconstruction retained; N1 does not block B01. |
| I-19 | Continuity remains distinct from provider-native session portability; handoff grants no delegation. |
| I-20 | Core owns deterministic side effects; provider-specific behavior remains Adapter/Driver only. |
| I-21 | Current stack/repository/persistence, Alembic, artifact/secret, and fixed workflow vocabulary remain. |
| I-22 | Later execution requires real cwd/change/cancel/timeout/cleanup/provenance/auth/failure evidence. |
| I-23 | Required Stability P0 precedes Working Product execution; planning cannot claim product PASS. |

## 3. Exact F3 file allowlist proposal

F2 is asked to approve exactly these F3 writes and no others:

1. `docs/00_SCOPE_BASELINE.md`
2. `docs/01_PRD.md`
3. `docs/02_SA.md`
4. `docs/03_SD.md`
5. `docs/10_DECISION_LOG.md`
6. `docs/18_ARCHITECTURE_DECISIONS.md`
7. `docs/34_ADR_013_WORK_GENERATION_CANDIDATE_AND_ACCEPTANCE.md` (new)
8. `docs/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md` (new)

`docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md` is explicitly `REFERENCE_ONLY` and is not in the F3 write allowlist. No broad “update all docs” authorization is requested.

## 4. M-IDENTITY formal decision text

F3 shall use the following normative text as the single aggregate identity/outcome decision:

> A `WorkGenerationRef` is the stable pair `(TaskID, generation_revision)`. A control revision is not a generation revision. `Task`, `WorkGeneration`, `Run`, and `Candidate` are distinct identities: a Task may have multiple generations; a WorkGeneration may have multiple Runs; a Candidate is a frozen publication derived from exactly one WorkGeneration and identified by its own `CandidateID`. An implementation MUST NOT introduce an `Attempt Aggregate`; Run remains the durable execution identity without freezing `Run == Attempt`.
>
> Within one WorkGeneration, all writer actions MUST remain in the same writer lineage. Different command IDs, APIs, reconnects, retries, or transports MUST NOT create unrelated writer lineages for the same generation. A new writer lineage requires a new generation according to the accepted contract.
>
> Model B is authoritative. Core derives the `Snapshot` and `ChangeSet` from a verified baseline snapshot and verified result snapshot. Caller claims, UI labels, submitted diff text, or runtime/vendor session data are not identity truth. `SnapshotID`, `ChangeSetID`, `CandidateID`, and `EvidenceSetID` are generated and verified by the canonical REV1 Golden identity authority; downstream documents MUST reference that authority and MUST NOT redefine canonicalization or recompute the identifiers independently.
>
> Candidate publication freezes the exact WorkGeneration, writer lineage, verified Snapshot/ChangeSet, artifacts, and policy-relevant provenance. Candidate verification and every accepted EvidenceSet MUST bind to the exact `CandidateID` and the exact frozen content. Evidence from another Candidate, mutable workspace, unverified diff, or historical run cannot satisfy the Candidate.
>
> Requirement applicability and verification outcome are separate. Applicability is `REQUIRED`, `OPTIONAL`, or `N/A`; outcome is recorded independently. `N/A` is valid only when a trusted deterministic predicate and its evidence establish non-applicability. A required item cannot be omitted, downgraded, or converted to `N/A` by a caller, UI, agent opinion, or missing evidence.
>
> `Reject` applies only before a Candidate has ever been accepted. After acceptance, history is append-only: an accepted decision is never overwritten or relabeled. A later Human action is `Revoke` or `Supersede`, with a new append-only decision record that references the prior accepted decision and exact Candidate.

## 5. M-HUMAN formal decision text

F3 shall use the following D11-A-LP amendment text:

> D11 adopts `A-LP` for the Local-Personal boundary. A Human decision is eligible for acceptance only when the principal is authenticated as Human through the approved local-personal protocol. Agent/runtime/service credentials are separate and MUST NOT be promoted, aliased, prefixed, or interpreted as Human credentials. If the A-LP boundary is unavailable, ambiguous, expired, revoked, or fails verification, D11 Option C remains the mandatory fail-closed fallback: the result remains `HUMAN_DECISION` / `NEED_ACTION` and MUST NOT become `PASS`, `VERIFIED`, or Human-accepted.
>
> Pairing grant, bounded Human session, and per-decision challenge are distinct objects and MUST NOT be collapsed. A pairing grant creates no decision. A session is bounded and revocable and creates no decision. A decision challenge is single-purpose and binds the Human action to the exact rendered Candidate view, exact `CandidateID`, decision kind, nonce, and current eligibility context.
>
> The protocol MUST provide unpredictable nonce and anti-replay validation, idempotent decision submission, CSRF defense, and Origin validation appropriate to the local browser boundary. Reuse, cross-Candidate substitution, stale challenge, wrong Origin, revoked session, or mismatched exact view fails closed. The accepted decision log is append-only and records Human principal reference, exact Candidate/view binding, decision kind, time, and protocol evidence without storing secret values.
>
> Allowed Human decision kinds are `Accept`, `Reject`, `Revoke`, and `Supersede`. `Reject` is pre-acceptance only. `Revoke` and `Supersede` are post-acceptance append-only actions. There is no `Override Accept` operation.
>
> This amendment freezes the trust semantics, not a particular implementation. It does not freeze TTL values, mandatory restart re-pairing, a session-storage mechanism, Enterprise IAM, or hardware attestation.

## 6. M-EXECUTION current determination

`M-EXECUTION: NOT REQUIRED / IMPLEMENTATION MAPPING ONLY`.

No new evidence requires a public `RuntimeAdapter` contract change or a change to `RuntimeBindingSnapshot`. W2 may map current contracts to the frozen semantics through implementation. ADR-011 remains authoritative for runtime identity and transport. If F3 or a later implementation proves a public contract change unavoidable, work must stop with `M_EXECUTION_CONFLICT: FOUND` and `HOLD_FOR_ARCHITECTURE_CHANGE_CONTROL`; it cannot be smuggled into this proposal.

## 7. Per-file current → proposed wording

### 7.1 `docs/00_SCOPE_BASELINE.md`

- PATH: `docs/00_SCOPE_BASELINE.md`
- CURRENT_AUTHORITATIVE_SECTION: §2 V1 Maturity Classes; §5 Governance Baseline
- CURRENT_WORDING_SUMMARY: Defines CORE/BASELINE/COMPATIBILITY/FUTURE and high-level assurance, but does not state the frozen generation/candidate identity or eligible Human-decision boundary.
- PROPOSED_WORDING:

> **V1 contract clarification.** `Task`, `WorkGeneration`, `Run`, and `Candidate` are separate identities; Candidate and Evidence bind to the REV1 Golden identity authority. Human acceptance requires the D11-A-LP eligible Human boundary, with D11-C fail-closed fallback. This clarification does not change the existing maturity classification, P0/N1 boundary, workflow vocabulary, runtime public contract, or Product Scope.

- WHY_REQUIRED: Prevent identity and Human-trust requirements from being mistaken for optional implementation detail.
- FROZEN_INVARIANT_MAPPING: I-01, I-02, I-03, I-04, I-14, I-15, I-19, I-23.
- M_IDENTITY / M_HUMAN mapping: both, summary/reference only.
- COMPATIBILITY_IMPACT: Additive clarification; no existing identifier or endpoint removed.
- MIGRATION_IMPACT: None in this document; later implementation migration remains separate.
- IMPLEMENTATION_IMPACT: Routes W1/W3/W4/W5; grants no implementation authorization.
- TEST_IMPACT: Later contract tests must prove identity binding and Human eligibility.
- LEGACY_WORDING_PRESERVATION: Keep all maturity classes, modes, workflows, assurance, data policy, extension, and deployment text.
- CHANGE_TYPE: `ADD`
- F2_HUMAN_APPROVAL_REQUIRED: `YES`

### 7.2 `docs/01_PRD.md`

- PATH: `docs/01_PRD.md`
- CURRENT_AUTHORITATIVE_SECTION: §7 Workspace / Task / History; Evidence; Policy / Assurance; §11 V1 Release Criteria
- CURRENT_WORDING_SUMMARY: Requires stable Task/Run history and evidence, but not WorkGeneration/Candidate identity, exact Candidate binding, or A-LP Human eligibility.
- PROPOSED_WORDING:

> **FR-IDENTITY.** The product SHALL preserve stable `TaskID`, `WorkGenerationRef`, `RunID`, `CandidateID`, and `EvidenceSetID` references according to the REV1 Golden identity authority. Same-generation writer activity SHALL remain one writer lineage. Candidate publication SHALL freeze exact content and provenance; verification and evidence SHALL bind to that exact Candidate.
>
> **FR-OUTCOME.** Applicability (`REQUIRED` / `OPTIONAL` / `N/A`) SHALL be distinct from outcome. `N/A` requires a trusted predicate. Pre-acceptance `Reject` and post-acceptance `Revoke` / `Supersede` SHALL preserve append-only Human history.
>
> **FR-HUMAN.** An accepted Human decision SHALL require D11-A-LP Human-only principal eligibility, exact-view challenge binding, anti-replay/idempotency, and CSRF/Origin protection. D11-C remains the fallback. Agent credentials cannot authorize Human acceptance; `Override Accept` does not exist.

- WHY_REQUIRED: Makes accepted contract observable as product requirements without claiming implementation.
- FROZEN_INVARIANT_MAPPING: I-01..I-08, I-14..I-23.
- M_IDENTITY / M_HUMAN mapping: both.
- COMPATIBILITY_IMPACT: Additive V1 requirements; existing journeys and maturity labels remain.
- MIGRATION_IMPACT: Future data migration/backfill may be required; F3 changes text only.
- IMPLEMENTATION_IMPACT: W1, W3, W4, W5, W6 acceptance criteria.
- TEST_IMPACT: Positive/negative tests for exact binding, lineage, applicability, and Human protocol.
- LEGACY_WORDING_PRESERVATION: Preserve UJ-01..UJ-05, V1 scope, metrics, provider maturity limits, and release criteria; append requirements only.
- CHANGE_TYPE: `ADD`
- F2_HUMAN_APPROVAL_REQUIRED: `YES`

### 7.3 `docs/02_SA.md`

- PATH: `docs/02_SA.md`
- CURRENT_AUTHORITATIVE_SECTION: §3 Domain Entities; §3.1 Task / Run Semantic Boundary; §4 Trust & Evidence; §15 Event & Audit; §17 Communication / Transport / Gateway Boundary
- CURRENT_WORDING_SUMMARY: Separates Task and Run and defines evidence/trust broadly; its generalized retry/fallback/resume wording predates the frozen WorkGeneration/Candidate model.
- PROPOSED_WORDING:

> Replace only the obsolete generalized identity paragraph in §3.1 with: `Task != WorkGeneration != Run != Candidate`. `WorkGenerationRef=(TaskID,generation_revision)` is stable; control revision is separate. A generation may contain multiple Runs, but all writer actions in that generation share one lineage. No Attempt Aggregate is introduced and `Run == Attempt` is not frozen.
>
> Add to §4: Core-derived Model B Snapshot/ChangeSet and REV1 Golden identity are the authority. Candidate freeze, exact Candidate verification, EvidenceSet binding, and applicability/outcome separation are mandatory. AI opinion and historical evidence cannot become verified Candidate evidence.
>
> Add to §15: Candidate and Human decision events are append-only. Reject is pre-acceptance; Revoke/Supersede reference an earlier accepted decision without overwriting it.
>
> Add to §17: D11-A-LP operates at the local Human decision boundary; Agent/runtime authentication remains distinct. REST remains the durable command/query boundary and WebSocket remains the live-event target. Neither transport is itself Human proof.

- WHY_REQUIRED: Aligns analysis semantics with I-01..I-23 and removes an identity ambiguity before implementation.
- FROZEN_INVARIANT_MAPPING: I-01..I-08, I-14..I-23; I-09..I-13 preserved by no execution change.
- M_IDENTITY / M_HUMAN mapping: both.
- COMPATIBILITY_IMPACT: Existing Task/Run records remain; new generation/candidate meaning is additive and requires explicit migration policy later.
- MIGRATION_IMPACT: Analysis identifies future persistence/backfill need; no migration is authorized.
- IMPLEMENTATION_IMPACT: W1/W3/W4/W5 mapping only.
- TEST_IMPACT: Contract tests for lineage, freeze, evidence binding, append-only decisions, and fallback.
- LEGACY_WORDING_PRESERVATION: Preserve runtime, target, storage, secret, browser, P0/N1, and transport sections except bounded references above.
- CHANGE_TYPE: `MODIFY`
- F2_HUMAN_APPROVAL_REQUIRED: `YES`

### 7.4 `docs/03_SD.md`

- PATH: `docs/03_SD.md`
- CURRENT_AUTHORITATIVE_SECTION: §3 Run State; §6 Artifact Storage; §10 Evidence Envelope; §11 API / Event Boundary; §12 Repository Interfaces; §15 Test Design; §18 Runtime Binding Design
- CURRENT_WORDING_SUMMARY: Provides implementation design for Run, artifacts, evidence, APIs and runtime binding but lacks frozen WorkGeneration/Candidate and A-LP protocol details.
- PROPOSED_WORDING:

> Add a design subsection defining references among Task, WorkGeneration, Run, Candidate, Snapshot, ChangeSet, EvidenceSet, and HumanDecision. Core owns Snapshot/ChangeSet derivation and REV1 identifier verification. Candidate records are immutable after publication and repositories reject cross-Candidate evidence.
>
> Extend Evidence Envelope with explicit applicability, outcome, trusted applicability predicate reference, exact CandidateID, and exact verification binding. A REQUIRED item without valid evidence fails; N/A without its trusted predicate fails.
>
> Extend the Human decision API design with separate pairing grant, bounded/revocable session, and single-use decision challenge; bind exact view, CandidateID, action and nonce; enforce anti-replay, idempotency, CSRF and Origin; append Accept/Reject/Revoke/Supersede records; omit Override Accept.
>
> Preserve the existing `RuntimeAdapter` public method set and `RuntimeBindingSnapshot` semantics. Preserve REST for durable commands/queries and WebSocket for live events. Preserve fixed workflow node/status/verdict vocabulary.

- WHY_REQUIRED: Gives F3 exact design homes for the accepted contract without changing runtime or workflow contracts.
- FROZEN_INVARIANT_MAPPING: I-01..I-23.
- M_IDENTITY / M_HUMAN mapping: both; M-EXECUTION is reference-only preservation.
- COMPATIBILITY_IMPACT: Additive data/API design with explicit legacy migration requirement; no current endpoint removed.
- MIGRATION_IMPACT: Future Alembic and deterministic backfill must be separately proposed, rehearsed, and accepted.
- IMPLEMENTATION_IMPACT: W1/W3/W4/W5; no code under F3.
- TEST_IMPACT: Repository, API, replay, CSRF/Origin, exact-view, freeze, and negative binding cases.
- LEGACY_WORDING_PRESERVATION: Preserve Run lifecycle, Adapter interface, RuntimeBindingSnapshot, P0/N1, REST/WebSocket, storage, secrets, Browser Companion, and workflow vocabulary.
- CHANGE_TYPE: `ADD`
- F2_HUMAN_APPROVAL_REQUIRED: `YES`

### 7.5 `docs/10_DECISION_LOG.md`

- PATH: `docs/10_DECISION_LOG.md`
- CURRENT_AUTHORITATIVE_SECTION: D11; Architecture Decisions
- CURRENT_WORDING_SUMMARY: D11 currently records Option C fail-closed and reserves authenticated principal mapping; it does not contain accepted A-LP semantics. Dirty overlay adds G13/G14 routing only.
- PROPOSED_WORDING:

> Amend D11 status to `CONFIRMED; A-LP HUMAN ACCEPTED; OPTION C FALLBACK PRESERVED`. Add the exact M-HUMAN text from §5 by reference to `docs/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md`. State that this acceptance grants no product implementation, fixed TTL, restart policy, storage choice, Enterprise IAM, or hardware attestation.
>
> Add `D13 — WorkGeneration, Candidate, Evidence and Acceptance Identity — HUMAN ACCEPTED` by reference to ADR-013, using the exact M-IDENTITY text in §4. State `M-EXECUTION: NOT REQUIRED / IMPLEMENTATION MAPPING ONLY`.

- WHY_REQUIRED: Decision Log is the canonical Human-decision index.
- FROZEN_INVARIANT_MAPPING: I-01..I-08, I-14..I-23; D11-C.
- M_IDENTITY / M_HUMAN mapping: D13 / amended D11.
- COMPATIBILITY_IMPACT: Supersedes only the “future Option A or B undecided” portion of D11; preserves fail-closed behavior and history.
- MIGRATION_IMPACT: None at F3; references future separately authorized migration.
- IMPLEMENTATION_IMPACT: No authorization.
- TEST_IMPACT: Later W5 protocol tests; W3/W4 identity tests.
- LEGACY_WORDING_PRESERVATION: Preserve all D01-D12 and historical routing. The dirty G13/G14 overlay is not adopted by F3 because it is a separate routing record.
- CHANGE_TYPE: `MODIFY`
- F2_HUMAN_APPROVAL_REQUIRED: `YES`

### 7.6 `docs/18_ARCHITECTURE_DECISIONS.md`

- PATH: `docs/18_ARCHITECTURE_DECISIONS.md`
- CURRENT_AUTHORITATIVE_SECTION: ADR-004, ADR-007..ADR-011, V1 Guardrails
- CURRENT_WORDING_SUMMARY: Index covers runtime, artifacts, workflow, security, and ADR-011; ADR-012 Doctor exists elsewhere but the heading still says ADR-001..010.
- PROPOSED_WORDING:

> Update the title/index scope without altering accepted ADR text. Add `ADR-012 — Runtime Doctor Reporting` as an existing-reference entry. Add `ADR-013 — WorkGeneration, Candidate and Acceptance Identity` pointing to `docs/34_ADR_013_WORK_GENERATION_CANDIDATE_AND_ACCEPTANCE.md`. Add a D11-A-LP amendment reference under ADR-010 pointing to `docs/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md`. Record that ADR-011 is unchanged and `M-EXECUTION` is implementation mapping only.

- WHY_REQUIRED: Maintains an accurate formal index and prevents the new decisions from being hidden in planning records.
- FROZEN_INVARIANT_MAPPING: I-01..I-23.
- M_IDENTITY / M_HUMAN mapping: ADR-013 / ADR-010+D11 amendment.
- COMPATIBILITY_IMPACT: Index/reference-only additions; existing ADR-001..012 wording preserved.
- MIGRATION_IMPACT: None.
- IMPLEMENTATION_IMPACT: None.
- TEST_IMPACT: Cross-reference validation only.
- LEGACY_WORDING_PRESERVATION: Existing ADR summaries and V1 guardrails remain verbatim except title/index references.
- CHANGE_TYPE: `MODIFY`
- F2_HUMAN_APPROVAL_REQUIRED: `YES`

### 7.7 `docs/34_ADR_013_WORK_GENERATION_CANDIDATE_AND_ACCEPTANCE.md`

- PATH: `docs/34_ADR_013_WORK_GENERATION_CANDIDATE_AND_ACCEPTANCE.md`
- CURRENT_AUTHORITATIVE_SECTION: New file; source authority is Freeze Record and REV1.
- CURRENT_WORDING_SUMMARY: No current formal ADR contains the complete aggregate identity/outcome decision.
- PROPOSED_WORDING: Create an ADR with Context, Decision, exact §4 normative text, Model B diagram/reference, applicability/outcome table, candidate freeze, EvidenceSet binding, alternatives rejected (Attempt Aggregate, caller-derived diff, mutable candidate, destructive acceptance overwrite), compatibility/migration/test impact, and implementation-not-authorized status.
- WHY_REQUIRED: Formal Change Plan requires one aggregate M-IDENTITY/OUTCOME decision.
- FROZEN_INVARIANT_MAPPING: I-01..I-08, I-14..I-19, I-23.
- M_IDENTITY / M_HUMAN mapping: M-IDENTITY primary; Human outcome vocabulary only.
- COMPATIBILITY_IMPACT: Stable legacy Task/Run retained; migration/backfill explicit.
- MIGRATION_IMPACT: Future, separately authorized schema/backfill/rollback.
- IMPLEMENTATION_IMPACT: W1/W3/W4/W5 mapping; none authorized.
- TEST_IMPACT: Golden identity vectors, lineage, freeze, exact binding, applicability/outcome, append-only history.
- LEGACY_WORDING_PRESERVATION: References REV1 Golden authority; does not duplicate/redefine its canonicalization.
- CHANGE_TYPE: `ADD`
- F2_HUMAN_APPROVAL_REQUIRED: `YES`

### 7.8 `docs/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md`

- PATH: `docs/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md`
- CURRENT_AUTHORITATIVE_SECTION: New file; extends D11 and ADR-010.
- CURRENT_WORDING_SUMMARY: D11-C exists, but accepted A-LP trust and protocol semantics have no formal home.
- PROPOSED_WORDING: Create the formal D11 amendment with exact §5 normative text, local-personal threat boundary, object separation, sequence, failure table, append-only decision history, compatibility/migration/test impact, non-goals, and implementation-not-authorized status.
- WHY_REQUIRED: Formalizes Human acceptance eligibility without weakening D11-C.
- FROZEN_INVARIANT_MAPPING: I-14..I-23; I-07/I-08 for decision lifecycle.
- M_IDENTITY / M_HUMAN mapping: M-HUMAN primary; exact Candidate binding references M-IDENTITY.
- COMPATIBILITY_IMPACT: Existing unauthenticated flows remain NEED_ACTION; no fabricated upgrade to Human accepted.
- MIGRATION_IMPACT: Future append-only decision/pairing/session/challenge persistence requires separate plan; no secret migration.
- IMPLEMENTATION_IMPACT: W5; none authorized.
- TEST_IMPACT: replay, idempotency, exact view, wrong candidate, Origin/CSRF, expiry/revocation, D11-C fallback, no Override Accept.
- LEGACY_WORDING_PRESERVATION: D11 history and Option C remain; unspecified TTL/storage/enterprise/hardware choices stay open.
- CHANGE_TYPE: `ADD`
- F2_HUMAN_APPROVAL_REQUIRED: `YES`

### 7.9 `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`

- PATH: `docs/29_ADR_011_RUNTIME_BINDING_AND_TRANSPORT.md`
- CURRENT_AUTHORITATIVE_SECTION: §2, §4, §5, §13
- CURRENT_WORDING_SUMMARY: Human-accepted runtime binding and transport architecture; implementation not authorized.
- PROPOSED_WORDING: No edit. F3 documents may reference ADR-011 for RuntimeBindingSnapshot and transport identity. `M-EXECUTION` stays `NOT REQUIRED / IMPLEMENTATION MAPPING ONLY`.
- WHY_REQUIRED: Explicitly proves no convenient public runtime-contract rewrite is hidden in F1/F3.
- FROZEN_INVARIANT_MAPPING: I-09..I-13.
- M_IDENTITY / M_HUMAN mapping: neither; execution preservation boundary.
- COMPATIBILITY_IMPACT: None.
- MIGRATION_IMPACT: None under F3.
- IMPLEMENTATION_IMPACT: None.
- TEST_IMPACT: Hash/reference verification only.
- LEGACY_WORDING_PRESERVATION: Entire file unchanged.
- CHANGE_TYPE: `REFERENCE_ONLY`
- F2_HUMAN_APPROVAL_REQUIRED: `YES`

## 8. ADR/index/reference changes

The proposal uses existing ADR-012 for Runtime Doctor, assigns the next unoccupied architecture identifier ADR-013 to the single aggregate identity/outcome decision, and treats D11-A-LP as an amendment under the existing ADR-010 security boundary rather than a competing authentication architecture. This avoids renumbering, rewriting ADR-011, or multiplying the seven REV1 identity clarifications into separate ADRs.

## 9. SA synchronization proposal

SA receives semantic relationships and trust boundaries, not storage or endpoint pseudocode. It replaces only the now-obsolete generalized Task/Run ambiguity, then adds Model B, Candidate/Evidence binding, append-only Human outcomes, and transport-not-authentication language. Runtime, data classification, browser, P0/N1, and technology sections remain.

## 10. SD synchronization proposal

SD receives the implementable reference graph, repository invariants, evidence fields, failure conditions, and A-LP protocol responsibilities. It must reference rather than duplicate REV1 canonicalization. Existing RuntimeAdapter and RuntimeBindingSnapshot sections remain unchanged. Any later data model, endpoint, or migration requires its own authorized Goal.

## 11. PRD minimum changes

Only three requirement groups are added: stable identity/freeze, outcome/applicability/history, and eligible Human acceptance. No persona, journey, maturity, metric, provider support, or release claim is expanded.

## 12. Scope minimum changes

One V1 contract-clarification paragraph is added. It explicitly says this is not scope expansion and preserves current CORE/BASELINE/COMPATIBILITY/FUTURE classifications.

## 13. Decision Log / D11 proposal

D11 records A-LP acceptance while retaining Option C as the mandatory fallback. D13 records the aggregate identity/outcome decision. Historical D01-D12 and routing records remain append-only. The dirty G13/G14 paragraph is a `USEFUL_REFERENCE` for later routing but is not part of the F3 formal contract allowlist.

## 14. Explicit NOT TO CHANGE

- No product source, production tests, schemas, migrations, runtime or frontend.
- No `RuntimeAdapter` public contract or `RuntimeBindingSnapshot` semantic change.
- No Attempt Aggregate and no `Run == Attempt` freeze.
- No workflow node/status/verdict vocabulary change.
- No P0/N1 boundary change.
- No REST/WebSocket boundary change.
- No provider/live-vendor/external certification claim.
- No fixed TTL, restart re-pair rule, session-storage implementation, Enterprise IAM, or hardware attestation.
- No F2/F3/S0/product implementation authorization by implication.

## 15. Legacy wording preservation

| Overlay | Classification | Treatment |
|---|---|---|
| Primary dirty `docs/10_DECISION_LOG.md` G13/G14 routing addition | `USEFUL_REFERENCE` | Preserve in primary; do not adopt into F3 contract sync because it is separate routing and does not alter accepted M decisions. |
| TA-LR LR-039 Human decision/history/recovery | `SUPERSEDED` for old planning wording; accepted semantics retained | Replace planning ambiguity with exact D11-A-LP amendment; preserve D11-C and append-only history. |
| TA-LR LR-047 dirty formal/navigation overlays | `REQUIRES_F3_MIGRATION` | Compare per file/hash; use only bounded approved wording; no whole-file merge. |
| Dirty runtime contract/registry overlays LR-048 | `NOT_RELEVANT` to F1/F3 | Preserve for W2 intake; no adoption or runtime contract proposal. |
| G23/G25/G26/G27/G28 accepted outputs LR-052..LR-056 | `USEFUL_REFERENCE` | Preserve provenance; do not treat as fresh Track A verification or formal wording authority. |
| Old G19-G30 routing | `SUPERSEDED` where TA-LR says so | Keep history; no second active legacy roadmap and no deletion. |
| G30 external certification | `CONFLICTING` with any certification claim | Preserve as `HISTORICAL_NEED_ACTION`; route to separate external release verification. |

The primary dirty/untracked workspace remains `PRESERVE / NOT_AUTO_ADOPTED`; G08/G09 remain `PRESERVE / NEXT / REQUIRES_REVALIDATION`.

## 16. Compatibility impact

The proposal is additive at the formal-contract level. Existing TaskID/RunID, runtime adapter behavior, RuntimeBindingSnapshot, workflow files, API transport split, and historical accepted evidence remain. Legacy records need explicit mapping rather than reinterpretation. Unauthenticated existing Human-like strings stay ineligible and cannot be upgraded by migration guesswork.

## 17. Migration impact

F1 and F3 are documentation-only. Later implementation may require new generation/candidate/evidence/decision persistence and deterministic legacy mapping. That work must use Alembic as migration authority, preserve Task/Run/Evidence history, fail closed on ambiguity, include backup/restore and rollback rehearsal, and never migrate secret values into normal domain records. Exact schema and backfill values are intentionally not frozen here.

## 18. Test impact

Later authorized implementation must cover: REV1 Golden vectors; same-generation lineage negative cases; Core-derived Snapshot/ChangeSet; Candidate immutability; cross-Candidate evidence rejection; required/optional/N/A predicates; pre/post acceptance action legality; append-only history; exact-view mismatch; nonce replay; idempotent retry; CSRF/Origin; expired/revoked session; Agent credential rejection; D11-C fallback; unchanged RuntimeAdapter; unchanged REST/WebSocket and workflow vocabulary.

## 19. Rollback/document restoration approach

F3 must record pre-edit blob hashes for every allowed existing file and create only the two approved new files. Rollback is a bounded inverse patch restoring those exact blobs and removing only the two F3-created files if they remain unaccepted. Never reset, clean, prune, overwrite primary dirty files, or rewrite accepted Git history. An accepted formal checkpoint must be superseded by a later append-only change, not amended in place.

## 20. Before/After summary

| Boundary | Before f34 | Proposed after F3 (only if F2 approves) |
|---|---|---|
| Identity | Task/Run stable but generation/candidate incomplete | Exact Task/WorkGeneration/Run/Candidate and Model B contract |
| Evidence | Generic envelope | Exact Candidate/EvidenceSet binding and applicability/outcome separation |
| Human | D11-C only | A-LP eligible Human path plus unchanged C fallback |
| Acceptance history | Not fully formalized | Reject before acceptance; Revoke/Supersede after; append-only |
| Execution | ADR-011 accepted | Unchanged; mapping only |
| Scope/workflow/transport | Frozen | Unchanged |

## 21. Cross-reference verification plan

F3 validation must resolve every Markdown path; confirm section headings named in §7; verify ADR-012 already denotes Runtime Doctor and ADR-013 is unoccupied at predecessor; search all F3 targets for each I-01..I-23 mapping; verify D11-C, P0/N1, REST/WebSocket, fixed node/status/verdict vocabulary, M-EXECUTION, F3/S0 states; compare hashes for ADR-011 and all non-allowlisted formal files; and compare `apps`, `services`, `schemas`, `workflows`, and `extensions` trees with f34.

## 22. F2 Human approval checklist

- [ ] Approve exact eight-path F3 write allowlist in §3.
- [ ] Approve ADR-013 identifier and new path.
- [ ] Approve D11-A-LP amendment path and its ADR-010 relationship.
- [ ] Approve exact M-IDENTITY text in §4.
- [ ] Approve exact M-HUMAN text in §5.
- [ ] Confirm M-EXECUTION remains mapping only.
- [ ] Confirm D11-C, P0/N1, REST/WebSocket, fixed workflow vocabulary, and historical decisions are preserved.
- [ ] Confirm no provider certification, implementation, migration, F3, or S0 is authorized by F2 review alone.
- [ ] Approve legacy overlay classifications in §15.
- [ ] Specify the exact accepted F1 Candidate SHA as F3 predecessor if approving F3.

## 23. F3 execution prerequisites

F3 requires independent L2 PASS on the exact F1 Candidate/package, explicit Human F2 approval of wording and allowlist, an exact remote-verified accepted F1 receipt/checkpoint, a newly authorized isolated formalization Goal, clean lane ownership, and fresh predecessor/target hashes. Any wording or allowlist change creates a new review candidate.

## 24. Known limitations

- No product implementation or executable protocol is delivered.
- Migration schema/backfill, API shape, TTL, storage, and UI are intentionally undecided.
- G30 provider certification remains `HISTORICAL_NEED_ACTION`.
- G08/G09 and primary dirty/untracked items remain preserved and require later bounded revalidation/adoption decisions.
- The requested SOL/MEDIUM routing is recorded; the harness does not expose a cryptographically attestable model identity, so actual model identity is `UNKNOWN` rather than inferred.

## 25. F1 final verdict request

Independent Reviewer is asked to return exactly `PASS`, `NEED_FIX`, or `HOLD` for this Candidate and to assess: authority fidelity, I-01..I-23 completeness, exact wording, bounded allowlist, unchanged formal/product trees, overlay preservation, M-EXECUTION preservation, and executable F2/F3 gates. A PASS is a recommendation for Human F2 consideration only; it is not F2 approval and does not authorize F3, S0, push, or product implementation.
