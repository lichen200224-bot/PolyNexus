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
  id: string
  name: string
  description: string | null
  created_at: string
}

export interface Task {
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
  name: string
  description?: string | null
}

export interface TaskCreateRequest {
  title: string
  workflow_id: string
  workflow_version: number
  mode?: string | null
  context_package_id?: string | null
}

export interface RunCreateRequest {
  context_package_id: string
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
