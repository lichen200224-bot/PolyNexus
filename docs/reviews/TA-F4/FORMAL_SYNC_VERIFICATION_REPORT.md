# TA-F4 Formal Synchronization Verification Report

## 1. Authorization and verdict scope

TA-F4 execution is authorized by `TA-F4-HUMAN-AUTH-20260911-01` before this Candidate is
created. This report verifies the Human-accepted TA-F3 formal synchronization. It is document
and governance verification only. It does not assert F4 acceptance or L2 PASS and does not
execute a product migration, runtime, schema, frontend, workflow, provider, release, F5, or S0
operation.

```yaml
AUTHORIZATION_ID: TA-F4-HUMAN-AUTH-20260911-01
F3_REVIEWED_SHA: c4c17924ad568e5ae279fa3632a9960421ba80cb
F3_RECEIPT_SHA: 284929a8f5a39df5524ccba7d733aa9161fc91e9
F3_FORMAL_PREDECESSOR_SHA: 632b5e061c225e717e3ec0d5686a83f654858529
PREVIOUS_F4_CANDIDATE: a0bb7458bab95836c6af066b8d2d12a61917c195
PREVIOUS_F4_CANDIDATE_DISPOSITION: ABANDONED_FOR_PROMOTION
F3_EXACT_EIGHT_FILE_DELTA: VERIFIED
F4_FORMAL_TARGET_CHANGES: NONE
PRODUCT_CODE_CHANGES: NONE
M_EXECUTION_CONFLICT: NOT_FOUND
PRODUCT_IMPLEMENTATION: HOLD
S0: NOT_AUTHORIZED
S0_PREDECESSOR: UNASSIGNED
```

## 2. Authoritative inputs

- TA-F4 Human authorization `TA-F4-HUMAN-AUTH-20260911-01`.
- TA-F3 accepted receipt and handoff at exact predecessor `284929a8...`.
- TA-F3 reviewed formal result `c4c1792...` and its exact parent `632b5e0...`.
- Accepted F1 exact sync proposal and F2 exact wording/eight-file approval.
- TA-LR-01 accepted Architecture Freeze Record, Gate 2 REV1, Formal Change Plan, Work
  Packages, and 56-item legacy reconciliation ledger.
- The eight accepted formal files plus reference-only ADR-011.

The abandoned Candidate is reference-only timing history and is not an accepted input or an
ancestor of this remediation Candidate. Historical chat memory is not authority.

## 3. Cross-reference verification

Every repository-local `docs/*.md` reference found in the eight F3 formal files resolves in
the F3 receipt tree. The ADR index resolves ADR-011, ADR-012, ADR-013, and D11-A-LP targets.
The accepted F1 proposal and TA-F3 receipt references also resolve. Detailed machine-readable
results are in `evidence/cross-reference-report.json`.

## 4. I-01 through I-23 consistency

All 23 frozen invariants have explicit authority-to-formal mappings and were checked for
contradiction. The F3 wording strengthens the accepted identity and Human-decision contracts
without weakening unchanged invariants. No new invariant number, Attempt aggregate, workflow
vocabulary, runtime public contract, or second execution truth was introduced.

The mapping distinguishes direct formal coverage from preserved external Freeze/REV1
authority. A preserved mapping does not claim that F3 reprinted the entire invariant.

## 5. D11-C fallback

D11-A-LP is the accepted Local-Personal Human-only protocol. D11-C remains mandatory and
fail-closed whenever A-LP is unavailable, ambiguous, expired, revoked, or fails verification.
Such a result remains `HUMAN_DECISION` / `NEED_ACTION` and cannot become `PASS`, `VERIFIED`,
or Human-accepted. Agent/runtime/service credentials cannot be interpreted as Human proof.

## 6. Legacy and overlay disposition

| Item | F4 disposition | Preservation result |
|---|---|---|
| LR-008 document provenance | VERIFIED_BOUNDED_SYNC | Exact F3 paths only; no whole-file overlay adoption. |
| LR-019 migration/restore | REQUIRES_FUTURE_MIGRATION | No schema or migration execution; legacy provenance remains untrusted until separately migrated. |
| LR-020 old G19-G23 routing | SUPERSEDED_PRESERVED | Track A remains the only active routing; accepted historical product bytes are not deleted. |
| LR-040 pre-REV1 HOLD labels | SUPERSEDED_HISTORICAL | Freeze authority controls current state; historical records remain intact. |
| LR-043/LR-044/LR-045 legacy branches | REFERENCE_ONLY | No merge, rebase, checkout, or bulk import. |
| LR-047 dirty formal overlays | PRESERVED_NOT_ADOPTED | Primary dirty checkout is not overwritten, staged, cleaned, or reset. |
| LR-050 mixed untracked overlays | PRESERVED_NOT_ADOPTED | Requires future item-level scope and ownership decisions. |
| G08/G09 | PRESERVE / NEXT / REQUIRES_REVALIDATION | No facts invented and no historical entry removed. |

There is no second active legacy roadmap.

## 7. Migration and compatibility

F3 changed formal text only. Future schema fields, Alembic revisions, deterministic legacy
backfill, representative legacy database rehearsal, backup/restore, downgrade limits, API
surface, and compatibility tests require separately approved implementation Goals. Existing
accepted provenance must not be guessed into trusted Candidate, EvidenceSet, or Human identity.

`M-EXECUTION` remains `NOT REQUIRED / IMPLEMENTATION MAPPING ONLY`. No evidence found in this
document verification requires changing `RuntimeAdapter` or `RuntimeBindingSnapshot`.

## 8. P0/N1 and delivery boundaries

P0 Minimal Portable Accepted Package remains a B01 exit requirement and must reconstruct
accepted source and required acceptance evidence without a provider-private session. N1 full
selected-task portability remains NEXT and does not block B01. REST polling remains the First
Vertical durable delivery; WebSocket remains the optional NEXT live-delivery target.

## 9. Before/after delta preservation

The F3 formal delta is exactly six modified and two added files between `632b5e0...` and
`c4c1792...`. Before/after blob identities and statuses are retained in
`evidence/formal-delta-report.json`; the new L2 package contains a newly generated exact Git
patch and self-contained bundle bound to this remediation Candidate.

## 10. Explicit non-changes

- No edits to the eight accepted F3 formal files or ADR-011.
- No product source, production tests, schema, migrations, runtime, frontend, or workflows.
- No provider/external certification or live vendor verification claim.
- No push, F4 acceptance, F5, S0 start, S0 predecessor assignment, or Product Implementation
  branch.

## 11. Known limitations and requested verdict

This is static formal-document verification. It intentionally does not claim TA-F4 PASS or
acceptance, product/runtime conformance, migration success, UI correctness, provider
certification, or Working Product PASS. Independent L2 Reviewer should return `PASS`,
`NEED_FIX`, or `HOLD` for the exact new Candidate. A PASS is advisory until Human acceptance
and does not itself authorize push, F5, S0, or Product Implementation.
