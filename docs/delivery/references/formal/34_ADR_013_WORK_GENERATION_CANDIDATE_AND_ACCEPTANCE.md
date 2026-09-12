# ADR-013 — Work Generation, Candidate, Verification, and Acceptance

Status: HUMAN_ACCEPTED / FORMAL_SYNC

Date: 2026-09-11

Implementation: NOT_IMPLEMENTED / NOT_AUTHORIZED

## Context

The frozen architecture requires durable identity, evidence, verification, and Human
acceptance semantics without collapsing lifecycle concepts or treating an AI opinion as
deterministic proof. This ADR formalizes the exact contract approved at TA-F2. It does not
authorize product implementation.

## Decision

### Identity separation and reference

A `WorkGenerationRef` is the stable pair `(TaskID, generation_revision)`. A control revision
is not a generation revision. `Task`, `WorkGeneration`, `Run`, and `Candidate` are distinct
identities: a Task may have multiple generations; a WorkGeneration may have multiple Runs;
a Candidate is a frozen publication derived from exactly one WorkGeneration and identified
by its own `CandidateID`. An implementation MUST NOT introduce an `Attempt Aggregate`; Run
remains the durable execution identity without freezing `Run == Attempt`.

Within one WorkGeneration, all writer actions MUST remain in the same writer lineage.
Different command IDs, APIs, reconnects, retries, or transports MUST NOT create unrelated
writer lineages for the same generation. A new writer lineage requires a new generation
according to the accepted contract.

### Model B and REV1 Golden authority

Model B is authoritative. Core derives the `Snapshot` and `ChangeSet` from a verified baseline
snapshot and verified result snapshot. Caller claims, UI labels, submitted diff text, or
runtime/vendor session data are not identity truth. `SnapshotID`, `ChangeSetID`, `CandidateID`,
and `EvidenceSetID` are generated and verified by the canonical REV1 Golden identity authority;
downstream documents MUST reference that authority and MUST NOT redefine canonicalization or
recompute the identifiers independently.

### Exact verification binding

Candidate publication freezes the exact WorkGeneration, writer lineage, verified
Snapshot/ChangeSet, artifacts, and policy-relevant provenance. Candidate verification and
every accepted EvidenceSet MUST bind to the exact `CandidateID` and the exact frozen content.
Evidence from another Candidate, mutable workspace, unverified diff, or historical run cannot
satisfy the Candidate.

### Applicability and outcome

Requirement applicability and verification outcome are separate. Applicability is `REQUIRED`,
`OPTIONAL`, or `N/A`; outcome is recorded independently. `N/A` is valid only when a trusted
deterministic predicate and its evidence establish non-applicability. A required item cannot
be omitted, downgraded, or converted to `N/A` by a caller, UI, agent opinion, or missing
evidence.

### Candidate lifecycle and Human acceptance history

`Reject` applies only before a Candidate has ever been accepted. After acceptance, history is
append-only: an accepted decision is never overwritten or relabeled. A later Human action is
`Revoke` or `Supersede`, with a new append-only decision record that references the prior
accepted decision and exact Candidate.

## Alternatives rejected

- Collapsing Task, WorkGeneration, Run, or Candidate identity.
- Introducing an Attempt aggregate or changing frozen workflow vocabulary.
- Allowing cross-generation writer artifacts to satisfy Candidate lineage.
- Treating `N/A` as a successful verification outcome.
- Mutating or deleting an accepted Human decision.

## Compatibility and migration impact

This formal sync preserves existing public runtime contracts. Future implementation may add
identity/reference fields and deterministic legacy backfill only through separately approved
schema, migration, compatibility, and rollback work. Existing accepted provenance remains
preserved and is not silently reclassified.

## Test impact

Future authorized implementation must test identity separation, same-generation lineage,
Candidate immutability, exact Candidate/EvidenceSet binding, applicability semantics,
acceptance eligibility, and append-only Reject/Revoke/Supersede transitions. These tests are
not authorized by this ADR sync.

## Preserved boundaries

- `M-EXECUTION`: `NOT REQUIRED / IMPLEMENTATION MAPPING ONLY`.
- No change to the `RuntimeAdapter` public contract or `RuntimeBindingSnapshot` semantics.
- P0/N1 boundary, REST/WebSocket boundary, and fixed workflow vocabulary remain unchanged.
- Product implementation, F4, and S0 are not authorized by this document.

## Rollback and supersession

Before implementation, rollback is document restoration to the F3 predecessor. After Human
acceptance, substantive replacement requires a new ADR that explicitly supersedes this one;
historical decision and acceptance records remain append-only.
