import { useState } from 'react'
import type { ApiClientConfig } from '../api'
import { createProject, AuthError, ApiError } from '../api'

interface CreateProjectFormProps {
  config: ApiClientConfig
  onCreated: () => void
  onCancel: () => void
}

export function CreateProjectForm({ config, onCreated, onCancel }: CreateProjectFormProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await createProject(config, {
        name: name.trim(),
        description: description.trim() || null,
      })
      onCreated()
    } catch (err) {
      if (err instanceof AuthError) {
        setError('Authentication required')
      } else if (err instanceof ApiError && err.status === 422) {
        setError('Invalid project data. Check the required fields.')
      } else {
        setError('Unable to create project. Try again.')
      }
      setSubmitting(false)
    }
  }

  return (
    <form className="create-form" onSubmit={handleSubmit} aria-label="Create project">
      {error && <div className="form-error" role="alert">{error}</div>}
      <div className="form-field">
        <label htmlFor="project-name">Project name</label>
        <input
          id="project-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={submitting}
          required
          aria-required="true"
        />
      </div>
      <div className="form-field">
        <label htmlFor="project-desc">Description (optional)</label>
        <input
          id="project-desc"
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={submitting}
        />
      </div>
      <div className="form-actions">
        <button type="submit" disabled={submitting || !name.trim()}>
          {submitting ? 'Creating...' : 'Create project'}
        </button>
        <button type="button" onClick={onCancel} disabled={submitting}>
          Cancel
        </button>
      </div>
    </form>
  )
}
