import { workRequest, taskGenerationPath } from '../api'
import type { Generation } from '../api'
import { useEffect, useState, useCallback, useRef } from 'react'
import type { ApiClientConfig, Run, RunResult, Finding, Evidence, Artifact, RunEvent } from '../api'
import { getRun, getRunResult, getRunFindings, getRunEvidence, getRunArtifacts, getRunHistory, AuthError, ApiError, NotFoundError } from '../api'
import { StatusMessage } from './StatusMessage'

interface RunDetailProps {
  config: ApiClientConfig
  runId: string
  onBack: () => void
}

function toUserMessage(err: unknown): string {
  if (err instanceof AuthError) return 'Authentication required. Set LOOPBACK_TOKEN on the Core server.'
  if (err instanceof NotFoundError) return 'Run not found.'
  if (err instanceof ApiError) {
    if (err.status === 422) return 'Validation error: stored ownership or contract is invalid.'
    return 'Unable to load run data.'
  }
  return 'Unable to load run data.'
}

const HUMAN_REQUIRED_STATES = new Set(['HUMAN_REQUIRED', 'WAITING_FOR_HUMAN', 'PENDING_HUMAN'])
const TERMINAL_ERROR_STATES = new Set(['FAILED', 'TIMED_OUT', 'CANCELLED', 'ORPHANED'])

function stateMessage(state: string): { kind: 'human-required' | 'terminal'; title: string; detail: string } | null {
  if (HUMAN_REQUIRED_STATES.has(state)) {
    return {
      kind: 'human-required',
      title: 'Human action required',
      detail: 'Review the required decision or confirmation outside this read-only result view, then reload the run.',
    }
  }
  if (TERMINAL_ERROR_STATES.has(state)) {
    return {
      kind: 'terminal',
      title: `Run ended: ${state}`,
      detail: 'This terminal state is shown as recorded. No success or evidence is inferred; inspect the durable history below.',
    }
  }
  return null
}

export function RunDetail({ config, runId, onBack }: RunDetailProps) {
  const [commandError,setCommandError]=useState(''),[commandBusy,setCommandBusy]=useState(false)
  const commandBodies=useRef(new Map<string,Record<string,unknown>>())
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
  const send=async(kind:'execute'|'cancel')=>{
    if(!run?.generation_revision)return
    setCommandBusy(true);setCommandError('')
    try {
      const current=await workRequest<Generation>(config,'GET',`${taskGenerationPath(run.task_id)}/${run.generation_revision}`)
      if(current.ownership_unknown)throw new Error('unknown ownership')
      const key=kind+run.id
      if(!commandBodies.current.has(key))commandBodies.current.set(key,{generation_revision:run.generation_revision,expected_control_revision:current.control_revision,command_id:crypto.randomUUID(),...(kind==='cancel'?{expected_fence:current.writer?.fence??0}:{})})
      await workRequest(config,'POST',`/runs/${encodeURIComponent(run.id)}/${kind}`,commandBodies.current.get(key))
      await load()
    } catch {setCommandError('Unable to send command. Refresh the recorded state and check runtime readiness.')}
    finally {setCommandBusy(false)}
  }


  return (
    <section aria-labelledby="run-detail-heading">
      <div className="section-header">
        <h2 id="run-detail-heading">Run Detail</h2>
        <button type="button" onClick={onBack} className="back-link" aria-label="Back to run preparation">Back to preparation</button>
      </div>

      {loading && <StatusMessage kind="loading">Loading run detail...</StatusMessage>}

      {error && (
        <StatusMessage kind={error === 'Authentication required. Set LOOPBACK_TOKEN on the Core server.' ? 'permission' : 'error'} title={error} action={<button type="button" onClick={load}>Retry</button>} />
      )}

      {!loading && !error && run && (
        <>
          {(() => {
            const notice = stateMessage(run.state)
            return notice ? <StatusMessage kind={notice.kind} title={notice.title}>{notice.detail}</StatusMessage> : null
          })()}
          <section aria-labelledby="run-meta-heading" className="task-info">
            <div className="section-header">
              <h3 id="run-meta-heading">Run overview</h3>
              <span className="section-count">{run.state}</span>
            </div>
            <p><strong>State:</strong> {run.state}</p>
            <p>Generation: {run.generation_revision??'Legacy unbound / unverified'}</p>
            <button type="button" disabled={commandBusy} onClick={()=>void load()}>Refresh recorded state</button>
            <button type="button" disabled={commandBusy||!run.generation_revision||run.state!=='CREATED'} onClick={()=>void send('execute')}>Start this Run</button>
            <button type="button" disabled={commandBusy||!run.generation_revision||!['CREATED','STARTING','RUNNING'].includes(run.state)} onClick={()=>void send('cancel')}>Cancel this Run</button>
            {commandError&&<p role="alert">{commandError}</p>}

            <details className="detail-disclosure">
              <summary>Show run identity and execution metadata</summary>
              <p><strong>ID:</strong> {run.id}</p>
              <p><strong>Workflow:</strong> {run.workflow_id} v{run.workflow_version}</p>
              <p><strong>Target:</strong> {run.execution_target}</p>
              <p><strong>Resume:</strong> {run.resume_mode}</p>
              <p><strong>Created:</strong> {run.created_at}</p>
            </details>
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
            <div className="section-header">
              <h3 id="findings-heading">Findings</h3>
              <span className="section-count">{findings?.length ?? 0}</span>
            </div>
            <details className="detail-disclosure" open={Boolean(findings?.length)}>
              <summary>{findings?.length ? 'Review findings' : 'Show findings'}</summary>
              {findings === null ? null : findings.length === 0 ? (
                <p className="status-message">No findings.</p>
              ) : (
                <ul>
                  {findings.map(f => (
                    <li key={f.id}>{f.id} — task:{f.task_id} — run:{f.run_id} — {f.title} — {f.description} — {f.severity} — {f.status} — evidence: {f.evidence_refs.length ? f.evidence_refs.join(', ') : '—'} — {f.created_at}</li>
                  ))}
                </ul>
              )}
            </details>
          </section>

          <section aria-labelledby="evidence-heading" className="detail-section">
            <div className="section-header">
              <h3 id="evidence-heading">Evidence</h3>
              <span className="section-count">{evidence?.length ?? 0}</span>
            </div>
            <details className="detail-disclosure">
              <summary>{evidence?.length ? 'Inspect evidence' : 'Show evidence'}</summary>
              {evidence === null ? null : evidence.length === 0 ? (
                <p className="status-message">No evidence.</p>
              ) : (
                <ul>
                  {evidence.map(e => (
                    <li key={e.id}>{e.id} — task:{e.task_id} — run:{e.run_id} — {e.actor_id} — {e.source} — {e.type} — {e.status} — artifacts: {e.artifact_refs.length ? e.artifact_refs.join(', ') : '—'} — meta: {Object.keys(e.metadata).length ? JSON.stringify(e.metadata) : '—'} — {e.observed_at}</li>
                  ))}
                </ul>
              )}
            </details>
          </section>

          <section aria-labelledby="artifacts-heading" className="detail-section">
            <div className="section-header">
              <h3 id="artifacts-heading">Artifacts</h3>
              <span className="section-count">{artifacts?.length ?? 0}</span>
            </div>
            <details className="detail-disclosure">
              <summary>{artifacts?.length ? 'Inspect artifacts' : 'Show artifacts'}</summary>
              {artifacts === null ? null : artifacts.length === 0 ? (
                <p className="status-message">No artifacts.</p>
              ) : (
                <ul>
                  {artifacts.map(a => (
                    <li key={a.id}>{a.id} — project:{a.project_id} — task:{a.task_id ?? '—'} — run:{a.run_id ?? '—'} — {a.artifact_type} — {a.mime_type} — {a.source_type} — {a.storage_ref} — {a.sha256} — {a.size} bytes</li>
                  ))}
                </ul>
              )}
            </details>
          </section>

          <section aria-labelledby="history-heading" className="detail-section">
            <div className="section-header">
              <h3 id="history-heading">History</h3>
              <span className="section-count">{history?.length ?? 0}</span>
            </div>
            <details className="detail-disclosure">
              <summary>{history?.length ? 'Inspect history' : 'Show history'}</summary>
              {history === null ? null : history.length === 0 ? (
                <p className="status-message">No history events.</p>
              ) : (
                <ul>
                  {history.map(ev => (
                    <li key={ev.id}>{ev.id} — run:{ev.run_id} — {ev.from_state} → {ev.to_state} at {ev.occurred_at}{ev.reason ? ` — ${ev.reason}` : ''}</li>
                  ))}
                </ul>
              )}
            </details>
          </section>
        </>
      )}
    </section>
  )
}
