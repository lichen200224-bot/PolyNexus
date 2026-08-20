import { useEffect, useState, useCallback } from 'react'
import type { ApiClientConfig, Run, RunResult, Finding, Evidence, Artifact, RunEvent } from '../api'
import { getRun, getRunResult, getRunFindings, getRunEvidence, getRunArtifacts, getRunHistory, AuthError, ApiError, NotFoundError } from '../api'

interface RunDetailProps {
  config: ApiClientConfig
  runId: string
  onBack: () => void
}

function toUserMessage(err: unknown): string {
  if (err instanceof AuthError) return 'Authentication required. Set LOOPBACK_TOKEN on the Core server.'
  if (err instanceof NotFoundError) return 'Run not found.'
  if (err instanceof ApiError) {
    if (err.status === 422) return typeof err.body === 'string' && err.body ? `Validation error: ${err.body}` : 'Validation error: stored ownership or contract is invalid.'
    return err.message || 'Failed to load data'
  }
  return err instanceof Error ? err.message : 'Failed to load data'
}

export function RunDetail({ config, runId, onBack }: RunDetailProps) {
  const [run, setRun] = useState<Run | null>(null)
  const [result, setResult] = useState<RunResult | null | undefined>(undefined)
  const [findings, setFindings] = useState<Finding[] | null>(null)
  const [evidence, setEvidence] = useState<Evidence[] | null>(null)
  const [artifacts, setArtifacts] = useState<Artifact[] | null>(null)
  const [history, setHistory] = useState<RunEvent[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    // Clear stale data on retry so we do not show fabricated/stale records
    setRun(null); setResult(undefined); setFindings(null); setEvidence(null); setArtifacts(null); setHistory(null)
    try {
      const [runRes, resultRes, findingsRes, evidenceRes, artifactsRes, historyRes] = await Promise.all([
        getRun(config, runId),
        getRunResult(config, runId),
        getRunFindings(config, runId),
        getRunEvidence(config, runId),
        getRunArtifacts(config, runId),
        getRunHistory(config, runId),
      ])
      setRun(runRes)
      setResult(resultRes.result)
      setFindings(findingsRes.findings)
      setEvidence(evidenceRes.evidence)
      setArtifacts(artifactsRes.artifacts)
      setHistory(historyRes.events)
    } catch (err) {
      setError(toUserMessage(err))
    } finally {
      setLoading(false)
    }
  }, [config, runId])

  useEffect(() => { load() }, [load])

  return (
    <section aria-labelledby="run-detail-heading">
      <div className="section-header">
        <h2 id="run-detail-heading">Run Detail</h2>
        <button type="button" onClick={onBack} className="back-link" aria-label="Back to run preparation">Back to preparation</button>
      </div>

      {loading && <div role="status" className="status-message">Loading run detail...</div>}

      {error && (
        <div role="alert" className="form-error">
          <p>{error}</p>
          <button type="button" onClick={load}>Retry</button>
        </div>
      )}

      {!loading && !error && run && (
        <>
          <section aria-labelledby="run-meta-heading" className="task-info">
            <h3 id="run-meta-heading">Run</h3>
            <p><strong>ID:</strong> {run.id}</p>
            <p><strong>State:</strong> {run.state}</p>
            <p><strong>Workflow:</strong> {run.workflow_id} v{run.workflow_version}</p>
            <p><strong>Target:</strong> {run.execution_target}</p>
            <p><strong>Resume:</strong> {run.resume_mode}</p>
            <p><strong>Created:</strong> {run.created_at}</p>
          </section>

          <section aria-labelledby="result-heading" className="detail-section">
            <h3 id="result-heading">Result</h3>
            {result === null || result === undefined ? (
              result === null ? <p className="status-message">No result yet.</p> : null
            ) : (
              <div className="result-card">
                <p><strong>Status:</strong> {result.status}</p>
                <p><strong>Summary:</strong> {result.summary}</p>
                <p><strong>Findings:</strong> {result.finding_ids.length ? result.finding_ids.join(', ') : '—'}</p>
                <p><strong>Evidence:</strong> {result.evidence_ids.length ? result.evidence_ids.join(', ') : '—'}</p>
                <p><strong>Artifacts:</strong> {result.artifact_ids.length ? result.artifact_ids.join(', ') : '—'}</p>
              </div>
            )}
            {result === undefined && <p className="status-message">No result yet.</p>}
          </section>

          <section aria-labelledby="findings-heading" className="detail-section">
            <h3 id="findings-heading">Findings</h3>
            {findings === null ? null : findings.length === 0 ? (
              <p className="status-message">No findings.</p>
            ) : (
              <ul>
                {findings.map(f => (
                  <li key={f.id}>{f.id} — task:{f.task_id} — run:{f.run_id} — {f.title} — {f.description} — {f.severity} — {f.status} — evidence: {f.evidence_refs.length ? f.evidence_refs.join(', ') : '—'} — {f.created_at}</li>
                ))}
              </ul>
            )}
          </section>

          <section aria-labelledby="evidence-heading" className="detail-section">
            <h3 id="evidence-heading">Evidence</h3>
            {evidence === null ? null : evidence.length === 0 ? (
              <p className="status-message">No evidence.</p>
            ) : (
              <ul>
                {evidence.map(e => (
                  <li key={e.id}>{e.id} — task:{e.task_id} — run:{e.run_id} — {e.actor_id} — {e.source} — {e.type} — {e.status} — artifacts: {e.artifact_refs.length ? e.artifact_refs.join(', ') : '—'} — meta: {Object.keys(e.metadata).length ? JSON.stringify(e.metadata) : '—'} — {e.observed_at}</li>
                ))}
              </ul>
            )}
          </section>

          <section aria-labelledby="artifacts-heading" className="detail-section">
            <h3 id="artifacts-heading">Artifacts</h3>
            {artifacts === null ? null : artifacts.length === 0 ? (
              <p className="status-message">No artifacts.</p>
            ) : (
              <ul>
                {artifacts.map(a => (
                  <li key={a.id}>{a.id} — project:{a.project_id} — task:{a.task_id ?? '—'} — run:{a.run_id ?? '—'} — {a.artifact_type} — {a.mime_type} — {a.source_type} — {a.storage_ref} — {a.sha256} — {a.size} bytes</li>
                ))}
              </ul>
            )}
          </section>

          <section aria-labelledby="history-heading" className="detail-section">
            <h3 id="history-heading">History</h3>
            {history === null ? null : history.length === 0 ? (
              <p className="status-message">No history events.</p>
            ) : (
              <ul>
                {history.map(ev => (
                  <li key={ev.id}>{ev.id} — run:{ev.run_id} — {ev.from_state} → {ev.to_state} at {ev.occurred_at}{ev.reason ? ` — ${ev.reason}` : ''}</li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </section>
  )
}
