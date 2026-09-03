import { useState } from 'react'
import type { ApiClientConfig } from '../api'
import { createTask, AuthError, ApiError } from '../api'

interface CreateTaskFormProps {
  config: ApiClientConfig
  projectId: string
  onCreated: () => void
  onCancel: () => void
}

const WORKFLOW_OPTIONS = [
  { value: 'review-minimal', label: 'Review (minimal)' },
]

const MODE_OPTIONS = [
  { value: 'DISCUSS', label: 'Discuss' },
  { value: 'REVIEW', label: 'Review' },
  { value: 'VALIDATE', label: 'Validate' },
]

export function CreateTaskForm({ config, projectId, onCreated, onCancel }: CreateTaskFormProps) {
  const [title, setTitle] = useState('')
  const [workflowId, setWorkflowId] = useState('review-minimal')
  const [workflowVersion, setWorkflowVersion] = useState(1)
  const [mode, setMode] = useState('REVIEW')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await createTask(config, projectId, {
        title: title.trim(),
        workflow_id: workflowId,
        workflow_version: workflowVersion,
        mode,
      })
      onCreated()
    } catch (err) {
      if (err instanceof AuthError) {
        setError('Authentication required')
      } else if (err instanceof ApiError && err.status === 422) {
        setError('Invalid task data. Check the required fields.')
      } else if (err instanceof ApiError && err.status === 404) {
        setError('Project not found')
      } else {
        setError('Unable to create task. Try again.')
      }
      setSubmitting(false)
    }
  }

  return (
    <form className="create-form" onSubmit={handleSubmit} aria-label="Create task">
      {error && <div className="form-error" role="alert">{error}</div>}
      <div className="form-field">
        <label htmlFor="task-title">Task title</label>
        <input
          id="task-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          disabled={submitting}
          required
          aria-required="true"
        />
      </div>
      <div className="form-field">
        <label htmlFor="task-workflow">Workflow</label>
        <select
          id="task-workflow"
          value={workflowId}
          onChange={(e) => setWorkflowId(e.target.value)}
          disabled={submitting}
        >
          {WORKFLOW_OPTIONS.map((w) => (
            <option key={w.value} value={w.value}>{w.label}</option>
          ))}
        </select>
      </div>
      <div className="form-field">
        <label htmlFor="task-version">Workflow version</label>
        <input
          id="task-version"
          type="number"
          min={1}
          value={workflowVersion}
          onChange={(e) => setWorkflowVersion(Number(e.target.value))}
          disabled={submitting}
        />
      </div>
      <div className="form-field">
        <label htmlFor="task-mode">Mode</label>
        <select
          id="task-mode"
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          disabled={submitting}
        >
          {MODE_OPTIONS.map((m) => (
            <option key={m.value} value={m.value}>{m.label}</option>
          ))}
        </select>
      </div>
      <div className="form-actions">
        <button type="submit" disabled={submitting || !title.trim()}>
          {submitting ? 'Creating...' : 'Create task'}
        </button>
        <button type="button" onClick={onCancel} disabled={submitting}>
          Cancel
        </button>
      </div>
    </form>
  )
}
