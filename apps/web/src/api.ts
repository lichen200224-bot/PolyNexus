/**
 * PolyNexus Frontend API Client Boundary.
 *
 * Convention:
 * - baseUrl MUST include the version prefix, e.g. "http://localhost:5173/api/v1".
 * - No trailing slash on baseUrl.
 * - No hard-coded token, port, or production secret anywhere in this file.
 * - getAuthHeaders() is injected; when no auth source exists it returns {},
 *   which will produce a 403 from the backend (fail closed).
 */

// ---------------------------------------------------------------------------
// Types — mirrors backend Pydantic schemas (services/core API schemas)
// ---------------------------------------------------------------------------

export interface Project {
  archived?: boolean
  classification?: string
  id: string
  name: string
  description: string | null
  created_at: string
}

export interface Task {
  classification?: string
  id: string
  project_id: string
  title: string
  workflow_id: string
  workflow_version: number
  mode: string
  context_package_id: string | null
  created_at: string
}

export interface RunEvent {
  id: string
  run_id: string
  from_state: string
  to_state: string
  occurred_at: string
  reason: string | null
}

export interface RunResult {
  run_id: string
  status: string
  summary: string
  finding_ids: string[]
  evidence_ids: string[]
  artifact_ids: string[]
}

export interface Run {
  generation_revision?: number | null
  generation_binding_status?: string
  id: string
  task_id: string
  workflow_id: string
  workflow_version: number
  context_package_id: string
  execution_target: string
  resume_mode: string
  state: string
  runtime_ref: string | null
  created_at: string
  updated_at: string
  events: RunEvent[]
  result: RunResult | null
}

// Response wrappers — must match backend `{ projects }`, `{ tasks }`, `{ runs }`
export interface ProjectListResponse {
  projects: Project[]
}

export interface TaskListResponse {
  tasks: Task[]
}

export interface RunListResponse {
  runs: Run[]
}

export interface ProjectCreateRequest {
  classification?: string
  name: string
  description?: string | null
}

export interface TaskCreateRequest {
  classification?: string
  title: string
  workflow_id: string
  workflow_version: number
  mode?: string | null
  context_package_id?: string | null
}

export interface RunCreateRequest {
  generation_revision: number
  expected_control_revision: number
  command_id: string
  context_package_id: string
}

// ---------------------------------------------------------------------------
// ContextPackage
// ---------------------------------------------------------------------------

export interface ContextPackage {
  classification?: string
  id: string
  project_id: string
  version: number
  instructions: string[]
  constraints: string[]
  project_facts: Record<string, string>
  artifact_refs: string[]
  prior_decision_refs: string[]
  memory_refs: string[]
  source_refs: string[]
  created_at: string
}

export interface ContextPackageCreateRequest {
  classification?: string
  version: number
  instructions?: string[]
  constraints?: string[]
  project_facts?: Record<string, string>
  artifact_refs?: string[]
  prior_decision_refs?: string[]
  memory_refs?: string[]
  source_refs?: string[]
}

// ---------------------------------------------------------------------------
// WP-09C read-only query types
// ---------------------------------------------------------------------------

export interface Finding {
  id: string
  task_id: string
  run_id: string
  title: string
  description: string
  severity: string
  evidence_refs: string[]
  status: string
  created_at: string
}

export interface Evidence {
  id: string
  task_id: string
  run_id: string
  actor_id: string
  source: string
  type: string
  status: string
  artifact_refs: string[]
  metadata: Record<string, string>
  observed_at: string
}

export interface Artifact {
  classification?: string
  id: string
  project_id: string
  task_id: string | null
  run_id: string | null
  artifact_type: string
  mime_type: string
  source_type: string
  storage_ref: string
  sha256: string
  size: number
}

export interface RunResultWrapper {
  result: RunResult | null
}

export interface FindingsWrapper {
  findings: Finding[]
}

export interface EvidenceWrapper {
  evidence: Evidence[]
}

export interface ArtifactsWrapper {
  artifacts: Artifact[]
}

export interface HistoryWrapper {
  events: RunEvent[]
}

export interface HealthLayer {
  status: 'ready' | 'not_ready' | 'unknown'
  reason?: string
}

export interface HealthResponse {
  status: string
  service: string
  version: string
  baseline: string
  readiness: 'partial' | 'not_ready'
  layers: {
    process: HealthLayer
    schema: HealthLayer
    database_integrity: HealthLayer
    core: HealthLayer
    api_auth: HealthLayer
    web_client: HealthLayer
    runtime: HealthLayer
  }
}

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly body?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class AuthError extends ApiError {
  constructor(body?: unknown) {
    super('Authentication required', 403, body)
    this.name = 'AuthError'
  }
}

export class NotFoundError extends ApiError {
  constructor(resource: string, id: string) {
    super(`${resource} ${id} not found`, 404)
    this.name = 'NotFoundError'
  }
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

export type AuthHeaderProvider = () => Record<string, string> | Promise<Record<string, string>>

export interface ApiClientConfig {
  /** Base URL MUST include /api/v1, e.g. "/api/v1" (default, uses Vite proxy) or "http://127.0.0.1:8765/api/v1" (direct) */
  baseUrl: string
  /** Inject auth headers; return {} when no auth source is available. */
  getAuthHeaders: AuthHeaderProvider
  /** True only when START supplied the process-scoped browser credential. */
  authConfigured?: boolean
}

async function request<T>(
  config: ApiClientConfig,
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const url = `${config.baseUrl}${path}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...await config.getAuthHeaders(),
  }

  const init: RequestInit = { method, headers }
  if (body !== undefined) {
    init.body = JSON.stringify(body)
  }

  const res = await fetch(url, init)

  if (res.status === 403) {
    const text = await res.text().catch(() => '')
    throw new AuthError(text || undefined)
  }

  if (res.status === 404) {
    throw new NotFoundError(path, '')
  }

  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new ApiError(`API error ${res.status}`, res.status, text)
  }

  return res.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// Startup health
// ---------------------------------------------------------------------------

export function getHealth(config: ApiClientConfig): Promise<HealthResponse> {
  return request<HealthResponse>(config, 'GET', '/health')
}

// ---------------------------------------------------------------------------
// Project endpoints
// ---------------------------------------------------------------------------

export function listProjects(config: ApiClientConfig): Promise<ProjectListResponse> {
  return request<ProjectListResponse>(config, 'GET', '/projects')
}

export function createProject(
  config: ApiClientConfig,
  body: ProjectCreateRequest,
): Promise<Project> {
  return request<Project>(config, 'POST', '/projects', body)
}

export function getProject(config: ApiClientConfig, projectId: string): Promise<Project> {
  return request<Project>(config, 'GET', `/projects/${encodeURIComponent(projectId)}`)
}

// ---------------------------------------------------------------------------
// Task endpoints
// ---------------------------------------------------------------------------

export function listTasks(
  config: ApiClientConfig,
  projectId: string,
): Promise<TaskListResponse> {
  return request<TaskListResponse>(
    config,
    'GET',
    `/projects/${encodeURIComponent(projectId)}/tasks`,
  )
}

export function createTask(
  config: ApiClientConfig,
  projectId: string,
  body: TaskCreateRequest,
): Promise<Task> {
  return request<Task>(
    config,
    'POST',
    `/projects/${encodeURIComponent(projectId)}/tasks`,
    body,
  )
}

export function getTask(config: ApiClientConfig, taskId: string): Promise<Task> {
  return request<Task>(config, 'GET', `/tasks/${encodeURIComponent(taskId)}`)
}

// ---------------------------------------------------------------------------
// Run endpoints
// ---------------------------------------------------------------------------

export function listRuns(
  config: ApiClientConfig,
  taskId: string,
): Promise<RunListResponse> {
  return request<RunListResponse>(
    config,
    'GET',
    `/tasks/${encodeURIComponent(taskId)}/runs`,
  )
}

export function createRun(
  config: ApiClientConfig,
  taskId: string,
  body: RunCreateRequest,
): Promise<Run> {
  return request<Run>(
    config,
    'POST',
    `/tasks/${encodeURIComponent(taskId)}/runs`,
    body,
  )
}

export function getRun(config: ApiClientConfig, runId: string): Promise<Run> {
  return request<Run>(config, 'GET', `/runs/${encodeURIComponent(runId)}`)
}

// ---------------------------------------------------------------------------
// ContextPackage endpoints
// ---------------------------------------------------------------------------

export function createContextPackage(
  config: ApiClientConfig,
  projectId: string,
  body: ContextPackageCreateRequest,
): Promise<ContextPackage> {
  return request<ContextPackage>(
    config,
    'POST',
    `/projects/${encodeURIComponent(projectId)}/context-packages`,
    body,
  )
}

// ---------------------------------------------------------------------------
// WP-09C read-only query endpoints
// ---------------------------------------------------------------------------

export function getRunResult(
  config: ApiClientConfig,
  runId: string,
): Promise<RunResultWrapper> {
  return request<RunResultWrapper>(
    config,
    'GET',
    `/runs/${encodeURIComponent(runId)}/result`,
  )
}

export function getRunFindings(
  config: ApiClientConfig,
  runId: string,
): Promise<FindingsWrapper> {
  return request<FindingsWrapper>(
    config,
    'GET',
    `/runs/${encodeURIComponent(runId)}/findings`,
  )
}

export function getRunEvidence(
  config: ApiClientConfig,
  runId: string,
): Promise<EvidenceWrapper> {
  return request<EvidenceWrapper>(
    config,
    'GET',
    `/runs/${encodeURIComponent(runId)}/evidence`,
  )
}

export function getRunArtifacts(
  config: ApiClientConfig,
  runId: string,
): Promise<ArtifactsWrapper> {
  return request<ArtifactsWrapper>(
    config,
    'GET',
    `/runs/${encodeURIComponent(runId)}/artifacts`,
  )
}

export function getRunHistory(
  config: ApiClientConfig,
  runId: string,
): Promise<HistoryWrapper> {
  return request<HistoryWrapper>(
    config,
    'GET',
    `/runs/${encodeURIComponent(runId)}/history`,
  )
}


export interface Generation {
  task_id: string
  generation_revision?: number
  revision: number
  control_revision: number
  aborted: number | boolean
  closed: number | boolean
  ownership_unknown: number | boolean
  work_aborted: boolean
  inputs: Record<string, string>
  writer: { run_id: string; fence: number; released: number | boolean } | null
  workspace: { workspace_id: string; identity: unknown; git_observation: { state: string }; ownership: { state: string }; recoverability: { state: string; cleanup: string } } | null
  events: Array<{event_id: string; kind: string; control_revision: number}>
}
export function workRequest<T>(config: ApiClientConfig, method: string, path: string, body?: unknown): Promise<T> {
  return request<T>(config, method, path, body)
}
export const taskGenerationPath = (task: string) => `/tasks/${encodeURIComponent(task)}/generations`

// ---------------------------------------------------------------------------
// D1b exact Candidate view / Human boundary
// ---------------------------------------------------------------------------

export interface CandidateView {
  format: 'pn.candidate.view.v1'
  candidate_id: string
  candidate: Record<string, unknown>
  changeset: Record<string, unknown>
  baseline: Record<string, unknown>
  result: Record<string, unknown>
  diff: Array<Record<string, unknown>>
  checks: Array<Record<string, unknown>>
  evidence: Record<string, unknown> | null
  evidence_set_id: string | null
  missing_reasons: string[]
  eligibility_revision: number
  review_round: number
  decision_revision: number
  requirements: Record<string, unknown>
  validation_contract: Array<Record<string, unknown>>
  publication: Record<string, unknown> | null
  requirements_snapshot_id: string
  validation_contract_snapshot_id: string
  verification: Record<string, unknown> | null
  verification_id: string | null
  assurance: Record<string, unknown> | null
  disposition: { state: string; acceptance_id: string | null }
  decision_history: Array<Record<string, unknown>>
  policy_revision: number
  view_digest: string
}

export interface DecisionChallenge {
  challenge_id: string
  candidate_id: string
  action: 'Accept' | 'Reject' | 'Revoke' | 'Supersede'
  replacement_acceptance_id: string | null
  view_digest: string
  nonce: string
  expires_at: string
}

export type HumanEnrollmentCeremony = 'registration' | 'authentication' | 'revocation'

export interface WebAuthnCredentialResponse {
  clientDataJSON: string
  attestationObject?: string | null
  authenticatorData?: string | null
  signature?: string | null
  userHandle?: string | null
}

export interface WebAuthnCredential {
  id: string
  rawId: string
  type: 'public-key'
  response: WebAuthnCredentialResponse
}

export interface HumanEnrollmentChallenge {
  challenge_id: string
  challenge: string
  ceremony: HumanEnrollmentCeremony
  audience: string
  origin: string
  rp_id: string
  principal_ref: string | null
  user_id: string | null
  allow_credentials: Array<{ id: string; type: 'public-key' }>
  expires_at: string
}

export interface HumanPairing {
  grant_id: string
  principal_ref: string
  status: string
  expires_at: string
  key_id?: string
  auth_method?: string
  enrollment_challenge_id?: string
  pairing_token?: string
}

export interface HumanSession {
  session_id: string
  principal_ref: string
  audience: string
  status: string
  expires_at: string
}

export interface DecisionReceipt {
  action: string
  acceptance_id: string | null
  candidate_id: string
  decision_id: string
  disposition: string
  idempotent: boolean
  revision: number
}

export function createHumanPairing(
  config: ApiClientConfig,
  body:
    | { challenge_id: string; credential: WebAuthnCredential; expires_at: string }
    | { principal_ref: string; enrollment_proof: string; expires_at: string },
): Promise<HumanPairing> {
  return request<HumanPairing>(config, 'POST', '/human/pairings', body)
}

export function issueHumanEnrollmentChallenge(
  config: ApiClientConfig,
  body: {
    ceremony: HumanEnrollmentCeremony
    key_id?: string
    session_id?: string
    csrf_token?: string
  },
): Promise<HumanEnrollmentChallenge> {
  return request<HumanEnrollmentChallenge>(config, 'POST', '/human/enrollment/challenges', body)
}

export function registerHumanCredential(
  config: ApiClientConfig,
  body: { challenge_id: string; credential: WebAuthnCredential },
): Promise<{ key_id: string; principal_ref: string; status: string; algorithm: string; fingerprint: string; rp_id: string; origin: string }> {
  return request<{ key_id: string; principal_ref: string; status: string; algorithm: string; fingerprint: string; rp_id: string; origin: string }>(config, 'POST', '/human/enrollment/credentials', body)
}

export function revokeHumanCredential(
  config: ApiClientConfig,
  body: { challenge_id: string; key_id: string; credential: WebAuthnCredential },
): Promise<{ key_id: string; principal_ref: string; status: string; revoked_grants: boolean }> {
  return request<{ key_id: string; principal_ref: string; status: string; revoked_grants: boolean }>(config, 'POST', '/human/enrollment/revoke', body)
}

export function createHumanSession(
  config: ApiClientConfig,
  body: { grant_id: string; pairing_token?: string; pairing_proof?: string; audience: string; csrf_token: string; expires_at?: string },
): Promise<HumanSession> {
  return request<HumanSession>(config, 'POST', '/human/sessions', body)
}

export function revokeHumanSession(
  config: ApiClientConfig,
  sessionId: string,
  body: { csrf_token: string },
): Promise<{ session_id: string; status: string }> {
  return request<{ session_id: string; status: string }>(
    config,
    'POST',
    `/human/sessions/${encodeURIComponent(sessionId)}/revoke`,
    body,
  )
}

export function getCandidateView(
  config: ApiClientConfig,
  candidateId: string,
  policyRevision = 1,
): Promise<CandidateView> {
  return request<CandidateView>(
    config,
    'GET',
    `/candidates/${encodeURIComponent(candidateId)}/view?policy_revision=${policyRevision}`,
  )
}

export function issueDecisionChallenge(
  config: ApiClientConfig,
  body: { session_id: string; candidate_id: string; action: DecisionChallenge['action']; replacement_acceptance_id?: string | null; policy_revision?: number },
): Promise<DecisionChallenge> {
  return request<DecisionChallenge>(config, 'POST', '/human/decision-challenges', body)
}

export function submitHumanDecision(
  config: ApiClientConfig,
  body: Record<string, unknown>,
): Promise<DecisionReceipt> {
  return request<DecisionReceipt>(config, 'POST', '/human/decisions', body)
}
