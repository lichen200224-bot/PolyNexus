# D11-A-LP — Local-Personal Human Decision Protocol

Status: HUMAN_ACCEPTED / FORMAL_SYNC

Date: 2026-09-11

Implementation: NOT_IMPLEMENTED / NOT_AUTHORIZED

## Decision boundary

D11 adopts `A-LP` for the Local-Personal boundary. A Human decision is eligible for acceptance
only when the principal is authenticated as Human through the approved local-personal
protocol. Agent/runtime/service credentials are separate and MUST NOT be promoted, aliased,
prefixed, or interpreted as Human credentials. If the A-LP boundary is unavailable,
ambiguous, expired, revoked, or fails verification, D11 Option C remains the mandatory
fail-closed fallback: the result remains `HUMAN_DECISION` / `NEED_ACTION` and MUST NOT become
`PASS`, `VERIFIED`, or Human-accepted.

## Protocol records

Pairing grant, bounded Human session, and per-decision challenge are distinct objects and MUST
NOT be collapsed. A pairing grant creates no decision. A session is bounded and revocable and
creates no decision. A decision challenge is single-purpose and binds the Human action to the
exact rendered Candidate view, exact `CandidateID`, decision kind, nonce, and current
eligibility context.

## Exact-view binding

The protocol MUST provide unpredictable nonce and anti-replay validation, idempotent decision
submission, CSRF defense, and Origin validation appropriate to the local browser boundary.
Reuse, cross-Candidate substitution, stale challenge, wrong Origin, revoked session, or
mismatched exact view fails closed. The accepted decision log is append-only and records
Human principal reference, exact Candidate/view binding, decision kind, time, and protocol
evidence without storing secret values.

## Decision history

Allowed Human decision kinds are `Accept`, `Reject`, `Revoke`, and `Supersede`. `Reject` is
pre-acceptance only. `Revoke` and `Supersede` are post-acceptance append-only actions. There is
no `Override Accept` operation.

## Deliberately unfrozen choices

This amendment freezes the trust semantics, not a particular implementation. It does not
freeze TTL values, mandatory restart re-pairing, a session-storage mechanism, Enterprise IAM,
or hardware attestation.

## Compatibility, migration, and tests

This formal sync does not add an authentication subsystem, endpoint, schema, migration, or
product implementation. Future authorized work must preserve D11-C compatibility and test
principal separation, bounded/revocable sessions, exact-view binding, nonce anti-replay,
idempotency, CSRF/Origin enforcement, and append-only Accept/Reject/Revoke/Supersede history.

## Preserved boundaries

The P0/N1 boundary, REST/WebSocket transport boundary, fixed workflow vocabulary,
`RuntimeAdapter` public contract, and `RuntimeBindingSnapshot` semantics are unchanged.
F4, S0, and Product Implementation remain not authorized.
