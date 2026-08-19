import { useState, useEffect } from 'react'
import type { ApiClientConfig, Task } from '../api'
import { listTasks, AuthError } from '../api'
import { CreateTaskForm } from './CreateTaskForm'

interface TaskListProps {
  config: ApiClientConfig
  projectId: string
  onSelectTask: (task: Task) => void
  onBack: () => void
}

const MODE_LABELS: Record<string, string> = {
  DISCUSS: 'Discuss',
  REVIEW: 'Review',
  VALIDATE: 'Validate',
}

export function TaskList({ config, projectId, onSelectTask, onBack }: TaskListProps) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  const load = () => {
    setLoading(true)
    setError(null)
    listTasks(config, projectId)
      .then((res) => setTasks(res.tasks))
      .catch((err) => {
        if (err instanceof AuthError) {
          setError('Authentication required')
        } else {
          setError(err.message || 'Failed to load tasks')
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [config, projectId])

  if (loading) {
    return <div className="status-message" role="status">Loading tasks...</div>
  }

  if (error) {
    return (
      <div className="status-message status-error" role="alert">
        {error}
        <button type="button" onClick={onBack} className="back-link">Back to projects</button>
      </div>
    )
  }

  return (
    <section aria-labelledby="task-list-heading">
      <div className="section-header">
        <h2 id="task-list-heading">Tasks</h2>
        <div className="section-actions">
          <button type="button" onClick={() => setShowCreate(!showCreate)}>
            {showCreate ? 'Cancel' : 'New task'}
          </button>
          <button type="button" onClick={onBack} className="back-link">Back</button>
        </div>
      </div>
      {showCreate && (
        <CreateTaskForm
          config={config}
          projectId={projectId}
          onCreated={() => { setShowCreate(false); load() }}
          onCancel={() => setShowCreate(false)}
        />
      )}
      {tasks.length === 0 ? (
        <div className="status-message">No tasks in this project yet.</div>
      ) : (
        <ul className="task-list" role="list">
          {tasks.map((t) => (
            <li key={t.id} className="task-item">
              <button
                type="button"
                className="task-item-btn"
                onClick={() => onSelectTask(t)}
              >
                <span className="task-title">{t.title}</span>
                <span className="task-mode">{MODE_LABELS[t.mode] || t.mode}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
