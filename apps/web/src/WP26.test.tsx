import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { App } from './App'

const originalFetch = globalThis.fetch
const flush = () => new Promise<void>((resolve) => setTimeout(resolve, 80))

async function mount() {
  const el = document.createElement('div')
  document.body.appendChild(el)
  createRoot(el).render(<App />)
  await flush()
  return el
}

const project = { id: 'p_1', name: 'Project', description: null, created_at: '2026-01-01T00:00:00' }
const task = {
  id: 't_1', project_id: 'p_1', title: 'Task', workflow_id: 'review-minimal',
  workflow_version: 1, mode: 'REVIEW', context_package_id: null, created_at: '2026-01-01T00:00:00',
}

function runFixture(state: string) {
  return {
    id: 'run_1', task_id: 't_1', workflow_id: 'review-minimal', workflow_version: 1,
    context_package_id: 'ctx_1', execution_target: 'LOCAL', resume_mode: 'NONE', state,
    runtime_ref: null, created_at: '2026-01-01T00:00:00', updated_at: '2026-01-01T00:00:00',
    events: [], result: null,
  }
}

function installRunFixture(state: string) {
  const run = runFixture(state)
  globalThis.fetch = vi.fn(async (input: string | URL | Request) => {
    const url = typeof input === 'string' ? input : input.toString()
    if (url.includes('/result')) return new Response(JSON.stringify({ result: null }), { status: 200 })
    if (url.includes('/findings')) return new Response(JSON.stringify({ findings: [] }), { status: 200 })
    if (url.includes('/evidence')) return new Response(JSON.stringify({ evidence: [] }), { status: 200 })
    if (url.includes('/artifacts')) return new Response(JSON.stringify({ artifacts: [] }), { status: 200 })
    if (url.includes('/history')) return new Response(JSON.stringify({ events: [] }), { status: 200 })
    if (url.includes('/runs/run_1')) return new Response(JSON.stringify(run), { status: 200 })
    if (url.includes('/runs')) return new Response(JSON.stringify({ runs: [run] }), { status: 200 })
    if (url.includes('/tasks')) return new Response(JSON.stringify({ tasks: [task] }), { status: 200 })
    return new Response(JSON.stringify({ projects: [project] }), { status: 200 })
  }) as typeof fetch
}

async function openRunDetail(state: string) {
  installRunFixture(state)
  const el = await mount()
  el.querySelector<HTMLButtonElement>('.project-item-btn')!.click()
  await flush()
  el.querySelector<HTMLButtonElement>('.task-item-btn')!.click()
  await flush()
  Array.from(el.querySelectorAll('button')).find((button) => button.textContent?.includes('View result'))!.click()
  await flush()
  return el
}

describe('WP-26 UX progressive disclosure and state contract', () => {
  afterEach(() => { globalThis.fetch = originalFetch })

  it('provides a keyboard skip link and keeps secondary guidance collapsed', async () => {
    globalThis.fetch = vi.fn(async () => new Response(JSON.stringify({ projects: [] }), { status: 200 })) as typeof fetch
    const el = await mount()
    const skip = el.querySelector<HTMLAnchorElement>('.skip-link')
    expect(skip?.getAttribute('href')).toBe('#workspace-content')
    expect(skip?.textContent).toContain('Skip to workspace')
    expect((el.querySelector('.disclosure-card') as HTMLDetailsElement).open).toBe(false)
    el.remove()
  })

  it('offers a retryable project failure and does not retain stale data', async () => {
    let first = true
    globalThis.fetch = vi.fn(async () => {
      if (first) {
        first = false
        return new Response(JSON.stringify({ detail: 'server detail' }), { status: 500 })
      }
      return new Response(JSON.stringify({ projects: [project] }), { status: 200 })
    }) as typeof fetch
    const el = await mount()
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Unable to load projects')
    expect(el.textContent).not.toContain('server detail')
    el.querySelector<HTMLButtonElement>('[role="alert"] button')!.click()
    await flush()
    expect(el.textContent).toContain('Project')
    el.remove()
  })

  it.each([
    ['HUMAN_REQUIRED', 'Human action required'],
    ['FAILED', 'Run ended: FAILED'],
    ['TIMED_OUT', 'Run ended: TIMED_OUT'],
  ])('exposes %s as an explicit non-success state', async (state, message) => {
    const el = await openRunDetail(state)
    expect(el.querySelector('[role="alert"]')?.textContent).toContain(message)
    expect(el.textContent).toContain(state)
    el.remove()
  })
})
