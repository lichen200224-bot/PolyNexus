import { GenerationControls } from './GenerationControls'
import { ContextArtifacts } from './ContextArtifacts'
import type { Generation } from '../api'
import { useState, useEffect, useRef } from 'react'
import type { ApiClientConfig, Task, Run, ContextPackageCreateRequest } from '../api'
import { listRuns, createRun, createContextPackage, AuthError, ApiError } from '../api'
import { StatusMessage } from './StatusMessage'

interface RunPreparationProps {
  archived?: boolean
  config: ApiClientConfig
  task: Task
  onBack: () => void
  onOpenDetail: (runId: string) => void
}

function parseMultiline(raw: string): string[] {
  return raw
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.length > 0)
}

function parseProjectFacts(raw: string): Record<string, string> | string {
  const lines = raw
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.length > 0)
  if (lines.length === 0) return {}
  const facts: Record<string, string> = {}
  for (const line of lines) {
    const idx = line.indexOf('=')
    if (idx < 1) {
      return `Invalid project_facts line: "${line}" (expected key=value format)`
    }
    const key = line.slice(0, idx).trim()
    const value = line.slice(idx + 1).trim()
    facts[key] = value
  }
  return facts
}

export function RunPreparation({ config, task, onBack, onOpenDetail, archived=false }: RunPreparationProps) {
  const [generation,setGeneration]=useState<Generation|null>(null)
  const runCommand=useRef(new Map<string,string>())
  const [cpClassification,setCpClassification]=useState('INTERNAL')
  const [runs, setRuns] = useState<Run[]>([])
  const [loading, setLoading] = useState(true)
  const [contextPackageId, setContextPackageId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [runsError, setRunsError] = useState<string | null>(null)

  // ContextPackage authoring state
  const [showCpForm, setShowCpForm] = useState(false)
  const [cpVersion, setCpVersion] = useState('1')
  const [cpInstructions, setCpInstructions] = useState('')
  const [cpConstraints, setCpConstraints] = useState('')
  const [cpProjectFacts, setCpProjectFacts] = useState('')
  const [cpArtifactRefs, setCpArtifactRefs] = useState('')
  const [cpPriorDecisionRefs, setCpPriorDecisionRefs] = useState('')
  const [cpMemoryRefs, setCpMemoryRefs] = useState('')
  const [cpSourceRefs, setCpSourceRefs] = useState('')
  const [cpSubmitting, setCpSubmitting] = useState(false)
  const [cpError, setCpError] = useState<string | null>(null)
  const [cpSuccess, setCpSuccess] = useState<{ id: string; version: number } | null>(null)
  const [cpValidationError, setCpValidationError] = useState<string | null>(null)

  const loadRuns = () => {
    setLoading(true)
    setRuns([])
    setRunsError(null)
    listRuns(config, task.id)
      .then((res) => setRuns(res.runs))
      .catch((err) => {
        if (err instanceof AuthError) {
          setRunsError('Authentication required')
        } else {
          setRunsError('Unable to load runs. Try again.')
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadRuns() }, [config, task.id])

  const handleCreateRun = async (e: React.FormEvent) => {
    e.preventDefault()
    if(archived)return
    if(!generation||generation.closed||generation.aborted||generation.ownership_unknown||generation.inputs.context_package_id!==contextPackageId.trim()){setError("Choose an open, verified generation before creating a Run.");return}
    setSubmitting(true)
    setError(null)
    try {
      const key=String(generation.revision)+':'+generation.control_revision
      if(!runCommand.current.has(key))runCommand.current.set(key,crypto.randomUUID())
      await createRun(config, task.id, {
        generation_revision:generation.revision,expected_control_revision:generation.control_revision,command_id:runCommand.current.get(key)!,
        context_package_id: contextPackageId.trim(),
      })
      setContextPackageId('')
      loadRuns()
    } catch (err) {
      if (err instanceof AuthError) {
        setError('Authentication required')
      } else if (err instanceof ApiError && err.status === 422) {
        setError('Invalid ContextPackage. Check the reference and try again.')
      } else if (err instanceof ApiError && err.status === 404) {
        setError('Task not found')
      } else {
        setError('Unable to create run. Try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const parseVersion = (raw: string): number | null => {
    const trimmed = raw.trim()
    if (!trimmed) return null
    const num = Number(trimmed)
    if (!Number.isInteger(num) || num < 1) return null
    return num
  }

  const handleCreateCp = async (e: React.FormEvent) => {
    e.preventDefault()
    if(archived)return
    setCpError(null)
    setCpSuccess(null)
    setCpValidationError(null)

    // Validate version strictly
    const versionNum = parseVersion(cpVersion)
    if (versionNum === null) {
      setCpValidationError('Version must be an integer >= 1')
      return
    }

    // Validate project_facts
    const factsResult = parseProjectFacts(cpProjectFacts)
    if (typeof factsResult === 'string') {
      setCpValidationError(factsResult)
      return
    }

    const body: ContextPackageCreateRequest = {
      classification: cpClassification,
      version: versionNum,
      instructions: parseMultiline(cpInstructions),
      constraints: parseMultiline(cpConstraints),
      project_facts: factsResult,
      artifact_refs: parseMultiline(cpArtifactRefs),
      prior_decision_refs: parseMultiline(cpPriorDecisionRefs),
      memory_refs: parseMultiline(cpMemoryRefs),
      source_refs: parseMultiline(cpSourceRefs),
    }

    setCpSubmitting(true)
    try {
      const result = await createContextPackage(config, task.project_id, body)
      setCpSuccess({ id: result.id, version: result.version })
      setContextPackageId(result.id)
    } catch (err) {
      if (err instanceof AuthError) {
        setCpError('Authentication required')
      } else if (err instanceof ApiError && err.status === 404) {
        setCpError('Project not found')
      } else if (err instanceof ApiError && err.status === 422) {
        setCpError('Validation error. Check the ContextPackage fields.')
      } else {
        setCpError('Unable to create ContextPackage. Try again.')
      }
    } finally {
      setCpSubmitting(false)
    }
  }

  const isVersionValid = parseVersion(cpVersion) !== null
  const canCreateRun = !archived && contextPackageId.trim().length > 0 && !submitting && !!generation && !generation.closed && !generation.aborted && !generation.ownership_unknown && generation.inputs.context_package_id===contextPackageId.trim()
  const canCreateCp = !archived && !cpSubmitting && isVersionValid

  return (
    <section aria-labelledby="run-prep-heading">
      <div className="section-header">
        <h2 id="run-prep-heading">Review Preparation</h2>
        <button type="button" onClick={onBack} className="back-link">Back to tasks</button>
      </div>

      {archived&&<p role="status">Archived project: new work is disabled; recorded history and safe cancellation remain available.</p>}
      <div className="task-info">
        <p><strong>Task:</strong> {task.title}</p>
        <p><strong>Mode:</strong> {task.mode}</p>
        <p><strong>Workflow:</strong> {task.workflow_id} v{task.workflow_version}</p>
      </div>

      {/* ContextPackage Authoring Section */}
      <div className="cp-authoring-section">
        <button
          type="button"
          className="back-link"
          onClick={() => setShowCpForm(!showCpForm)}
          aria-expanded={showCpForm}
          disabled={archived}
          aria-controls="cp-authoring-form"
        >
          {showCpForm ? '- Hide ContextPackage authoring' : '+ Create new ContextPackage'}
        </button>

        {showCpForm && !archived && (
          <form
            id="cp-authoring-form"
            className="create-form"
            onSubmit={handleCreateCp}
            aria-label="Create context package"
          >
            {cpError && <div className="form-error" role="alert">{cpError}</div>}
            {cpValidationError && <div className="form-error" role="alert">{cpValidationError}</div>}
            {cpSuccess && (
              <div className="status-message" role="status">
                Created ContextPackage {cpSuccess.id} (version {cpSuccess.version})
              </div>
            )}

            <label>Context classification<select value={cpClassification} onChange={e=>setCpClassification(e.target.value)}>{["PUBLIC","INTERNAL","CONFIDENTIAL","RESTRICTED"].map(c=><option key={c}>{c}</option>)}</select></label>
            <div className="form-field">
              <label htmlFor="cp-version">Version *</label>
              <input
                id="cp-version"
                type="number"
                min={1}
                value={cpVersion}
                onChange={(e) => setCpVersion(e.target.value)}
                disabled={cpSubmitting}
                aria-required="true"
                aria-describedby="cp-version-hint"
              />
              <span id="cp-version-hint" className="field-hint">
                Integer version number (minimum 1)
              </span>
            </div>

            <div className="form-field">
              <label htmlFor="cp-instructions">Instructions</label>
              <textarea
                id="cp-instructions"
                value={cpInstructions}
                onChange={(e) => setCpInstructions(e.target.value)}
                disabled={cpSubmitting}
                rows={3}
                placeholder="One instruction per line"
                aria-describedby="cp-instructions-hint"
              />
              <span id="cp-instructions-hint" className="field-hint">
                One instruction per line. Blank lines are omitted.
              </span>
            </div>

            <div className="form-field">
              <label htmlFor="cp-constraints">Constraints</label>
              <textarea
                id="cp-constraints"
                value={cpConstraints}
                onChange={(e) => setCpConstraints(e.target.value)}
                disabled={cpSubmitting}
                rows={3}
                placeholder="One constraint per line"
                aria-describedby="cp-constraints-hint"
              />
              <span id="cp-constraints-hint" className="field-hint">
                One constraint per line. Blank lines are omitted.
              </span>
            </div>

            <div className="form-field">
              <label htmlFor="cp-project-facts">Project Facts</label>
              <textarea
                id="cp-project-facts"
                value={cpProjectFacts}
                onChange={(e) => setCpProjectFacts(e.target.value)}
                disabled={cpSubmitting}
                rows={3}
                placeholder="key=value per line"
                aria-describedby="cp-project-facts-hint"
              />
              <span id="cp-project-facts-hint" className="field-hint">
                One key=value pair per line. Lines without "=" are rejected.
              </span>
            </div>

            <div className="form-field">
              <label htmlFor="cp-artifact-refs">Artifact References</label>
              <textarea
                id="cp-artifact-refs"
                value={cpArtifactRefs}
                onChange={(e) => setCpArtifactRefs(e.target.value)}
                disabled={cpSubmitting}
                rows={2}
                placeholder="One artifact ref per line"
              />
            </div>

            <div className="form-field">
              <label htmlFor="cp-prior-decision-refs">Prior Decision References</label><p className="field-hint">Imported Core Artifact IDs from this project. Content only; not Human authorization or acceptance.</p>
              <textarea
                id="cp-prior-decision-refs"
                value={cpPriorDecisionRefs}
                onChange={(e) => setCpPriorDecisionRefs(e.target.value)}
                disabled={cpSubmitting}
                rows={2}
                placeholder="One reference per line"
              />
            </div>

            <div className="form-field">
              <label htmlFor="cp-memory-refs">Memory References</label><p className="field-hint">Imported Core Artifact IDs from this project. Content only; not trusted or accepted memory.</p>
              <textarea
                id="cp-memory-refs"
                value={cpMemoryRefs}
                onChange={(e) => setCpMemoryRefs(e.target.value)}
                disabled={cpSubmitting}
                rows={2}
                placeholder="One reference per line"
              />
            </div>

            <div className="form-field">
              <label htmlFor="cp-source-refs">Source References</label>
              <textarea
                id="cp-source-refs"
                value={cpSourceRefs}
                onChange={(e) => setCpSourceRefs(e.target.value)}
                disabled={cpSubmitting}
                rows={2}
                placeholder="One source ref per line"
              />
            </div>

            <div className="form-actions">
              <button type="submit" disabled={!canCreateCp}>
                {cpSubmitting ? 'Creating...' : 'Create ContextPackage'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Run Creation Form */}
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
            Paste an existing ContextPackage ID or create one above. The server validates it belongs to this project.
          </span>
        </div>
        <div className="form-actions">
          <button type="submit" disabled={!canCreateRun}>
            {submitting ? 'Creating run...' : 'Create Run'}
          </button>
        </div>
      </form>

      <GenerationControls archived={archived} config={config} taskId={task.id} contextId={contextPackageId.trim()} onSelected={g=>{setGeneration(g);if(g)setContextPackageId(g.inputs.context_package_id)}}/>
      <ContextArtifacts archived={archived} config={config} projectId={task.project_id} onSelect={id=>{setContextPackageId(id);setGeneration(null)}} onArtifact={id=>{setCpArtifactRefs(old=>[...new Set([...parseMultiline(old),id])].join('\n'));setShowCpForm(true)}}/>

      <div className="runs-section">
        <h3>Runs</h3>
        {loading ? (
          <StatusMessage kind="loading">Loading runs...</StatusMessage>
        ) : runsError ? (
          <StatusMessage
            kind={runsError === 'Authentication required' ? 'permission' : 'error'}
            title={runsError}
            action={<button type="button" onClick={loadRuns}>Retry</button>}
          >
            {runsError === 'Authentication required' && (
              <p className="status-hint">Set the LOOPBACK_TOKEN environment variable on the Core server to enable API access.</p>
            )}
          </StatusMessage>
        ) : runs.length === 0 ? (
          <StatusMessage kind="empty">No runs yet.</StatusMessage>
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
                <button type="button" onClick={() => onOpenDetail(r.id)} aria-label={`View result and history for run ${r.id}`}>View result / history</button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
