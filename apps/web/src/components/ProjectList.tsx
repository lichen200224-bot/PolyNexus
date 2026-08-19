import { useState, useEffect } from 'react'
import type { ApiClientConfig, Project } from '../api'
import { listProjects, AuthError } from '../api'
import { CreateProjectForm } from './CreateProjectForm'

interface ProjectListProps {
  config: ApiClientConfig
  onSelectProject: (project: Project) => void
}

export function ProjectList({ config, onSelectProject }: ProjectListProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  const load = () => {
    setLoading(true)
    setError(null)
    listProjects(config)
      .then((res) => setProjects(res.projects))
      .catch((err) => {
        if (err instanceof AuthError) {
          setError('Authentication required')
        } else {
          setError(err.message || 'Failed to load projects')
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [config])

  if (loading) {
    return <div className="status-message" role="status">Loading projects...</div>
  }

  if (error) {
    return (
      <div className="status-message status-error" role="alert">
        {error}
        {error === 'Authentication required' && (
          <p className="status-hint">
            Set the LOOPBACK_TOKEN environment variable on the Core server to enable API access.
          </p>
        )}
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="status-message">
        <p>No projects yet.</p>
        <button type="button" onClick={() => setShowCreate(true)}>
          Create first project
        </button>
        {showCreate && (
          <CreateProjectForm
            config={config}
            onCreated={() => { setShowCreate(false); load() }}
            onCancel={() => setShowCreate(false)}
          />
        )}
      </div>
    )
  }

  return (
    <section aria-labelledby="project-list-heading">
      <div className="section-header">
        <h2 id="project-list-heading">Projects</h2>
        <button type="button" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? 'Cancel' : 'New project'}
        </button>
      </div>
      {showCreate && (
        <CreateProjectForm
          config={config}
          onCreated={() => { setShowCreate(false); load() }}
          onCancel={() => setShowCreate(false)}
        />
      )}
      <ul className="project-list" role="list">
        {projects.map((p) => (
          <li key={p.id} className="project-item">
            <button
              type="button"
              className="project-item-btn"
              onClick={() => onSelectProject(p)}
            >
              <span className="project-name">{p.name}</span>
              {p.description && (
                <span className="project-desc">{p.description}</span>
              )}
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
