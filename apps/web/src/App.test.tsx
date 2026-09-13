import { describe, expect, it, vi, afterEach } from 'vitest'
import { App, createDefaultConfig } from './App'
import { AuthError, ApiError, NotFoundError } from './api'

// ---------------------------------------------------------------------------
// Mock fetch
// ---------------------------------------------------------------------------

const originalFetch = globalThis.fetch

function mockJson(data: unknown, status = 200) {
  globalThis.fetch = vi.fn(async () =>
    new Response(JSON.stringify(data), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  ) as typeof fetch
}

function mockNever() {
  globalThis.fetch = vi.fn(() => new Promise(() => {})) as typeof fetch
}

function mockSeq(items: Array<{ d: unknown; s?: number }>) {
  let i = 0
  globalThis.fetch = vi.fn(async () => {
    const it = items[Math.min(i++, items.length - 1)]
    return new Response(JSON.stringify(it.d), {
      status: it.s ?? 200,
      headers: { 'Content-Type': 'application/json' },
    })
  }) as typeof fetch
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const flush = () => new Promise<void>((r) => setTimeout(r, 60))

async function mount(): Promise<HTMLDivElement> {
  const { createRoot } = await import('react-dom/client')
  const el = document.createElement('div')
  document.body.appendChild(el)
  createRoot(el).render(<App />)
  await flush()
  return el
}

function click(el: Element | null) {
  ;(el as HTMLElement).click()
}

// ---------------------------------------------------------------------------

// A prior explicit Begin is represented by a durable server fixture, never
// synthesized by the product or inferred from ContextPackage ID.
async function selectFixtureGeneration(el: HTMLDivElement) {
  const contextId=(el.querySelector('#cp-id') as HTMLInputElement).value
  const previous=globalThis.fetch
  globalThis.fetch=vi.fn(async(input: RequestInfo | URL,init?:RequestInit)=>{
    const url=String(input)
    if((init?.method??'GET')==='GET'&&url.endsWith('/generations'))return new Response(JSON.stringify({task_revision:1,generations:[{task_id:'t_1',revision:1,control_revision:0,aborted:0,closed:0,ownership_unknown:0,inputs:{context_package_id:contextId,requirements_ref:'fixture:requirements',validation_ref:'fixture:validation',baseline_ref:'fixture:baseline',input_ref:'fixture:input'},writer:null,workspace:null,events:[]}]}),{status:200,headers:{'Content-Type':'application/json'}})
    return previous(input,init)
  }) as typeof fetch
  ;(Array.from(el.querySelectorAll('button')).find(b=>b.textContent==='Load generations') as HTMLButtonElement).click()
  await flush()
  ;(el.querySelector('input[name="generation"][value="1"]') as HTMLInputElement).click()
  await flush()
}

// API error classes
// ---------------------------------------------------------------------------

describe('api errors', () => {
  it('ApiError', () => {
    const e = new ApiError('x', 422)
    expect(e.status).toBe(422)
    expect(e.name).toBe('ApiError')
  })
  it('AuthError', () => {
    const e = new AuthError()
    expect(e.status).toBe(403)
    expect(e.name).toBe('AuthError')
  })
  it('NotFoundError', () => {
    const e = new NotFoundError('P', 'p_1')
    expect(e.status).toBe(404)
    expect(e.message).toContain('P')
  })
})

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

describe('App', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  it('exports App', () => { expect(typeof App).toBe('function') })

  it('maps the process-only development token to the auth header', async () => {
    vi.stubEnv('VITE_POLYNEXUS_LOOPBACK_TOKEN', 'process-only-app-token')
    try {
      const config = createDefaultConfig()
      expect(config.authConfigured).toBe(true)
      expect(await config.getAuthHeaders()).toEqual({
        'X-Loopback-Token': 'process-only-app-token',
      })
    } finally {
      vi.unstubAllEnvs()
    }
  })

  it('renders header', async () => {
    mockJson({ projects: [] })
    const el = await mount()
    expect(el.textContent).toContain('PolyNexus')
    expect(el.textContent).toContain('Development Baseline')
    el.remove()
  })

  it('keeps secondary work-mode guidance behind a disclosure', async () => {
    mockJson({ projects: [] })
    const el = await mount()
    const disclosure = el.querySelector('.disclosure-card') as HTMLDetailsElement

    expect(disclosure).not.toBeNull()
    expect(disclosure.open).toBe(false)
    disclosure.querySelector('summary')!.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(disclosure.open).toBe(true)
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

describe('loading', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  it('shows Loading projects', async () => {
    mockNever()
    const el = await mount()
    expect(el.textContent).toContain('Loading projects')
    el.remove()
  })

  it('has role=status', async () => {
    mockNever()
    const el = await mount()
    expect(el.querySelectorAll('[role="status"]').length).toBeGreaterThan(0)
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// Empty
// ---------------------------------------------------------------------------

describe('empty', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  it('shows No projects yet', async () => {
    mockJson({ projects: [] })
    const el = await mount()
    expect(el.textContent).toContain('No projects yet')
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// 403
// ---------------------------------------------------------------------------

describe('403', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  it('shows Authentication required', async () => {
    mockJson({ detail: 'nope' }, 403)
    const el = await mount()
    expect(el.textContent).toContain('Authentication required')
    el.remove()
  })

  it('has role=alert', async () => {
    mockJson({ detail: 'nope' }, 403)
    const el = await mount()
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('shows LOOPBACK_TOKEN hint', async () => {
    mockJson({ detail: 'nope' }, 403)
    const el = await mount()
    expect(el.textContent).toContain('LOOPBACK_TOKEN')
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// Project list
// ---------------------------------------------------------------------------

describe('project list', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  it('shows names and descriptions', async () => {
    mockJson({
      projects: [
        { id: 'p_1', name: 'Alpha', description: 'Desc A', created_at: '2026-01-01T00:00:00' },
        { id: 'p_2', name: 'Beta', description: null, created_at: '2026-01-02T00:00:00' },
      ],
    })
    const el = await mount()
    expect(el.textContent).toContain('Alpha')
    expect(el.textContent).toContain('Desc A')
    expect(el.textContent).toContain('Beta')
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// Create form
// ---------------------------------------------------------------------------

describe('create form', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  it('appears after clicking button', async () => {
    mockJson({ projects: [] })
    const el = await mount()
    click(el.querySelector('button'))
    await flush()
    expect(el.querySelector('form')).not.toBeNull()
    expect(el.querySelector('#project-name')).not.toBeNull()
    el.remove()
  })

  it('has aria-label=Create project', async () => {
    mockJson({ projects: [] })
    const el = await mount()
    click(el.querySelector('button'))
    await flush()
    expect(el.querySelector('form')?.getAttribute('aria-label')).toBe('Create project')
    el.remove()
  })

  it('submit disabled when name empty', async () => {
    mockJson({ projects: [] })
    const el = await mount()
    click(el.querySelector('button'))
    await flush()
    expect((el.querySelector('button[type="submit"]') as HTMLButtonElement).disabled).toBe(true)
    el.remove()
  })

  it('shows error on 422', async () => {
    mockSeq([
      { d: { projects: [] } },
      { d: { detail: 'whitespace only' }, s: 422 },
    ])
    const el = await mount()
    click(el.querySelector('button'))
    await flush()
    const input = el.querySelector('#project-name') as HTMLInputElement
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(input, '   ')
    input.dispatchEvent(new Event('input', { bubbles: true }))
    input.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()
    el.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flush()
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('POST success creates project and refreshes list', async () => {
    const calls: Array<{ method: string; url: string }> = []
    globalThis.fetch = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      const method = init?.method ?? 'GET'
      calls.push({ method, url })

      if (method === 'POST') {
        return new Response(
          JSON.stringify({ id: 'p_new', name: 'New', description: null, created_at: '2026-01-01T00:00:00' }),
          { status: 201, headers: { 'Content-Type': 'application/json' } },
        )
      }
      // GET: first call returns empty, subsequent calls return the created project
      const getCallCount = calls.filter((c) => c.method === 'GET').length
      const projects = getCallCount <= 1
        ? []
        : [{ id: 'p_new', name: 'New', description: null, created_at: '2026-01-01T00:00:00' }]
      return new Response(
        JSON.stringify({ projects }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      )
    }) as typeof fetch

    const el = await mount()
    expect(el.textContent).toContain('No projects yet')

    click(el.querySelector('button'))
    await flush()
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#project-name')!, 'New')
    el.querySelector('#project-name')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#project-name')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()
    el.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flush()

    const postCalls = calls.filter((c) => c.method === 'POST')
    expect(postCalls.length).toBe(1)
    const getCalls = calls.filter((c) => c.method === 'GET')
    expect(getCalls.length).toBeGreaterThanOrEqual(2)
    expect(el.textContent).toContain('New')
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

describe('navigation', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  const p1 = { id: 'p_1', name: 'Test', description: null, created_at: '2026-01-01T00:00:00' }
  const t1 = {
    id: 't_1', project_id: 'p_1', title: 'Review Task', workflow_id: 'review-minimal',
    workflow_version: 1, mode: 'REVIEW', context_package_id: null, created_at: '2026-01-01T00:00:00',
  }

  it('project → tasks', async () => {
    mockSeq([{ d: { projects: [p1] } }, { d: { tasks: [] } }])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    expect(el.textContent).toContain('Tasks')
    expect(el.textContent).toContain('Back')
    el.remove()
  })

  it('task → run prep', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    expect(el.textContent).toContain('Review Preparation')
    expect(el.textContent).toContain('Review Task')
    expect(el.textContent).toContain('ContextPackage ID')
    el.remove()
  })

  it('back from tasks → projects', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [] } },
      { d: { projects: [p1] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    const back = Array.from(el.querySelectorAll('button')).find((b) => b.textContent === 'Back')!
    back.click()
    await flush()
    expect(el.textContent).toContain('Test')
    el.remove()
  })

  it('back from run-prep → tasks', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
      { d: { tasks: [t1] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const back = Array.from(el.querySelectorAll('button')).find((b) => b.textContent?.includes('Back to tasks'))!
    back.click()
    await flush()
    expect(el.textContent).toContain('Tasks')
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// Task list
// ---------------------------------------------------------------------------

describe('task list', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  const p1 = { id: 'p_1', name: 'P', description: null, created_at: '2026-01-01T00:00:00' }

  it('shows titles and modes including Validate', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      {
        d: {
          tasks: [
            { id: 't_1', project_id: 'p_1', title: 'Code Review', workflow_id: 'review-minimal', workflow_version: 1, mode: 'REVIEW', context_package_id: null, created_at: '2026-01-01T00:00:00' },
            { id: 't_2', project_id: 'p_1', title: 'Analysis', workflow_id: 'review-minimal', workflow_version: 1, mode: 'DISCUSS', context_package_id: null, created_at: '2026-01-01T00:00:00' },
            { id: 't_3', project_id: 'p_1', title: 'Checks', workflow_id: 'review-minimal', workflow_version: 1, mode: 'VALIDATE', context_package_id: null, created_at: '2026-01-01T00:00:00' },
          ],
        },
      },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    expect(el.textContent).toContain('Code Review')
    expect(el.textContent).toContain('Review')
    expect(el.textContent).toContain('Analysis')
    expect(el.textContent).toContain('Discuss')
    expect(el.textContent).toContain('Checks')
    expect(el.textContent).toContain('Validate')
    el.remove()
  })

  it('shows error on 403', async () => {
    mockSeq([{ d: { projects: [p1] } }, { d: { detail: 'forbidden' }, s: 403 }])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    expect(el.textContent).toContain('Authentication required')
    el.remove()
  })

  it('shows error on 404', async () => {
    mockSeq([{ d: { projects: [p1] } }, { d: { detail: 'Project not found' }, s: 404 }])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('shows error on 422', async () => {
    mockSeq([{ d: { projects: [p1] } }, { d: { detail: 'invalid workflow' }, s: 422 }])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('shows empty when no tasks', async () => {
    mockSeq([{ d: { projects: [p1] } }, { d: { tasks: [] } }])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    expect(el.textContent).toContain('No tasks in this project yet')
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// CreateTaskForm error branches
// ---------------------------------------------------------------------------

describe('CreateTaskForm errors', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  const p1 = { id: 'p_1', name: 'P', description: null, created_at: '2026-01-01T00:00:00' }
  const t1 = {
    id: 't_1', project_id: 'p_1', title: 'Task', workflow_id: 'review-minimal',
    workflow_version: 1, mode: 'REVIEW', context_package_id: null, created_at: '2026-01-01T00:00:00',
  }

  it('shows error on task create 403', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [] } },
      { d: { detail: 'forbidden' }, s: 403 },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    const newTaskBtn = Array.from(el.querySelectorAll('button')).find((b) => b.textContent === 'New task')!
    newTaskBtn.click()
    await flush()
    el.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flush()
    expect(el.textContent).toContain('Authentication required')
    el.remove()
  })

  it('shows error on task create 404', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [] } },
      { d: { detail: 'Project not found' }, s: 404 },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    const newTaskBtn = Array.from(el.querySelectorAll('button')).find((b) => b.textContent === 'New task')!
    newTaskBtn.click()
    await flush()
    el.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flush()
    expect(el.textContent).toContain('Project not found')
    el.remove()
  })

  it('shows error on task create 422', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [] } },
      { d: { detail: 'invalid workflow version' }, s: 422 },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    const newTaskBtn = Array.from(el.querySelectorAll('button')).find((b) => b.textContent === 'New task')!
    newTaskBtn.click()
    await flush()
    el.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flush()
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// Run CREATED state
// ---------------------------------------------------------------------------

describe('Run CREATED', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  const p1 = { id: 'p_1', name: 'Test', description: null, created_at: '2026-01-01T00:00:00' }
  const t1 = {
    id: 't_1', project_id: 'p_1', title: 'Task', workflow_id: 'review-minimal',
    workflow_version: 1, mode: 'REVIEW', context_package_id: null, created_at: '2026-01-01T00:00:00',
  }

  it('displays CREATED / LOCAL / NONE', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      {
        d: {
          runs: [{
            id: 'run_1', task_id: 't_1', workflow_id: 'review-minimal', workflow_version: 1,
            context_package_id: 'ctx_1', execution_target: 'LOCAL', resume_mode: 'NONE',
            state: 'CREATED', runtime_ref: null, created_at: '2026-01-01T00:00:00',
            updated_at: '2026-01-01T00:00:00', events: [], result: null,
          }],
        },
      },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    expect(el.textContent).toContain('CREATED')
    expect(el.textContent).toContain('LOCAL')
    expect(el.textContent).toContain('NONE')
    expect(el.textContent).toContain('run_1')
    el.remove()
  })

  it('shows No runs yet', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    expect(el.textContent).toContain('No runs yet')
    el.remove()
  })

  it('shows error on run list 403', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { detail: 'forbidden' }, s: 403 },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    expect(el.textContent).toContain('Authentication required')
    el.remove()
  })

  it('shows error on run list 404', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { detail: 'Task not found' }, s: 404 },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('shows error on run create 422', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
      { d: { detail: 'ContextPackage not found' }, s: 422 },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-id')!, 'ctx_invalid')
    el.querySelector('#cp-id')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-id')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()
    await selectFixtureGeneration(el)
    el.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flush()
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('shows error on run create 403', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
      { d: { detail: 'forbidden' }, s: 403 },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-id')!, 'ctx_1')
    el.querySelector('#cp-id')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-id')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()
    await selectFixtureGeneration(el)
    el.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flush()
    expect(el.textContent).toContain('Authentication required')
    el.remove()
  })

  it('shows error on run create 404', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
      { d: { detail: 'Task not found' }, s: 404 },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-id')!, 'ctx_1')
    el.querySelector('#cp-id')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-id')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()
    await selectFixtureGeneration(el)
    el.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))
    await flush()
    expect(el.textContent).toContain('Task not found')
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// Accessibility
// ---------------------------------------------------------------------------

describe('accessibility', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  it('loading has role=status', async () => {
    mockNever()
    const el = await mount()
    expect(el.querySelectorAll('[role="status"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('error has role=alert', async () => {
    mockJson({ detail: 'x' }, 403)
    const el = await mount()
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('project form has aria-label', async () => {
    mockJson({ projects: [] })
    const el = await mount()
    click(el.querySelector('button'))
    await flush()
    expect(el.querySelector('form')?.getAttribute('aria-label')).toBe('Create project')
    el.remove()
  })

  it('task form has aria-label', async () => {
    const p1 = { id: 'p_1', name: 'P', description: null, created_at: '2026-01-01T00:00:00' }
    mockSeq([{ d: { projects: [p1] } }, { d: { tasks: [] } }])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    const newTaskBtn = Array.from(el.querySelectorAll('button')).find((b) => b.textContent === 'New task')!
    newTaskBtn.click()
    await flush()
    expect(el.querySelector('form')?.getAttribute('aria-label')).toBe('Create task')
    el.remove()
  })

  it('run form has aria-label', async () => {
    const p1 = { id: 'p_1', name: 'P', description: null, created_at: '2026-01-01T00:00:00' }
    const t1 = {
      id: 't_1', project_id: 'p_1', title: 'T', workflow_id: 'review-minimal',
      workflow_version: 1, mode: 'REVIEW', context_package_id: null, created_at: '2026-01-01T00:00:00',
    }
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    expect(el.querySelector('form')?.getAttribute('aria-label')).toBe('Create run')
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// WP-08B: ContextPackage authoring / selection
// ---------------------------------------------------------------------------

describe('WP-08B: ContextPackage authoring', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  const p1 = { id: 'p_1', name: 'Test', description: null, created_at: '2026-01-01T00:00:00' }
  const t1 = {
    id: 't_1', project_id: 'p_1', title: 'Task', workflow_id: 'review-minimal',
    workflow_version: 1, mode: 'REVIEW', context_package_id: null, created_at: '2026-01-01T00:00:00',
  }

  it('shows authoring toggle button', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    expect(el.textContent).toContain('Create new ContextPackage')
    el.remove()
  })

  it('opens authoring form on click', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()
    expect(el.querySelector('#cp-version')).not.toBeNull()
    expect(el.querySelector('#cp-instructions')).not.toBeNull()
    expect(el.querySelector('#cp-constraints')).not.toBeNull()
    expect(el.querySelector('#cp-project-facts')).not.toBeNull()
    el.remove()
  })

  it('create form has aria-label', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()
    const form = el.querySelector('#cp-authoring-form')
    expect(form?.getAttribute('aria-label')).toBe('Create context package')
    el.remove()
  })

  it('version field has aria-required', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()
    const versionInput = el.querySelector('#cp-version') as HTMLInputElement
    expect(versionInput.getAttribute('aria-required')).toBe('true')
    el.remove()
  })

  it('API posts to encoded path with full manifest shape including trim and blank omission', async () => {
    const calls: Array<{ method: string; url: string; body?: string }> = []
    const specialProject = { id: 'p_special/1 2', name: 'Special Project', description: null, created_at: '2026-01-01T00:00:00' }
    const specialTask = {
      id: 't_special', project_id: 'p_special/1 2', title: 'Task', workflow_id: 'review-minimal',
      workflow_version: 1, mode: 'REVIEW', context_package_id: null, created_at: '2026-01-01T00:00:00',
    }

    globalThis.fetch = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      const method = init?.method ?? 'GET'
      const body = init?.body as string | undefined
      calls.push({ method, url, body })

      if (method === 'POST' && url.includes('context-packages')) {
        return new Response(
          JSON.stringify({
            id: 'context_new', project_id: 'p_special/1 2', version: 2,
            instructions: [], constraints: [], project_facts: {},
            artifact_refs: [], prior_decision_refs: [], memory_refs: [],
            source_refs: [], created_at: '2026-01-01T00:00:00',
          }),
          { status: 201, headers: { 'Content-Type': 'application/json' } },
        )
      }
      if (method === 'GET' && url.includes('runs')) {
        return new Response(JSON.stringify({ runs: [] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      if (method === 'GET' && url.includes('tasks')) {
        return new Response(JSON.stringify({ tasks: [specialTask] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({ projects: [specialProject] }), {
        status: 200, headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch

    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    // Open authoring form
    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    // Set version
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-version')!, '2')
    el.querySelector('#cp-version')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-version')!.dispatchEvent(new Event('change', { bubbles: true }))

    // Helper for textarea
    const setTa = (selector: string, val: string) => {
      const taSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')!.set!
      taSetter.call(el.querySelector(selector)!, val)
      el.querySelector(selector)!.dispatchEvent(new Event('input', { bubbles: true }))
    }

    setTa('#cp-instructions', '  inst 1  \n\n  inst 2  \n')
    setTa('#cp-constraints', 'const 1\n\nconst 2\n')
    setTa('#cp-project-facts', ' key1 = value1 \n\n key2=value2 \n')
    setTa('#cp-artifact-refs', ' art1 \n\n art2 \n')
    setTa('#cp-prior-decision-refs', ' dec1 \n\n dec2 \n')
    setTa('#cp-memory-refs', ' mem1 \n\n mem2 \n')
    setTa('#cp-source-refs', ' src1 \n\n src2 \n')

    // Submit
    el.querySelector('#cp-authoring-form')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()

    const cpCalls = calls.filter((c) => c.url.includes('context-packages'))
    expect(cpCalls.length).toBe(1)
    expect(cpCalls[0].method).toBe('POST')
    // Verify URL encoding of special project id 'p_special/1 2'
    expect(cpCalls[0].url).toContain('/projects/p_special%2F1%202/context-packages')
    // Verify body shape and whitespace trim + blank line omission
    const body = JSON.parse(cpCalls[0].body!)
    expect(body.version).toBe(2)
    expect(body.instructions).toEqual(['inst 1', 'inst 2'])
    expect(body.constraints).toEqual(['const 1', 'const 2'])
    expect(body.project_facts).toEqual({ key1: 'value1', key2: 'value2' })
    expect(body.artifact_refs).toEqual(['art1', 'art2'])
    expect(body.prior_decision_refs).toEqual(['dec1', 'dec2'])
    expect(body.memory_refs).toEqual(['mem1', 'mem2'])
    expect(body.source_refs).toEqual(['src1', 'src2'])
    el.remove()
  })

  it('create success populates run form and subsequent Run create uses returned ContextPackage ID', async () => {
    const postCalls: Array<{ url: string; body: any }> = []
    let createdRun: any = null

    globalThis.fetch = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      const method = init?.method ?? 'GET'
      const body = init?.body ? JSON.parse(init.body as string) : undefined

      if (method === 'POST') {
        postCalls.push({ url, body })
        if (url.includes('context-packages')) {
          return new Response(
            JSON.stringify({
              id: 'context_returned', project_id: 'p_1', version: 3,
              instructions: [], constraints: [], project_facts: {},
              artifact_refs: [], prior_decision_refs: [], memory_refs: [],
              source_refs: [], created_at: '2026-01-01T00:00:00',
            }),
            { status: 201, headers: { 'Content-Type': 'application/json' } },
          )
        }
        if (url.includes('/runs')) {
          createdRun = {
            id: 'run_created_from_cp', task_id: 't_1', workflow_id: 'review-minimal', workflow_version: 1,
            context_package_id: body.context_package_id, execution_target: 'LOCAL', resume_mode: 'NONE',
            state: 'CREATED', runtime_ref: null, created_at: '2026-01-01T00:00:00',
            updated_at: '2026-01-01T00:00:00', events: [], result: null,
          }
          return new Response(
            JSON.stringify(createdRun),
            { status: 201, headers: { 'Content-Type': 'application/json' } },
          )
        }
      }
      if (method === 'GET' && url.includes('runs')) {
        return new Response(JSON.stringify({ runs: createdRun ? [createdRun] : [] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      if (method === 'GET' && url.includes('tasks')) {
        return new Response(JSON.stringify({ tasks: [t1] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({ projects: [p1] }), {
        status: 200, headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch

    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    // Open authoring form and submit ContextPackage
    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()
    el.querySelector('#cp-authoring-form')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()

    // Verify success message shown and input updated
    expect(el.textContent).toContain('context_returned')
    expect(el.textContent).toContain('version 3')
    const cpInput = el.querySelector('#cp-id') as HTMLInputElement
    expect(cpInput.value).toBe('context_returned')

    // Now submit Run form
    await selectFixtureGeneration(el)
    el.querySelector('form[aria-label="Create run"]')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()

    // Assert that Run POST body specifically used the returned ID
    const runPostCall = postCalls.find((c) => c.url.includes('/runs'))
    expect(runPostCall).toBeDefined()
    expect(runPostCall!.body.context_package_id).toBe('context_returned')

    // Verify UI reflects newly created run
    expect(el.textContent).toContain('run_created_from_cp')
    expect(el.textContent).toContain('CREATED')
    el.remove()
  })

  it('rejects version 0 and disables submit', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-version')!, '0')
    el.querySelector('#cp-version')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-version')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()

    const submitBtn = el.querySelector('#cp-authoring-form button[type="submit"]') as HTMLButtonElement
    expect(submitBtn.disabled).toBe(true)
    el.remove()
  })

  it('rejects version 1.5 (decimal) and disables submit without truncation', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-version')!, '1.5')
    el.querySelector('#cp-version')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-version')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()

    const submitBtn = el.querySelector('#cp-authoring-form button[type="submit"]') as HTMLButtonElement
    expect(submitBtn.disabled).toBe(true)
    el.remove()
  })

  it('rejects non-numeric version "abc" and disables submit', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-version')!, 'abc')
    el.querySelector('#cp-version')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-version')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()

    const submitBtn = el.querySelector('#cp-authoring-form button[type="submit"]') as HTMLButtonElement
    expect(submitBtn.disabled).toBe(true)
    el.remove()
  })

  it('rejects negative version -2 and disables submit', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-version')!, '-2')
    el.querySelector('#cp-version')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-version')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()

    const submitBtn = el.querySelector('#cp-authoring-form button[type="submit"]') as HTMLButtonElement
    expect(submitBtn.disabled).toBe(true)
    el.remove()
  })

  it('version empty blocks submission', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-version')!, '')
    el.querySelector('#cp-version')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-version')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()

    const submitBtn = el.querySelector('#cp-authoring-form button[type="submit"]') as HTMLButtonElement
    expect(submitBtn.disabled).toBe(true)
    el.remove()
  })

  it('project_facts invalid line shows validation error', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    const taSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')!.set!
    taSetter.call(el.querySelector('#cp-project-facts')!, 'no-equals-sign')
    el.querySelector('#cp-project-facts')!.dispatchEvent(new Event('input', { bubbles: true }))
    await flush()

    el.querySelector('#cp-authoring-form')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()
    expect(el.textContent).toContain('Invalid project_facts line')
    el.remove()
  })

  it('403 error preserves form values', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      const method = init?.method ?? 'GET'

      if (method === 'POST' && url.includes('context-packages')) {
        return new Response(
          JSON.stringify({ detail: 'forbidden' }),
          { status: 403, headers: { 'Content-Type': 'application/json' } },
        )
      }
      if (method === 'GET' && url.includes('runs')) {
        return new Response(JSON.stringify({ runs: [] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      if (method === 'GET' && url.includes('tasks')) {
        return new Response(JSON.stringify({ tasks: [t1] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({ projects: [p1] }), {
        status: 200, headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch

    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    // Set some values
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-version')!, '5')
    el.querySelector('#cp-version')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-version')!.dispatchEvent(new Event('change', { bubbles: true }))
    const taSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')!.set!
    taSetter.call(el.querySelector('#cp-instructions')!, 'Test instruction')
    el.querySelector('#cp-instructions')!.dispatchEvent(new Event('input', { bubbles: true }))
    await flush()

    el.querySelector('#cp-authoring-form')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()

    expect(el.textContent).toContain('Authentication required')
    // Form values preserved
    expect((el.querySelector('#cp-version') as HTMLInputElement).value).toBe('5')
    expect((el.querySelector('#cp-instructions') as HTMLTextAreaElement).value).toBe('Test instruction')
    el.remove()
  })

  it('404 error preserves form values', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      const method = init?.method ?? 'GET'

      if (method === 'POST' && url.includes('context-packages')) {
        return new Response(
          JSON.stringify({ detail: 'Project not found' }),
          { status: 404, headers: { 'Content-Type': 'application/json' } },
        )
      }
      if (method === 'GET' && url.includes('runs')) {
        return new Response(JSON.stringify({ runs: [] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      if (method === 'GET' && url.includes('tasks')) {
        return new Response(JSON.stringify({ tasks: [t1] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({ projects: [p1] }), {
        status: 200, headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch

    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    const taSetter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')!.set!
    taSetter.call(el.querySelector('#cp-instructions')!, 'Some instruction')
    el.querySelector('#cp-instructions')!.dispatchEvent(new Event('input', { bubbles: true }))
    await flush()

    el.querySelector('#cp-authoring-form')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()

    expect(el.textContent).toContain('Project not found')
    expect((el.querySelector('#cp-instructions') as HTMLTextAreaElement).value).toBe('Some instruction')
    el.remove()
  })

  it('422 error preserves form values', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      const method = init?.method ?? 'GET'

      if (method === 'POST' && url.includes('context-packages')) {
        return new Response(
          JSON.stringify({ detail: 'Invalid body' }),
          { status: 422, headers: { 'Content-Type': 'application/json' } },
        )
      }
      if (method === 'GET' && url.includes('runs')) {
        return new Response(JSON.stringify({ runs: [] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      if (method === 'GET' && url.includes('tasks')) {
        return new Response(JSON.stringify({ tasks: [t1] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({ projects: [p1] }), {
        status: 200, headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch

    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-version')!, '1')
    el.querySelector('#cp-version')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-version')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()

    el.querySelector('#cp-authoring-form')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()

    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    expect((el.querySelector('#cp-version') as HTMLInputElement).value).toBe('1')
    el.remove()
  })

  it('manual ContextPackage ID still creates Run', async () => {
    let createdRun: any = null
    globalThis.fetch = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      const method = init?.method ?? 'GET'

      if (method === 'POST' && url.includes('/runs')) {
        createdRun = {
          id: 'run_1', task_id: 't_1', workflow_id: 'review-minimal', workflow_version: 1,
          context_package_id: 'ctx_manual', execution_target: 'LOCAL', resume_mode: 'NONE',
          state: 'CREATED', runtime_ref: null, created_at: '2026-01-01T00:00:00',
          updated_at: '2026-01-01T00:00:00', events: [], result: null,
        }
        return new Response(
          JSON.stringify(createdRun),
          { status: 201, headers: { 'Content-Type': 'application/json' } },
        )
      }
      if (method === 'GET' && url.includes('runs')) {
        return new Response(JSON.stringify({ runs: createdRun ? [createdRun] : [] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      if (method === 'GET' && url.includes('tasks')) {
        return new Response(JSON.stringify({ tasks: [t1] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({ projects: [p1] }), {
        status: 200, headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch

    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    // Set manual CP ID
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-id')!, 'ctx_manual')
    el.querySelector('#cp-id')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-id')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()

    // Submit run creation
    await selectFixtureGeneration(el)
    el.querySelector('form[aria-label="Create run"]')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()

    expect(el.textContent).toContain('run_1')
    expect(el.textContent).toContain('CREATED')
    el.remove()
  })

  it('submitting disables buttons', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    // Now mock endless fetch for the submit
    mockNever()

    // Set CP ID and submit run
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
    setter.call(el.querySelector('#cp-id')!, 'ctx_1')
    el.querySelector('#cp-id')!.dispatchEvent(new Event('input', { bubbles: true }))
    el.querySelector('#cp-id')!.dispatchEvent(new Event('change', { bubbles: true }))
    await flush()

    await selectFixtureGeneration(el)
    el.querySelector('form[aria-label="Create run"]')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()

    expect(el.textContent).toContain('Creating run...')
    el.remove()
  })

  it('back navigation from run-prep works', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
      { d: { tasks: [t1] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const back = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Back to tasks'),
    )!
    back.click()
    await flush()
    expect(el.textContent).toContain('Tasks')
    el.remove()
  })

  it('labels have stable ids and describedby', async () => {
    mockSeq([
      { d: { projects: [p1] } },
      { d: { tasks: [t1] } },
      { d: { runs: [] } },
    ])
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    // Open authoring form
    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    // Check labels have htmlFor matching input ids
    const labels = el.querySelectorAll('label')
    labels.forEach((label) => {
      const htmlFor = label.getAttribute('for')
      if (htmlFor) {
        expect(el.querySelector(`#${htmlFor}`)).not.toBeNull()
      }
    })

    // Check cp-id has describedby
    const cpIdInput = el.querySelector('#cp-id')
    expect(cpIdInput?.getAttribute('aria-describedby')).toBe('cp-id-hint')
    el.remove()
  })

  it('role=alert on error, role=status on success', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = typeof input === 'string' ? input : input.toString()
      const method = init?.method ?? 'GET'

      if (method === 'POST' && url.includes('context-packages')) {
        return new Response(
          JSON.stringify({ detail: 'forbidden' }),
          { status: 403, headers: { 'Content-Type': 'application/json' } },
        )
      }
      if (method === 'GET' && url.includes('runs')) {
        return new Response(JSON.stringify({ runs: [] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      if (method === 'GET' && url.includes('tasks')) {
        return new Response(JSON.stringify({ tasks: [t1] }), {
          status: 200, headers: { 'Content-Type': 'application/json' },
        })
      }
      return new Response(JSON.stringify({ projects: [p1] }), {
        status: 200, headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch

    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()

    const toggleBtn = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.includes('Create new ContextPackage')
    )!
    toggleBtn.click()
    await flush()

    el.querySelector('#cp-authoring-form')!.dispatchEvent(
      new Event('submit', { bubbles: true, cancelable: true }),
    )
    await flush()

    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })
})

// ---------------------------------------------------------------------------
// WP-09D: Run detail
// ---------------------------------------------------------------------------

describe('WP-09D run detail', () => {
  afterEach(() => { globalThis.fetch = originalFetch })
  const p1 = { id: 'p_1', name: 'P', description: null, created_at: '2026-01-01T00:00:00' }
  const t1 = { id: 't_1', project_id: 'p_1', title: 'T', workflow_id: 'review-minimal', workflow_version: 1, mode: 'REVIEW', context_package_id: null, created_at: '2026-01-01T00:00:00' }
  const runA = { id: 'run_1', task_id: 't_1', workflow_id: 'review-minimal', workflow_version: 1, context_package_id: 'ctx_1', execution_target: 'LOCAL', resume_mode: 'NONE', state: 'COMPLETED', runtime_ref: null, created_at: '2026-01-01T00:00:00', updated_at: '2026-01-01T00:00:00', events: [], result: null }
  const ev1 = { id: 'ev_1', task_id: 't_1', run_id: 'run_1', actor_id: 'a', source: 's', type: 'RUNTIME_EVIDENCE', status: 'PASS', artifact_refs: [], metadata: {}, observed_at: '2026-01-01T01:00:00' }
  const f1 = { id: 'f_1', task_id: 't_1', run_id: 'run_1', title: 'Find', description: 'desc', severity: 'LOW', evidence_refs: [], status: 'OPEN', created_at: '2026-01-01T01:00:00' }
  const art1 = { id: 'art_1', project_id: 'p_1', task_id: 't_1', run_id: 'run_1', artifact_type: 'TEXT', mime_type: 'text/plain', source_type: 'test', storage_ref: 'ref1', sha256: 'a'.repeat(64), size: 10 }
  const hist1 = { id: 'h1', run_id: 'run_1', from_state: 'CREATED', to_state: 'STARTING', occurred_at: '2026-01-01T00:00:00', reason: null }
  const hist2 = { id: 'h2', run_id: 'run_1', from_state: 'STARTING', to_state: 'RUNNING', occurred_at: '2026-01-01T00:01:00', reason: null }
  const resultObj = { run_id: 'run_1', status: 'COMPLETED', summary: 'done', finding_ids: ['f_1'], evidence_ids: ['ev_1'], artifact_ids: ['art_1'] }

  async function openDetailWithMocks(fetchFn: typeof fetch) {
    globalThis.fetch = fetchFn as typeof fetch
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    // runs list is already mocked to contain runA; now click View result / history
    const btn = Array.from(el.querySelectorAll('button')).find(b => b.textContent?.includes('View result'))!
    btn.click()
    await flush()
    await flush()
    return el
  }

  it('opens detail from run list', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/runs/run_1/result')) return new Response(JSON.stringify({ result: resultObj }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1/findings')) return new Response(JSON.stringify({ findings: [f1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1/evidence')) return new Response(JSON.stringify({ evidence: [ev1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1/artifacts')) return new Response(JSON.stringify({ artifacts: [art1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1/history')) return new Response(JSON.stringify({ events: [hist1, hist2] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.textContent).toContain('Run Detail')
    expect(el.textContent).toContain('run_1')
    el.remove()
  })

  it('keeps secondary run data collapsed while preserving result focus', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: resultObj }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [f1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [ev1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [art1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [hist1, hist2] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch

    const el = await openDetailWithMocks(globalThis.fetch)
    const taskInfoDisclosure = el.querySelector('.task-info .detail-disclosure') as HTMLDetailsElement
    const evidenceDisclosure = el.querySelector('[aria-labelledby="evidence-heading"] .detail-disclosure') as HTMLDetailsElement

    expect(taskInfoDisclosure.open).toBe(false)
    expect(evidenceDisclosure.open).toBe(false)
    expect(el.textContent).toContain('done')
    evidenceDisclosure.querySelector('summary')!.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    expect(evidenceDisclosure.open).toBe(true)
    el.remove()
  })

  it('calls five query URLs with encoded runId and wrappers', async () => {
    const specialId = 'run 1/2'
    const runSpecial = { ...runA, id: specialId }
    const calls: string[] = []
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      calls.push(url)
      if (url.includes('/result')) return new Response(JSON.stringify({ result: null }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/') && !url.includes('/runs/run%20')) return new Response(JSON.stringify(runSpecial), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runSpecial] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const btn = Array.from(el.querySelectorAll('button')).find(b => b.textContent?.includes('View result'))!
    btn.click()
    await flush(); await flush()
    const enc = encodeURIComponent(specialId)
    expect(calls.some(c => c.includes(`/runs/${enc}/result`))).toBe(true)
    expect(calls.some(c => c.includes(`/runs/${enc}/findings`))).toBe(true)
    expect(calls.some(c => c.includes(`/runs/${enc}/evidence`))).toBe(true)
    expect(calls.some(c => c.includes(`/runs/${enc}/artifacts`))).toBe(true)
    expect(calls.some(c => c.includes(`/runs/${enc}/history`))).toBe(true)
    el.remove()
  })

  it('renders result success', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: resultObj }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/runs')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.textContent).toContain('done')
    expect(el.textContent).toContain('COMPLETED')
    el.remove()
  })

  it('renders result null empty state without fabrication', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: null }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && url.includes('/runs/run_1')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.textContent).toContain('No result yet')
    expect(el.textContent).not.toContain('fabricated')
    el.remove()
  })

  it('renders findings/evidence/artifacts/history success', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: resultObj }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [f1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [ev1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [art1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [hist1, hist2] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.textContent).toContain('Find')
    expect(el.textContent).toContain('RUNTIME_EVIDENCE')
    expect(el.textContent).toContain('ref1')
    expect(el.textContent).toContain('CREATED')
    el.remove()
  })

  it('shows empty states for empty lists', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: null }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.textContent).toContain('No findings')
    expect(el.textContent).toContain('No evidence')
    expect(el.textContent).toContain('No artifacts')
    expect(el.textContent).toContain('No history')
    el.remove()
  })

  it('preserves history order from API', async () => {
    const evA = { id: 'a', run_id: 'run_1', from_state: 'CREATED', to_state: 'STARTING', occurred_at: '2026-01-02T00:00:00', reason: null }
    const evB = { id: 'b', run_id: 'run_1', from_state: 'STARTING', to_state: 'FAILED', occurred_at: '2026-01-03T00:00:00', reason: 'err' }
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: null }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [evB, evA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    const idxB = el.textContent!.indexOf('STARTING → FAILED')
    const idxA = el.textContent!.indexOf('CREATED → STARTING')
    expect(idxB < idxA).toBe(true)
    el.remove()
  })

  it('shows 403 with LOOPBACK_TOKEN hint', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/runs/run_1')) return new Response(JSON.stringify({ detail: 'forbidden' }), { status: 403, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.textContent).toContain('Authentication required')
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('shows 404 Run not found', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/runs/run_1')) return new Response(JSON.stringify({ detail: 'not found' }), { status: 404, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.textContent).toContain('Run not found')
    el.remove()
  })

  it('shows 422 validation error', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/runs/run_1')) return new Response(JSON.stringify({ detail: 'mismatch' }), { status: 422, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.textContent).toContain('Validation error')
    expect(el.textContent).not.toContain('mismatch')
    el.remove()
  })

  it('shows generic error and retry', async () => {
    let first = true
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/runs/run_1/result') && first) { first = false; return new Response(JSON.stringify({ detail: 'oops' }), { status: 500, headers: { 'Content-Type': 'application/json' } }) }
      if (url.includes('/result')) return new Response(JSON.stringify({ result: resultObj }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    const retry = Array.from(el.querySelectorAll('button')).find(b => b.textContent === 'Retry')!
    retry.click()
    await flush(); await flush()
    expect(el.textContent).toContain('done')
    el.remove()
  })

  it('loading shows role status', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/runs/run_1/result') || url.includes('/findings') || url.includes('/evidence') || url.includes('/artifacts') || url.includes('/history')) {
        return new Promise(() => {}) as Promise<Response>
      }
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await mount()
    click(el.querySelector('.project-item-btn'))
    await flush()
    click(el.querySelector('.task-item-btn'))
    await flush()
    const btn = Array.from(el.querySelectorAll('button')).find(b => b.textContent?.includes('View result'))!
    btn.click()
    await flush()
    expect(el.querySelectorAll('[role="status"]').length).toBeGreaterThan(0)
    el.remove()
  })

  it('retry does not retain stale data', async () => {
    let call = 0
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/runs/run_1/result') && call === 0) { call++; return new Response(JSON.stringify({ detail: 'err' }), { status: 500, headers: { 'Content-Type': 'application/json' } }) }
      if (url.includes('/result')) return new Response(JSON.stringify({ result: null }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.querySelectorAll('[role="alert"]').length).toBeGreaterThan(0)
    const retry = Array.from(el.querySelectorAll('button')).find(b => b.textContent === 'Retry')!
    retry.click()
    await flush(); await flush()
    expect(el.querySelectorAll('[role="alert"]').length).toBe(0)
    expect(el.textContent).toContain('No result yet')
    el.remove()
  })

  it('back navigation returns to preparation', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: null }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    const back = Array.from(el.querySelectorAll('button')).find(b => b.textContent?.includes('Back to preparation'))!
    back.click()
    await flush()
    expect(el.textContent).toContain('Review Preparation')
    el.remove()
  })

  it('has accessible labels and headings', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: null }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.querySelector('#run-detail-heading')).not.toBeNull()
    expect(el.querySelectorAll('h3').length).toBeGreaterThanOrEqual(5)
    expect(el.querySelector('button[aria-label="Back to run preparation"]')).not.toBeNull()
    el.remove()
  })

  it('artifact shows metadata only, no content', async () => {
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: null }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [art1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    expect(el.textContent).toContain('ref1')
    expect(el.textContent).toContain(art1.sha256)
    expect(el.textContent).not.toContain('content')
    el.remove()
  })

  it('shows full metadata/reference fields for all sections', async () => {
    const fFull = { id: 'f_1', task_id: 't_1', run_id: 'run_1', title: 'FindTitle', description: 'FindDesc', severity: 'LOW', evidence_refs: ['ev_1'], status: 'OPEN', created_at: '2026-01-01T01:00:00' }
    const eFull = { id: 'ev_1', task_id: 't_1', run_id: 'run_1', actor_id: 'actor_1', source: 'src1', type: 'TOOL_EVIDENCE', status: 'PASS', artifact_refs: ['art_1'], metadata: { k: 'v' }, observed_at: '2026-01-01T02:00:00' }
    const aFull = { id: 'art_1', project_id: 'p_1', task_id: 't_1', run_id: 'run_1', artifact_type: 'TEXT', mime_type: 'text/plain', source_type: 'test', storage_ref: 'ref1', sha256: 'a'.repeat(64), size: 10 }
    const hFull = { id: 'h1', run_id: 'run_1', from_state: 'CREATED', to_state: 'STARTING', occurred_at: '2026-01-01T00:00:00', reason: 'r' }
    globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/result')) return new Response(JSON.stringify({ result: resultObj }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [fFull] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [eFull] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [aFull] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/history')) return new Response(JSON.stringify({ events: [hFull] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs/run_1') && !url.includes('/result')) return new Response(JSON.stringify(runA), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [runA] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [t1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
      return new Response(JSON.stringify({ projects: [p1] }), { status: 200, headers: { 'Content-Type': 'application/json' } })
    }) as typeof fetch
    const el = await openDetailWithMocks(globalThis.fetch)
    // Finding fields
    expect(el.textContent).toContain('f_1')
    expect(el.textContent).toContain('FindTitle')
    expect(el.textContent).toContain('FindDesc')
    expect(el.textContent).toContain('LOW')
    expect(el.textContent).toContain('OPEN')
    expect(el.textContent).toContain('ev_1')
    expect(el.textContent).toContain('2026-01-01T01:00:00')
    // Finding task_id/run_id (WP-09D Attempt 3 fix)
    expect(el.textContent).toContain('task:t_1')
    expect(el.textContent).toContain('run:run_1')
    expect(el.textContent).toContain('f_1 — task:t_1 — run:run_1 — FindTitle')
    // Evidence fields
    expect(el.textContent).toContain('ev_1')
    expect(el.textContent).toContain('actor_1')
    expect(el.textContent).toContain('src1')
    expect(el.textContent).toContain('TOOL_EVIDENCE')
    expect(el.textContent).toContain('PASS')
    expect(el.textContent).toContain('art_1')
    expect(el.textContent).toContain('"k":"v"')
    expect(el.textContent).toContain('2026-01-01T02:00:00')
    // Evidence task_id/run_id (WP-09D Attempt 3 fix)
    expect(el.textContent).toContain('ev_1 — task:t_1 — run:run_1 — actor_1')
    // Artifact fields
    expect(el.textContent).toContain('art_1')
    expect(el.textContent).toContain('project:p_1')
    expect(el.textContent).toContain('task:t_1')
    expect(el.textContent).toContain('run:run_1')
    expect(el.textContent).toContain('TEXT')
    expect(el.textContent).toContain('text/plain')
    expect(el.textContent).toContain('test')
    expect(el.textContent).toContain('ref1')
    expect(el.textContent).toContain('a'.repeat(64))
    expect(el.textContent).toContain('10 bytes')
    // History fields
    expect(el.textContent).toContain('h1')
    expect(el.textContent).toContain('run:run_1')
    expect(el.textContent).toContain('CREATED → STARTING')
    expect(el.textContent).toContain('2026-01-01T00:00:00')
    expect(el.textContent).toContain('r')
    // Ensure no artifact content read or secret leak
    expect(el.textContent).not.toContain('content')
    expect(el.textContent).not.toContain('LOOPBACK_TOKEN')
    el.remove()
  })
})
