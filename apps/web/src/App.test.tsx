import { describe, expect, it, vi, afterEach } from 'vitest'
import { App } from './App'
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

  it('renders header', async () => {
    mockJson({ projects: [] })
    const el = await mount()
    expect(el.textContent).toContain('PolyNexus')
    expect(el.textContent).toContain('Development Baseline')
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
