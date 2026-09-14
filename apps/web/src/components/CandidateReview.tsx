import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type {
  ApiClientConfig,
  CandidateView,
  DecisionChallenge,
  HumanEnrollmentChallenge,
  HumanPairing,
  HumanSession,
  WebAuthnCredential,
} from '../api'
import {
  ApiError,
  AuthError,
  createHumanPairing,
  createHumanSession,
  getCandidateView,
  issueHumanEnrollmentChallenge,
  issueDecisionChallenge,
  registerHumanCredential,
  revokeHumanSession,
  submitHumanDecision,
} from '../api'
import { StatusMessage } from './StatusMessage'

interface CandidateReviewProps {
  config: ApiClientConfig
  candidateId: string
  onBack: () => void
}

function textValue(value: unknown): string {
  return typeof value === 'string' ? value : JSON.stringify(value)
}

function randomToken(): string {
  const cryptoApi = globalThis.crypto
  if (typeof cryptoApi?.randomUUID === 'function') {
    return cryptoApi.randomUUID()
  }
  if (!cryptoApi) throw new Error('secure_randomness_unavailable')
  const bytes = new Uint8Array(24)
  cryptoApi.getRandomValues(bytes)
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
}

function decodeBase64Url(value: string): ArrayBuffer {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - (value.length % 4)) % 4)
  const binary = window.atob(normalized)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index)
  return bytes.buffer
}

function encodeBase64Url(value: ArrayBuffer): string {
  const bytes = new Uint8Array(value)
  let binary = ''
  for (const byte of bytes) binary += String.fromCharCode(byte)
  return window.btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function serializeBrowserCredential(credential: PublicKeyCredential): WebAuthnCredential {
  const response = credential.response
  const serialized: WebAuthnCredential = {
    id: credential.id,
    rawId: encodeBase64Url(credential.rawId),
    type: 'public-key',
    response: {
      clientDataJSON: encodeBase64Url(response.clientDataJSON),
    },
  }
  if ('attestationObject' in response) {
    const attestationResponse = response as AuthenticatorAttestationResponse
    serialized.response.attestationObject = encodeBase64Url(attestationResponse.attestationObject)
  } else if ('authenticatorData' in response && 'signature' in response) {
    const assertionResponse = response as AuthenticatorAssertionResponse
    serialized.response.authenticatorData = encodeBase64Url(assertionResponse.authenticatorData)
    serialized.response.signature = encodeBase64Url(assertionResponse.signature)
    if (assertionResponse.userHandle) serialized.response.userHandle = encodeBase64Url(assertionResponse.userHandle)
  } else {
    throw new Error('webauthn_response_invalid')
  }
  return serialized
}

function requireWebAuthn(): void {
  if (typeof window.PublicKeyCredential === 'undefined' || !navigator.credentials) {
    throw new Error('webauthn_unavailable')
  }
}

function apiErrorDetail(reason: unknown): string | null {
  if (!(reason instanceof ApiError) || typeof reason.body !== 'string') return null
  try {
    const body = JSON.parse(reason.body) as { detail?: unknown }
    return typeof body.detail === 'string' ? body.detail : null
  } catch {
    return null
  }
}

interface PreparedHumanChallenge {
  challenge: HumanEnrollmentChallenge
  enrolledFingerprint: string | null
}

interface HumanChallengeResult {
  grant: HumanPairing | null
  nextChallenge: HumanEnrollmentChallenge | null
  enrolledFingerprint: string | null
}

async function prepareHumanChallenge(config: ApiClientConfig): Promise<PreparedHumanChallenge> {
  requireWebAuthn()
  try {
    // Re-pairing an already enrolled installation needs only a fresh
    // user-verification assertion.  Authentication is attempted first so a
    // normal session does not rotate the trust key on every visit.
    return {
      challenge: await issueHumanEnrollmentChallenge(config, { ceremony: 'authentication' }),
      enrolledFingerprint: null,
    }
  } catch (reason) {
    if (apiErrorDetail(reason) !== 'human_enrollment_required') throw reason
    const registration = await issueHumanEnrollmentChallenge(config, { ceremony: 'registration' })
    if (!registration.user_id || !registration.principal_ref) throw new Error('enrollment_response_invalid')
    return { challenge: registration, enrolledFingerprint: null }
  }
}

async function performHumanChallenge(
  config: ApiClientConfig,
  prepared: PreparedHumanChallenge,
): Promise<HumanChallengeResult> {
  requireWebAuthn()
  const { challenge } = prepared
  if (challenge.ceremony === 'registration') {
    // Keep this call before any awaited network operation.  Windows Hello and
    // other platform authenticators may require the current user gesture.
    const created = await navigator.credentials.create({
      publicKey: {
        challenge: decodeBase64Url(challenge.challenge),
        rp: { id: challenge.rp_id, name: 'PolyNexus' },
        user: {
          id: decodeBase64Url(challenge.user_id!),
          name: challenge.principal_ref!,
          displayName: 'Local Human',
        },
        pubKeyCredParams: [{ type: 'public-key', alg: -7 }],
        authenticatorSelection: { userVerification: 'required', residentKey: 'preferred' },
        timeout: 120000,
        attestation: 'none',
      },
    })
    if (!(created instanceof PublicKeyCredential)) throw new Error('webauthn_registration_cancelled')
    const registered = await registerHumanCredential(config, {
      challenge_id: challenge.challenge_id,
      credential: serializeBrowserCredential(created),
    })
    return {
      grant: null,
      nextChallenge: await issueHumanEnrollmentChallenge(config, { ceremony: 'authentication' }),
      enrolledFingerprint: registered.fingerprint,
    }
  }

  if (challenge.ceremony !== 'authentication') throw new Error('human_challenge_invalid')
  // As with registration, this must be reached directly from the second
  // user click rather than after an awaited challenge request.
  const assertion = await navigator.credentials.get({
    publicKey: {
      challenge: decodeBase64Url(challenge.challenge),
      rpId: challenge.rp_id,
      allowCredentials: challenge.allow_credentials.map((item) => ({
        id: decodeBase64Url(item.id),
        type: 'public-key' as const,
      })),
      userVerification: 'required',
      timeout: 120000,
    },
  })
  if (!(assertion instanceof PublicKeyCredential)) throw new Error('webauthn_authentication_cancelled')
  const grant = await createHumanPairing(config, {
    challenge_id: challenge.challenge_id,
    credential: serializeBrowserCredential(assertion),
    expires_at: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
  })
  return { grant, nextChallenge: null, enrolledFingerprint: prepared.enrolledFingerprint }
}

function protocolError(reason: unknown): string {
  if (reason instanceof AuthError) return 'Human protocol unavailable: authentication or the explicit A-LP deployment flag is missing.'
  if (reason instanceof ApiError) return `Human protocol request failed (${reason.status}). Check the server-side A-LP configuration and the supplied proof.`
  if (reason instanceof Error && reason.message === 'webauthn_unavailable') return 'This browser or host has no supported WebAuthn / Windows Hello authenticator.'
  if (reason instanceof Error && reason.message.includes('cancelled')) return 'The Human cancelled or did not complete the platform verification; no pairing was created.'
  if (reason instanceof Error && reason.name === 'NotAllowedError') return 'Windows Hello was cancelled, timed out, or the browser rejected the user gesture; no pairing was created. Prepare a new challenge and try the continuation button again.'
  if (reason instanceof Error && reason.name === 'SecurityError') return 'WebAuthn rejected this Origin or relying-party configuration; no pairing was created.'
  return 'Human protocol request failed.'
}

export function CandidateReview({ config, candidateId, onBack }: CandidateReviewProps) {
  const [view, setView] = useState<CandidateView | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pairing, setPairing] = useState<HumanPairing | null>(null)
  const [session, setSession] = useState<HumanSession | null>(null)
  const [csrfToken, setCsrfToken] = useState<string | null>(null)
  const [action, setAction] = useState<DecisionChallenge['action']>('Accept')
  const [reason, setReason] = useState('')
  const [replacementAcceptanceId, setReplacementAcceptanceId] = useState('')
  const [challenge, setChallenge] = useState<DecisionChallenge | null>(null)
  const [challengeView, setChallengeView] = useState<CandidateView | null>(null)
  const [humanBusy, setHumanBusy] = useState(false)
  const [humanError, setHumanError] = useState<string | null>(null)
  const [humanNotice, setHumanNotice] = useState<string | null>(null)
  const [humanChallenge, setHumanChallenge] = useState<HumanEnrollmentChallenge | null>(null)
  const [humanEnrollmentFingerprint, setHumanEnrollmentFingerprint] = useState<string | null>(null)

  const load = () => {
    setLoading(true)
    setError(null)
    getCandidateView(config, candidateId)
      .then(setView)
      .catch((reason) => {
        if (reason instanceof AuthError) setError('Authentication required')
        else if (reason instanceof ApiError && reason.status === 404) setError('Candidate view unavailable')
        else setError('Unable to load the exact Candidate view')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [config, candidateId])

  const pairHuman = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setHumanBusy(true)
    setHumanError(null)
    setHumanNotice(null)
    try {
      if (!humanChallenge) {
        const prepared = await prepareHumanChallenge(config)
        setHumanChallenge(prepared.challenge)
        setHumanEnrollmentFingerprint(prepared.enrolledFingerprint)
        setHumanNotice(prepared.challenge.ceremony === 'registration'
          ? 'Registration challenge ready. Click Continue with Windows Hello to start the platform prompt.'
          : 'Authorization challenge ready. Click Authorize with Windows Hello to start the platform prompt.')
        return
      }

      const flow = await performHumanChallenge(config, {
        challenge: humanChallenge,
        enrolledFingerprint: humanEnrollmentFingerprint,
      })
      if (flow.nextChallenge) {
        setHumanChallenge(flow.nextChallenge)
        setHumanEnrollmentFingerprint(flow.enrolledFingerprint)
        setHumanNotice(`Credential enrolled with public-key fingerprint ${flow.enrolledFingerprint}. Click Authorize with Windows Hello to continue.`)
        return
      }
      if (!flow.grant) throw new Error('pairing_missing')
      const grant = flow.grant
      if (!grant.pairing_token) throw new Error('pairing_token_missing')
      const csrf = randomToken()
      const nextSession = await createHumanSession(config, {
        grant_id: grant.grant_id,
        pairing_token: grant.pairing_token,
        audience: 'candidate-review',
        csrf_token: csrf,
        expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString(),
      })
      setPairing(grant)
      setSession(nextSession)
      setCsrfToken(csrf)
      setChallenge(null)
      setChallengeView(null)
      setHumanChallenge(null)
      setHumanEnrollmentFingerprint(null)
      const enrollmentNotice = flow.enrolledFingerprint
        ? `Credential enrolled with public-key fingerprint ${flow.enrolledFingerprint}. `
        : ''
      setHumanNotice(`${enrollmentNotice}Local-personal Human session active for ${nextSession.expires_at}.`)
    } catch (reasonValue) {
      setHumanError(protocolError(reasonValue))
    } finally {
      setHumanBusy(false)
    }
  }

  const issueChallengeForReview = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!view || !session || !csrfToken) {
      setHumanError('Pair a Human session before submitting a decision.')
      return
    }
    if (challenge) {
      setHumanError('Review or cancel the existing exact-view challenge first.')
      return
    }
    if (action !== 'Accept' && !reason.trim()) {
      setHumanError('A reason is required for Reject, Revoke, and Supersede.')
      return
    }
    if (action === 'Supersede' && !replacementAcceptanceId.trim()) {
      setHumanError('Supersede requires the accepted replacement acceptance ID.')
      return
    }
    setHumanBusy(true)
    setHumanError(null)
    setHumanNotice(null)
    try {
      const nextChallenge = await issueDecisionChallenge(config, {
        session_id: session.session_id,
        candidate_id: candidateId,
        action,
        replacement_acceptance_id: action === 'Supersede' ? replacementAcceptanceId.trim() : null,
        policy_revision: view.policy_revision,
      })
      const nextChallengeView = await getCandidateView(config, candidateId, view.policy_revision)
      if (nextChallengeView.view_digest !== nextChallenge.view_digest) {
        throw new Error('stale_candidate_view')
      }
      setChallenge(nextChallenge)
      setChallengeView(nextChallengeView)
      setHumanNotice(`Challenge issued. Review exact view ${nextChallenge.view_digest}, then confirm explicitly.`)
    } catch (reasonValue) {
      setHumanError(reasonValue instanceof Error && reasonValue.message === 'stale_candidate_view'
        ? 'The Candidate view changed while issuing the challenge. Refresh and issue a new challenge.'
        : protocolError(reasonValue))
    } finally {
      setHumanBusy(false)
    }
  }

  const confirmDecision = async () => {
    if (!session || !csrfToken || !challenge || !challengeView) {
      setHumanError('Issue and review an exact-view challenge before confirming.')
      return
    }
    setHumanBusy(true)
    setHumanError(null)
    setHumanNotice(null)
    try {
      const receipt = await submitHumanDecision(config, {
        session_id: session.session_id,
        challenge_id: challenge.challenge_id,
        nonce: challenge.nonce,
        action: challenge.action,
        candidate_id: candidateId,
        view_digest: challengeView.view_digest,
        csrf_token: csrfToken,
        origin: window.location.origin,
        command_id: `candidate-review-${randomToken()}`,
        reason: challenge.action === 'Accept' ? null : reason.trim(),
        policy_revision: challengeView.policy_revision,
        replacement_acceptance_id: challenge.action === 'Supersede' ? replacementAcceptanceId.trim() : null,
      })
      setHumanNotice(`${receipt.disposition}: ${receipt.decision_id}`)
      setChallenge(null)
      setChallengeView(null)
      await load()
    } catch (reasonValue) {
      setHumanError(protocolError(reasonValue))
    } finally {
      setHumanBusy(false)
    }
  }

  const endSession = async () => {
    if (!session || !csrfToken) return
    setHumanBusy(true)
    setHumanError(null)
    try {
      await revokeHumanSession(config, session.session_id, { csrf_token: csrfToken })
      setSession(null)
      setPairing(null)
      setCsrfToken(null)
      setChallenge(null)
      setChallengeView(null)
      setHumanNotice('Human session revoked on the server.')
    } catch (reasonValue) {
      setHumanError(protocolError(reasonValue))
    } finally {
      setHumanBusy(false)
    }
  }

  if (loading) return <StatusMessage kind="loading">Loading exact Candidate view...</StatusMessage>
  if (error) {
    return (
      <StatusMessage kind={error === 'Authentication required' ? 'permission' : 'error'} title={error} action={<button type="button" onClick={load}>Retry</button>}>
        <button type="button" className="back-link" onClick={onBack}>Back to projects</button>
      </StatusMessage>
    )
  }
  if (!view) return null

  const verification = view.verification
  const assurance = view.assurance
  return (
    <section className="candidate-review" aria-labelledby="candidate-review-heading">
      <div className="section-header">
        <div>
          <button type="button" className="back-link" onClick={onBack}>Back to projects</button>
          <p className="label">Exact Candidate view</p>
          <h2 id="candidate-review-heading">{view.candidate_id}</h2>
        </div>
        <button type="button" onClick={load} disabled={humanBusy || challenge !== null}>Refresh</button>
      </div>
      <dl className="candidate-facts">
        <div><dt>View digest</dt><dd>{view.view_digest}</dd></div>
        <div><dt>Disposition</dt><dd>{view.disposition.state}</dd></div>
        <div><dt>Acceptance</dt><dd>{view.disposition.acceptance_id ?? 'none'}</dd></div>
        <div><dt>Assurance mode/status</dt><dd>{assurance ? `${textValue(assurance.mode)} / ${textValue(assurance.status)}` : 'UNREVIEWED'}</dd></div>
        <div><dt>Verification outcome</dt><dd>{verification ? textValue(verification.outcome) : 'UNREVIEWED'}</dd></div>
        <div><dt>Acceptance eligible</dt><dd>{verification ? (verification.acceptance_eligible ? 'yes' : 'no') : 'no'}</dd></div>
        <div><dt>Evidence set</dt><dd>{view.evidence_set_id ?? 'none'}</dd></div>
        <div><dt>Eligibility revision</dt><dd>{view.eligibility_revision}</dd></div>
        <div><dt>Review / decision revision</dt><dd>{view.review_round} / {view.decision_revision}</dd></div>
      </dl>
      {view.missing_reasons.length > 0 && (
        <div className="review-warning" role="status">
          <strong>Missing or blocking reasons</strong>
          <ul>{view.missing_reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
        </div>
      )}
      <div className="candidate-actions" aria-live="polite">
        <strong>Human decision</strong>
        <p>Local-personal pairing uses a fresh WebAuthn / Windows Hello user-verification ceremony. The private key stays in the platform authenticator; the loopback token is never treated as a Human principal.</p>
        {!session ? (
          <form className="human-protocol-form" onSubmit={pairHuman}>
            <p className="field-hint">A new installation first prepares a registration challenge, then a second click starts Windows Hello. An enrolled installation prepares a fresh authorization challenge. Cancelling a prompt creates no Human session.</p>
            <button type="submit" disabled={humanBusy}>{humanBusy
              ? (humanChallenge ? 'Waiting for platform verification…' : 'Preparing challenge…')
              : !humanChallenge
                ? 'Prepare Windows Hello'
                : humanChallenge.ceremony === 'registration'
                  ? 'Continue with Windows Hello'
                  : 'Authorize with Windows Hello'}</button>
          </form>
        ) : (
          <>
            <p className="field-hint">Paired as {pairing?.principal_ref ?? session.principal_ref}; session expires {session.expires_at}.</p>
            <form className="human-protocol-form" onSubmit={issueChallengeForReview}>
              <div className="form-field">
                <label htmlFor="human-action">Decision</label>
                <select id="human-action" value={action} onChange={(event) => setAction(event.target.value as DecisionChallenge['action'])} disabled={humanBusy || challenge !== null}>
                  <option>Accept</option>
                  <option>Reject</option>
                  <option>Revoke</option>
                  <option>Supersede</option>
                </select>
              </div>
              {action === 'Supersede' && (
                <div className="form-field">
                  <label htmlFor="replacement-acceptance">Replacement acceptance ID</label>
                  <input id="replacement-acceptance" value={replacementAcceptanceId} onChange={(event) => setReplacementAcceptanceId(event.target.value)} disabled={humanBusy || challenge !== null} />
                </div>
              )}
              {action !== 'Accept' && (
                <div className="form-field">
                  <label htmlFor="human-reason">Reason</label>
                  <textarea id="human-reason" value={reason} onChange={(event) => setReason(event.target.value)} rows={3} disabled={humanBusy || challenge !== null} />
                </div>
              )}
              <div className="form-actions">
                {!challenge ? (
                  <button type="submit" disabled={humanBusy}>{humanBusy ? 'Issuing challenge…' : `Issue exact-view challenge for ${action}`}</button>
                ) : (
                  <>
                    <button type="button" onClick={confirmDecision} disabled={humanBusy || !challengeView}>{humanBusy ? 'Submitting…' : `Confirm ${challenge.action}`}</button>
                    <button type="button" onClick={() => { setChallenge(null); setChallengeView(null); setHumanNotice('Challenge cancelled.') }} disabled={humanBusy}>Cancel challenge</button>
                  </>
                )}
                <button type="button" onClick={endSession} disabled={humanBusy}>End session</button>
              </div>
              {challenge && challengeView && (
                <div className="review-warning" role="status">
                  <strong>Review the exact challenged view before the second gesture</strong>
                  <p>Action: {challenge.action}; view digest: {challenge.view_digest}; expires: {challenge.expires_at}.</p>
                  <pre>{JSON.stringify(challengeView, null, 2)}</pre>
                </div>
              )}
            </form>
          </>
        )}
        {humanNotice && <p className="human-notice" role="status">{humanNotice}</p>}
        {humanError && <p className="human-error" role="alert">{humanError}</p>}
      </div>
      <details className="detail-disclosure" open>
        <summary>Changed source</summary>
        {view.diff.length === 0 ? <p>No source changes.</p> : view.diff.map((change) => (
          <article className="diff-entry" key={String(change.path)}>
            <h3>{String(change.op).toUpperCase()}: {String(change.path)}</h3>
            <pre>{JSON.stringify({ before: change.before, after: change.after }, null, 2)}</pre>
          </article>
        ))}
      </details>
      <details className="detail-disclosure" open>
        <summary>Requirements and validation contract</summary>
        <pre>{JSON.stringify({ requirements: view.requirements, validation_contract: view.validation_contract, checks: view.checks }, null, 2)}</pre>
      </details>
      <details className="detail-disclosure">
        <summary>Evidence, publication, and decision history</summary>
        <pre>{JSON.stringify({ evidence: view.evidence, publication: view.publication, verification, assurance, decision_history: view.decision_history }, null, 2)}</pre>
      </details>
    </section>
  )
}
