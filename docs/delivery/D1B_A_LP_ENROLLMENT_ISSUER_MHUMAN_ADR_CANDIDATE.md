# D1B / D11-A-LP Enrollment Issuer — M-HUMAN / ADR Candidate

Status: HUMAN_DESIGN_APPROVED / IMPLEMENTATION_AUTHORIZED / INDEPENDENT_REVIEW_PASS_DECLARED

This document is a decision packet for the lawful local enrollment issuer required
by D11-A-LP. The Human has approved the design, authorized the isolated
implementation, and supplied the independent-review pass declaration recorded
below. This document does not itself authorize migration, deployment,
production enrollment, or Human product acceptance.

## 1. Scope and current gap

The supported target is a local-personal, single-Human installation of
PolyNexus. This packet does not claim resistance to a malicious same-OS
principal, a hostile sandbox, or Enterprise IAM compromise. Enterprise identity,
hardware-attestation policy, and multi-tenant administration remain out of scope.

The current D1b technical path proves the pairing/session/challenge/nonce
protocol with a TEST_ONLY fixture issuer. The fixture proof is not a lawful
production enrollment issuer. In particular, the existing
POLYNEXUS_HUMAN_A_LP_ENROLLMENT_SECRET path must remain TEST_ONLY and must not
become a production shared-HMAC trust root.

The missing product decision is how a real local Human enrollment creates the
first trusted A-LP public key and how Core verifies later Human proofs.

## 2. Proposed decision

Adopt a Local Enrollment Authority (LEA) backed by platform user presence:

1. The local Human completes Windows Hello/WebAuthn user verification in the
   local enrollment UI.
2. The browser-mediated platform authenticator creates a non-exportable
   credential in an OS-protected key store. The selected algorithm is ES256.
3. Core creates a fresh enrollment or protocol challenge and binds it to the
   installation, exact audience, fixed browser Origin, Human principal, expiry,
   and one-time-use record.
4. The platform authenticator signs the exact challenge-bound WebAuthn
   assertion. Core stores the public key and enrollment metadata, never the
   private key or a reusable secret.
5. The existing semantic sequence remains distinct:
   pairing establishes trust, session establishes a bounded authorization
   context, challenge binds the exact view/candidate/revisions, and the Human
   decision produces the append-only acceptance record.
6. If platform user presence or the LEA is unavailable, the system fails closed
   with A_LP_UNAVAILABLE and follows D11-C. There is no temporary accept channel.

The authorized implementation profile is standard browser-mediated WebAuthn /
Windows Hello with ES256. The D1b v1 HMAC fixture is retained only for
TEST_ONLY validation and is not accepted by the LOCAL production path. The
internal `pn-d11-a-lp-webauthn-v2` label identifies this protocol profile; it
does not introduce a caller-signed custom assertion envelope.

## 3. Recommended binding and lifecycle rules

The authorized implementation must enforce all of the following:

- challenge freshness, unpredictability, expiry, one-time use, and replay
  rejection;
- exact installation, audience, fixed Origin, Human principal, protocol
  version, and displayed-view/candidate/revision binding;
- explicit key state transitions ACTIVE, RETIRING, REVOKED, and COMPROMISED;
- controlled rotation with an auditable replacement chain;
- immediate revocation that invalidates new proof verification;
- no private-key export, no proof generation by an Agent, and no elevation from
  an actor string, loopback possession, or UI-supplied principal;
- no secret, private key, session token, challenge nonce, or proof value in
  ordinary evidence, export, logs, or queryable domain data;
- a D11-C fail-closed path for unsupported platform, unavailable browser
  authenticator, verification failure, or uncertain enrollment state.

Recommended restart behavior: persist the pairing trust record, but require a
new Human session after application restart. A previously active session must
not silently become a fresh acceptance authority.

Selected transport: a fixed-Origin local browser UI using the browser-mediated
WebAuthn API directly with Core. A separate broker or named-pipe adapter is
deferred; any later transport must preserve the same installation, challenge,
Origin and user-presence bindings.

## 4. Alternatives considered

### 4.1 Shared HMAC enrollment secret

Rejected for production. An environment or process secret is copyable by the
local Agent/runtime boundary and cannot prove a distinct Human presence. It may
remain a deterministic TEST_ONLY fixture under explicit test flags.

### 4.2 Loopback token, actor string, or UI checkbox

Rejected. Possession of localhost, an arbitrary actor identifier, or a
client-controlled confirmation is not a Human-only enrollment issuer and does
not establish a trusted public-key root.

### 4.3 Agent-generated Human proof

Rejected. The Agent may prepare a review and submit a challenge request, but it
must never create the Human enrollment assertion or upgrade its own authority.

### 4.4 Enterprise IAM or hardware attestation

Deferred and out of scope for this local-personal milestone. It would change the
identity, provisioning, recovery, and operational contracts and requires a
separate architecture and policy decision.

## 5. Minimum acceptance criteria before implementation can be accepted

The implementation must not be called complete until evidence demonstrates:

1. A real local Human can enroll with the selected platform user-presence
   mechanism and Core records only the public trust material and auditable
   metadata.
2. The exact challenge, Origin, audience, installation, principal, candidate,
   displayed view, and revisions are verified.
3. Expired, malformed, wrong-origin, wrong-audience, wrong-installation,
   wrong-principal, altered-view, altered-candidate, altered-revision, replayed,
   revoked, rotated, and unavailable-issuer proofs fail closed.
4. Key rotation, revocation, recovery, application restart, and uncertain
   enrollment states have deterministic outcomes and append-only evidence.
5. No private key or reusable enrollment secret appears in source, environment,
   ordinary logs, evidence, exports, or domain records.
6. Browser/UI UAT demonstrates that the Human sees the exact review target and
   cannot accept a different target through a stale or substituted challenge.
7. D11-C behavior is exercised when the platform, broker, or issuer is
   unavailable; no fallback produces a Human acceptance.
8. Independent design review and targeted, affected-regression, and relevant
   full validation pass on the authorized implementation branch.

## 6. Explicit Human decision block

The following values record the selected profile and are not a production
deployment authorization.

~~~
DESIGN_DECISION = APPROVE | REVISE | REJECT
PLATFORM = WINDOWS_HELLO_WEBAUTHN_REQUIRED | OTHER
SIGNATURE = ES256
TRANSPORT = FIXED_ORIGIN_BROWSER_MEDIATED_WEBAUTHN
RESTART = PERSIST_TRUST_REPAIR_SESSION
IMPLEMENTATION_AUTHORIZATION = GRANTED
INDEPENDENT_REVIEW = PASS_DECLARED_BY_HUMAN
~~~

Any future REVISE request must be recorded before changing the implementation
profile. The recorded approval and implementation authorization are limited to
the isolated local A-LP issuer scope; they do not authorize production state.

## 7. Governance gates

The gates are intentionally separate:

1. Human decision on this M-HUMAN / ADR candidate — recorded.
2. Independent design review against D11-A-LP, D11-C, security, recovery, and
   compatibility constraints — pass declared by the Human below.
3. Explicit implementation authorization naming the permitted branch/scope —
   recorded below.
4. Product implementation and verification on an isolated branch — covered by
   the validation evidence for this turn.
5. Human-only UAT and explicit Human product acceptance — still pending.

No agent, fixture principal, technical smoke test, or design approval can
substitute for step 5.

## 8. Human decision record

Decision: APPROVED

Decision token: A_LP_DESIGN_APPROVE

Decision date: 2026-09-14

The Human approved the proposed local enrollment issuer design direction:
Windows Hello/WebAuthn user presence, ES256, an OS-protected non-exportable
private key, Core-held public-key trust material, fixed-Origin browser-mediated
WebAuthn transport, with a separate broker deferred,
persisted pairing trust with a new session after restart, and D11-C fail-closed
behavior.

This approval does not by itself approve a formal contract amendment or
constitute Human product acceptance. The Human later supplied the separate
implementation authorization and independent-review pass declaration below.

~~~
HUMAN_DESIGN_APPROVAL = GRANTED
IMPLEMENTATION_AUTHORIZATION = GRANTED
IMPLEMENTATION_AUTHORIZATION_TOKEN = A_LP_IMPLEMENTATION_AUTHORIZE
IMPLEMENTATION_SCOPE = APPROVED_LOCAL_A_LP_ISSUER_ONLY
INDEPENDENT_REVIEW_TOKEN = A_LP_INDEPENDENT_REVIEW_PASS
INDEPENDENT_REVIEW_EVIDENCE = HUMAN_GATE_DECLARATION; NO_AGENT_GENERATED_REVIEW_LOG
PRODUCT_START_ALLOWED = YES_FOR_ISOLATED_IMPLEMENTATION_ONLY
HUMAN_PRODUCT_ACCEPTANCE = NOT_DECLARED
~~~

The independent-review token was supplied by the Human on 2026-09-14. It is
recorded as a gate declaration and does not claim an independent reviewer log
generated by the Agent. It also does not authorize migration, deployment,
production enrollment, or Human product acceptance.

## 9. References

- Candidate design:
  docs/delivery/D1B_A_LP_ENROLLMENT_ISSUER_DESIGN.md
- Formal A-LP protocol:
  docs/delivery/references/formal/35_D11_A_LP_LOCAL_HUMAN_DECISION_PROTOCOL.md
- Formal M-HUMAN amendment plan:
  docs/delivery/references/frozen/POLYNEXUS_FORMAL_CONTRACT_ADR_CHANGE_PLAN.md
- W3C WebAuthn Level 3:
  https://www.w3.org/TR/webauthn-3/
- Microsoft WebAuthn APIs:
  https://learn.microsoft.com/en-us/windows/security/identity-protection/hello-for-business/webauthn-apis
- Microsoft CNG Key Storage Providers:
  https://learn.microsoft.com/en-us/windows/win32/seccertenroll/cng-key-storage-providers

The external standards are design evidence only. They do not constitute product
implementation, authorization, or Human acceptance.
