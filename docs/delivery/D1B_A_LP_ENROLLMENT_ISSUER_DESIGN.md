# D1B / D11-A-LP Local Enrollment Issuer Design Candidate

Status: HUMAN_DESIGN_APPROVED / IMPLEMENTATION_AUTHORIZED / INDEPENDENT_REVIEW_PASS_DECLARED

Date: 2026-09-14 (Asia/Taipei)

Scope: Local-Personal / Single Human only. The Human has approved the design
direction, authorized the implementation, and supplied the separate
independent-review pass declaration. That declaration is recorded as a Human
gate input; it is not an agent-generated reviewer log. This document does not
authorize database migration, Human acceptance, commit, push, merge, release,
or deployment.

## 1. Decision summary

D1B currently has a verifier for an out-of-band enrollment assertion, but no
legitimate enrollment ceremony or issuer. The current environment-backed HMAC
secret is suitable only for isolated protocol fixtures. It must not become the
production Human trust root.

The recommended product design is a separate local A-LP Enrollment Authority
(LEA) backed by a platform user-presence ceremony such as WebAuthn /
Windows Hello:

1. The browser obtains a one-time enrollment challenge from Core.
2. The LEA requires explicit local Human user presence.
3. The LEA signs a short-lived assertion with an OS-protected, non-exportable
   signing key. The initial Windows profile uses ES256 for platform
   compatibility; the algorithm is selected by the registered trust record and
   cannot be downgraded.
4. Core verifies the assertion against a pinned public key and consumes the
   one-time challenge before creating a pairing grant.
5. The existing bounded session, exact-view challenge, nonce, idempotency,
   Origin/CSRF and append-only decision boundaries remain in force.

The authorized D1B implementation profile uses browser-mediated WebAuthn /
Windows Hello directly: the platform authenticator is the cryptographic issuer,
the browser transports the standard WebAuthn response, and Core verifies it.
The separate loopback LEA broker remains a compatible future packaging option,
not an unimplemented dependency or a reason to introduce a custom signed
enrollment envelope in this change.

If the LEA, platform authenticator, trust record, challenge, or verification
state is unavailable or ambiguous, the result remains D11-C
HUMAN_DECISION / NEED_ACTION. There is no automatic HMAC, loopback-token, or
actor-string fallback.

This design does not claim resistance to a malicious process running as the
same Windows OS principal, a hostile-code sandbox, Enterprise IAM compromise,
or legal/regulatory certification. Those boundaries remain the limits stated
by SECURITY.md.

## 2. Required invariants and source authority

The implementation must preserve these existing authorities:

- D11-A-LP requires a Human-only principal; Agent, runtime, service and
  loopback credentials cannot be promoted or aliased to Human.
- Pairing grant, bounded session and single-purpose decision challenge remain
  separate durable objects.
- A challenge binds the exact Candidate, rendered view digest, action,
  policy/evidence revision, session and short-lived nonce.
- Decision submission is atomic with nonce consumption and append-only history.
  Same command and same payload returns the original receipt; a different
  payload conflicts.
- Accept, Reject, Revoke and Supersede retain their current legality; there is
  no override operation.
- Secret values do not enter ordinary Domain records, Evidence, logs, Git,
  exports or P0 packages.
- A-LP failure preserves the D11-C fail-closed state.

Relevant current sources:

- docs/delivery/SECURITY.md
- docs/delivery/SA.md
- docs/delivery/references/formal/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md
- docs/delivery/references/frozen/POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md
- services/core/src/polynexus_core/persistence/d1b.py
- services/core/src/polynexus_core/api/d1b.py
- apps/web/src/components/CandidateReview.tsx

## 3. Trust model

### 3.1 Components

| Component | Responsibility | Must not do |
| --- | --- | --- |
| Browser UI | Display the enrollment ceremony and exact Candidate view; invoke platform user presence | Read private keys, SQLite, source files, or create a Human decision without the protocol |
| Core | Create/consume challenges, verify LEA assertions, create grants and enforce D1B decisions | Mint Human assertions or treat the loopback token as a Human credential |
| Local Enrollment Authority | Own the Human enrollment registry and request platform user presence before signing | Accept an Agent token as user presence or sign an arbitrary caller-supplied principal |
| OS authenticator/key store | Protect the LEA private key and require local user presence | Export the private key to Core, Web UI, Git or an ordinary environment variable |
| Core trust store | Hold public key, key id, algorithm, lifecycle and installation binding | Hold private keys, raw assertions or browser session secrets |

The LEA may be packaged as a small local broker; this does not require a
remote service, Enterprise IAM or a new product microservice topology. The
Core-to-LEA call must be bound to a Core-issued one-time challenge and the
browser UI must use an explicit fixed Origin. A random bearer token alone is
not user presence.

Implementation profile note: the current D1B path keeps the same trust
boundary without a separate broker. `navigator.credentials.create/get` invokes
the local platform authenticator, and the fixed-Origin browser response is sent
to Core's enrollment endpoints. A loopback token still authenticates the local
API caller only; it never becomes the Human credential.

### 3.2 Bootstrap / first enrollment

Bootstrap is a Human-only ceremony and cannot be completed by an Agent:

1. Core generates a cryptographically random registration challenge with a
   short expiry, fixed audience and installation binding.
2. The browser receives the Core-provided RP id, opaque user id and principal
   label, and invokes WebAuthn / Windows Hello with user verification required.
   Cancellation, timeout or unavailable platform support aborts bootstrap.
3. The platform authenticator creates a non-exportable credential protected by
   the OS user-presence mechanism; the browser returns the standard registration
   response, never the private key.
4. Core verifies the exact challenge, Origin, RP id hash, user-presence and
   user-verification flags, and ES256 public-key material before activation.
5. Core stores only the public key, key id, opaque principal reference,
   installation binding, status, sign counter and audit metadata. The private
   key remains in the platform authenticator.
6. Core returns the public-key fingerprint for the local UI to display. The
   user-verification ceremony is the activation confirmation; product UAT must
   still confirm that the Human sees the intended installation before making a
   decision.

The principal reference is generated by the LEA from an opaque random
identifier or credential identifier plus an installation-local salt. It is
not accepted as an arbitrary Human claim from the Agent or browser form.

No import of an existing private key is part of the first implementation.
Backup and restore must not reactivate a revoked key or grant.

## 4. Enrollment assertion contract

The current HMAC v1 fixture format must not be used for product A-LP. The
authorized implementation uses the browser's standard WebAuthn credential
envelope. `pn-d11-a-lp-webauthn-v2` is the internal protocol/evidence format
label; it is not a custom payload that callers can sign:

~~~text
{
  "id": "base64url(credential-id)",
  "rawId": "base64url(credential-id)",
  "type": "public-key",
  "response": {
    "clientDataJSON": "base64url(client-data-json)",
    "attestationObject": "base64url(attestation-object)"
  }
}
~~~

For authentication and revocation, the response instead contains
`authenticatorData`, `signature` and optional `userHandle`. The signed
WebAuthn inputs bind the challenge and Origin; Core binds the remaining
audience, ceremony, installation, key and principal through the persisted
challenge and trust record:

~~~json
{
  "challenge_id": "enrollment-challenge-id",
  "ceremony": "authentication",
  "audience": "polynexus-human-pairing",
  "installation_id": "sha256:...",
  "origin": "http://127.0.0.1:5173",
  "rp_id": "127.0.0.1",
  "expires_at": "2026-09-14T00:05:00+00:00"
}
~~~

Verification rules:

- Resolve key_id from the Core trust store; accept only ACTIVE or an
  explicitly bounded RETIRING key.
- Require the registered ES256 algorithm and reject algorithm substitution or
  downgrade.
- Verify WebAuthn client-data type, exact Origin, exact challenge digest,
  RP-id hash, user-presence and user-verification flags, attestation shape and
  the P-256 signature over `authenticatorData || SHA-256(clientDataJSON)`.
- Require the exact unconsumed challenge, audience, ceremony, installation,
  key and principal binding; consume it in the same transaction that creates
  the pairing grant or changes key state.
- Enforce the five-minute challenge lifetime and the authenticator sign-counter
  rule; unsupported or ambiguous platform responses fail closed.
- Store raw WebAuthn responses only in memory for verification. Persist only
  public trust material, sign count, pairing-token digest, key/challenge
  references and sanitized outcome.
- A pairing-token digest can create at most one grant. Reuse returns a bounded
  replay error and never creates a second grant.

The product implementation accepts `fmt=none` registration only: trust comes
from the required local user-verification ceremony and the resulting public
key, not from an unconfigured vendor-attestation allowlist.

The exact TTL is implementation policy, not a new frozen architecture
constant. The initial design default is two minutes for the enrollment
assertion and five minutes for the enrollment challenge; security review may
adjust bounded values without weakening the invariants.

## 5. Pairing, session and decision flow

The product flow is:

~~~text
Human enrollment
  -> Core one-time enrollment challenge
  -> LEA user-presence assertion
  -> Core verification + pairing grant
  -> bounded/revocable Human session
  -> exact Candidate view + decision challenge
  -> Human review/confirmation
  -> nonce-bound append-only decision
~~~

Pairing proves only that the registered local Human principal completed the
enrollment ceremony. It does not accept a Candidate, open a worktree, commit
source, push Git, or release anything. The existing D1B decision protocol
remains the only path for those product-side Human decisions.

Session restart behavior remains a policy choice under the frozen contract.
The recommended first implementation is to persist the pairing/trust record
but require a new bounded session after Core restart; an unexpired session
must never be revived merely because a database or process restarted.

## 6. Key lifecycle, revocation and recovery

Trust records have explicit lifecycle states:

~~~text
PENDING -> ACTIVE -> RETIRING -> REVOKED
                    \-> COMPROMISED
~~~

- PENDING cannot issue grants.
- ACTIVE can issue bounded assertions.
- RETIRING can finish a bounded overlap window but cannot extend beyond
  policy.
- REVOKED and COMPROMISED cannot issue or validate new assertions.
- Key rotation adds a new public key before retiring the old one; it never
  rewrites old decision history.
- Revoking a principal revokes its active grants and sessions through the
  existing append-only/security lifecycle. It does not mutate old decisions.
- Recovery requires a new Human presence ceremony. There is no silent
  recovery through the loopback token, an imported browser cookie, a database
  row, or a copied proof.
- Security-store backup is separate from ordinary P0/export. Restore must
  preserve revocation state and must fail closed when key status is unknown.

## 7. API and storage delta / implementation profile

The following is the approved design delta and the corresponding D1B profile:

1. Add Core-owned enrollment challenge/status routes with strict loopback and
   fixed-origin checks.
2. Replace the product verifier's single HMAC environment secret with a
   public-key trust registry and key lifecycle records.
3. Add a security-owned enrollment challenge/trust-key/principal boundary.
   Raw private keys, raw proof values, session tokens and nonce values are not
   ordinary domain columns.
4. Keep the current pairing/session/challenge/decision routes compatible at
   the semantic level, while versioning the proof format and rejecting the
   fixture v1 format outside TEST mode.
5. Keep POLYNEXUS_HUMAN_TEST_MODE=1 and synthetic principals TEST_ONLY.
   POLYNEXUS_HUMAN_A_LP_ENABLED=1 must require the real trust store and
   browser-mediated WebAuthn/Windows Hello issuer; it must not enable a test
   secret in LOCAL.

The implementation is limited to the approved local A-LP issuer scope. It does
not authorize migration outside this branch, deployment, production enrollment,
or Human product acceptance.

## 8. Required negative and recovery evidence

The implementation cannot advance to product acceptance without deterministic
oracles for at least:

| Case | Required result |
| --- | --- |
| Loopback token only, no A-LP assertion | Pairing denied; no grant |
| Fake, altered or HMAC-only assertion in LOCAL | Denied; no trust elevation |
| Altered principal, audience, origin, installation or challenge | Denied |
| Expired, future-skewed or wrong-key assertion | Denied |
| Same proof submitted twice | One grant only; replay error |
| LEA user cancels or does not complete user presence | No assertion/grant |
| Revoked/compromised key or principal | New pairing denied |
| Core restart during enrollment | Challenge remains single-use and bounded |
| Restore from a backup before revocation | Revocation cannot be silently undone |
| Cross-Origin or unknown local broker | Denied |
| Stale Candidate view or policy/evidence revision | Decision denied |
| Same command and same payload retry | Original receipt only |
| Same nonce with a different command, action or Candidate | challenge_replayed or conflict |
| Raw proof/private key/session/nonce in logs, DB export or P0 | Must not occur |

Tests must include unit vectors, Core/LEA integration, browser user-presence
UAT, restart/revocation/rotation, and the existing D1B affected/full suites.
Fixture success is evidence of protocol mechanics only and cannot become
Human product acceptance.

## 9. Governance and rollout gates

The pre-implementation gates are recorded as satisfied by the Human decision
record below. The remaining rollout gates are:

1. Complete the isolated implementation and its source/schema review.
2. Run targeted, affected-regression and relevant-full validation.
3. Complete real Human browser UAT and obtain explicit Human product
   acceptance.

Implementation sequence:

1. Pure assertion/trust-key vectors and fail-closed verifier.
2. Core challenge/trust registry and migration.
3. Browser enrollment/re-pair/revoke UX.
4. Targeted, affected-regression and relevant-full validation.
5. Fresh security review and real Human UAT.

Rollback is feature disablement to D11-C fail closed. It must not restore the
old shared-HMAC path as a production fallback, invalidate historical
append-only decisions, or mutate accepted source records.

## 10. Resolved profile and remaining Human gate

The authorized profile resolves the principal implementation choices as follows:

1. Windows Hello/WebAuthn user verification is required; unsupported or
   unavailable hosts produce A_LP_UNAVAILABLE / D11-C.
2. The initial algorithm is ES256 with a platform-protected non-exportable
   credential.
3. Transport is fixed-Origin browser-to-Core; a separate broker is deferred
   unless a later authorized change preserves the same bindings.
4. Trust keys persist with a bounded 15-minute rotation overlap; revocation
   invalidates grants and sessions immediately.
5. Pairing trust persists, while application restart requires a new bounded
   Human session.

The remaining Human gate is product UAT and explicit Human product acceptance;
the independent-review pass declaration is not that acceptance.

No choice above permits Enterprise IAM, arbitrary Agent self-pairing, hidden
automatic approval, or weakening the D11-C fallback.

## 11. External standards evidence

These sources support the protocol choices but do not prove PolyNexus
implementation or product acceptance:

- W3C WebAuthn Level 3 describes user-agent-mediated public-key credentials,
  RP-scoped credentials, server-generated unpredictable challenges, and
  mandatory verification of the expected Origin:
  https://www.w3.org/TR/webauthn-3/
- Microsoft documents Windows WebAuthn APIs for Windows Hello and FIDO2
  authenticators, including user verification:
  https://learn.microsoft.com/en-us/windows/security/identity-protection/hello-for-business/webauthn-apis
- Microsoft documents CNG key-storage providers and the Platform Crypto
  Provider for OS/TPM-backed asymmetric key storage:
  https://learn.microsoft.com/en-us/windows/win32/seccertenroll/cng-key-storage-providers

The implementation must verify the supported host and provider capabilities at
the start gate. An unavailable platform authenticator is an explicit
A_LP_UNAVAILABLE / D11-C result, not permission to fall back to an
environment-backed test secret.
