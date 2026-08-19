import { useState, useEffect } from 'react'
import type { ApiClientConfig, Task, Run } from '../api'
import { listRuns, createRun, AuthError, ApiError } from '../api'

interface RunPreparationProps {
  config: ApiClientConfig
  task: Task
  onBack: () => void
}

export function RunPreparation({ config, task, onBack }: RunPreparationProps) {
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  const [contextPackageId, setContextPackageId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadRuns = () => {
    setLoading(true)
    listRuns(config, task.id)
      .then((res) => setRuns(res.runs))
      .catch((err) => {
        if (err instanceof AuthError) {
          setError('Authentication required')
        } else {
          setError(err.message || 'Failed to load runs')
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadRuns() }, [config, task.id])

  const handleCreateRun = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await createRun(config, task.id, {
        context_package_id: contextPackageId.trim(),
      })
      setContextPackageId('')
      loadRuns()
    } catch (err) {
      if (err instanceof AuthError) {
        setError('Authentication required')
      } else if (err instanceof ApiError && err.status === 422) {
        setError(err.body ? String(err.body) : 'Invalid ContextPackage')
      } else if (err instanceof ApiError && err.status === 404) {
        setError('Task not found')
      } else {
        setError(err instanceof Error ? err.message : 'Failed to create run')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const canCreateRun = contextPackageId.trim().length > 0 && !submitting

  return (
    <section aria-labelledby="run-prep-heading">
      <div className="section-header">
        <h2 id="run-prep-heading">Review Preparation</h2>
        <button type="button" onClick={onBack} className="back-link">Back to tasks</button>
      </div>

      <div className="task-info">
        <p><strong>Task:</strong> {task.title}</p>
        <p><strong>Mode:</strong> {task.mode}</p>
        <p><strong>Workflow:</strong> {task.workflow_id} v{task.workflow_version}</p>
      </div>

      <form className="create-form" onSubmit={handleCreateRun} aria-label="Create run">
        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="form-field">
          <label htmlFor="cp-id">ContextPackage ID</label>
          <input
            id="cp-id"
            type="text"
            value={contextPackageId}
            onChange={(e) => setContextPackageId(e.target.value)}
            disabled={submitting}
            placeholder="context_xxxxx"
            aria-describedby="cp-id-hint"
          />
          <span id="cp-id-hint" className="field-hint">
            Paste an existing ContextPackage ID. The server validates it belongs to this project.
          </span>
        </div>
        <div className="form-actions">
          <button type="submit" disabled={!canCreateRun}>
            {submitting ? 'Creating run...' : 'Create Run'}
          </button>
        </div>
      </form>

      <div className="runs-section">
        <h3>Runs</h3>
        {loading ? (
          <div className="status-message" role="status">Loading runs...</div>
        ) : runs.length === 0 ? (
          <div className="status-message">No runs yet.</div>
        ) : (
          <ul className="run-list" role="list">
            {runs.map((r) => (
              <li key={r.id} className="run-item">
                <div className="run-header">
                  <span className="run-id">{r.id}</span>
                  <span className="run-state">{r.state}</span>
                </div>
                <div className="run-details">
                  <span>Target: {r.execution_target}</span>
                  <span>Resume: {r.resume_mode}</span>
                </div>
                {r.result && (
                  <div className="run-result">
                    <span>Result: {r.result.status}</span>
                    <span>{r.result.summary}</span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
