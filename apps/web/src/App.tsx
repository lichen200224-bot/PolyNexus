const workModes = [
  ['Discuss', 'Independent analysis, cross review, synthesis'],
  ['Review', 'Review code, documents, designs, or other artifacts'],
  ['Validate', 'Run deterministic checks and collect evidence'],
] as const

export function App() {
  return (
    <main className="shell">
      <header>
        <p className="eyebrow">PolyNexus · Development Baseline v1.0</p>
        <h1>Multi-AI Collaboration & Validation Workspace</h1>
        <p className="subtitle">
          Select a project, then start with the purpose of the work—not the provider.
        </p>
      </header>

      <section className="panel" aria-labelledby="project-heading">
        <div>
          <p className="label">Current Project</p>
          <h2 id="project-heading">First Vertical Slice</h2>
        </div>
        <button type="button" disabled title="Project persistence is the next implementation task">
          Open project
        </button>
      </section>

      <section>
        <h2>What do you want to do?</h2>
        <div className="mode-grid">
          {workModes.map(([name, description]) => (
            <article className="mode-card" key={name}>
              <h3>{name}</h3>
              <p>{description}</p>
              <button type="button" disabled>
                Coming in first product slice
              </button>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
