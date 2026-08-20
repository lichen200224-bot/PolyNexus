import { useState, useMemo } from 'react'
import type { ApiClientConfig, Project, Task } from './api'
import { ProjectList } from './components/ProjectList'
import { TaskList } from './components/TaskList'
import { RunPreparation } from './components/RunPreparation'
import { RunDetail } from './components/RunDetail'

const workModes = [
  ['Discuss', 'Independent analysis, cross review, synthesis'],
  ['Review', 'Review code, documents, designs, or other artifacts'],
  ['Validate', 'Run deterministic checks and collect evidence'],
] as const

type ViewState =
  | { view: 'projects' }
  | { view: 'tasks'; project: Project }
  | { view: 'run-prep'; project: Project; task: Task }
  | { view: 'run-detail'; project: Project; task: Task; runId: string }

function createDefaultConfig(): ApiClientConfig {
  const base = import.meta.env.VITE_POLYNEXUS_API_BASE_URL || '/api/v1'
  return {
    baseUrl: base.replace(/\/+$/, ''),
    getAuthHeaders: () => ({}),
  }
}

export function App() {
  const [state, setState] = useState<ViewState>({ view: 'projects' })
  const config = useMemo(createDefaultConfig, [])

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">PolyNexus · Development Baseline v1.0</p>
        <h1>Multi-AI Collaboration & Validation Workspace</h1>
        <p className="subtitle">
          Select a project, then start with the purpose of the work—not the provider.
        </p>
      </header>

      {state.view === 'projects' && (
        <>
          <section className="panel" aria-labelledby="project-heading">
            <div>
              <p className="label">Current Project</p>
              <h2 id="project-heading">Select a project</h2>
            </div>
          </section>
          <ProjectList
            config={config}
            onSelectProject={(p) => setState({ view: 'tasks', project: p })}
          />
        </>
      )}

      {state.view === 'tasks' && (
        <>
          <section className="panel" aria-labelledby="project-heading">
            <div>
              <p className="label">Current Project</p>
              <h2 id="project-heading">{state.project.name}</h2>
            </div>
          </section>
          <TaskList
            config={config}
            projectId={state.project.id}
            onSelectTask={(t) => setState({ view: 'run-prep', project: state.project, task: t })}
            onBack={() => setState({ view: 'projects' })}
          />
        </>
      )}

      {state.view === 'run-prep' && (
        <>
          <section className="panel" aria-labelledby="project-heading">
            <div>
              <p className="label">Current Project</p>
              <h2 id="project-heading">{state.project.name}</h2>
            </div>
          </section>
          <RunPreparation
            config={config}
            task={state.task}
            onBack={() => setState({ view: 'tasks', project: state.project })}
            onOpenDetail={(runId) => setState({ view: 'run-detail', project: state.project, task: state.task, runId })}
          />
        </>
      )}

      {state.view === 'run-detail' && (
        <>
          <section className="panel" aria-labelledby="project-heading">
            <div>
              <p className="label">Current Project</p>
              <h2 id="project-heading">{state.project.name}</h2>
            </div>
          </section>
          <RunDetail
            config={config}
            runId={state.runId}
            onBack={() => setState({ view: 'run-prep', project: state.project, task: state.task })}
          />
        </>
      )}

      <section className="modes-section">
        <h2>What do you want to do?</h2>
        <div className="mode-grid">
          {workModes.map(([name, description]) => (
            <article className="mode-card" key={name}>
              <h3>{name}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
