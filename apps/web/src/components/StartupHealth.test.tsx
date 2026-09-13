import { afterEach, describe, expect, it, vi } from 'vitest'
import { StartupHealth } from './StartupHealth'
import type { ApiClientConfig } from '../api'

const originalFetch = globalThis.fetch
const flush = () => new Promise<void>((resolve) => setTimeout(resolve, 60))

const health = {
  status: 'ok',
  service: 'polynexus-core',
  version: '0.1.0',
  baseline: 'development-v1.0',
  readiness: 'partial',
  layers: {
    process: { status: 'ready' },
    schema: { status: 'ready' },
    database_integrity: { status: 'ready' },
    core: { status: 'ready' },
    api_auth: { status: 'ready' },
    web_client: { status: 'unknown', reason: 'not_observed_by_core' },
    runtime: { status: 'unknown', reason: 'no_live_runtime_probe' },
  },
}

async function mount(config: ApiClientConfig): Promise<HTMLDivElement> {
  const { createRoot } = await import('react-dom/client')
  const element = document.createElement('div')
  document.body.appendChild(element)
  createRoot(element).render(<StartupHealth config={config} />)
  await flush()
  return element
}

function pairedConfig(token = 'process-only-test-token'): ApiClientConfig {
  return {
    baseUrl: '/api/v1',
    authConfigured: true,
    getAuthHeaders: () => ({ 'X-Loopback-Token': token }),
  }
}

describe('StartupHealth', () => {
  afterEach(() => {
    globalThis.fetch = originalFetch
    document.body.replaceChildren()
  })

  it('fails closed without a process-scoped pairing credential', async () => {
    globalThis.fetch = vi.fn() as typeof fetch
    const element = await mount({
      baseUrl: '/api/v1',
      authConfigured: false,
      getAuthHeaders: () => ({}),
    })

    expect(element.textContent).toContain('Web/clientnot_ready')
    expect(element.textContent).toContain('pairing_not_configured')
    expect(globalThis.fetch).not.toHaveBeenCalled()
  })

  it('marks the fresh client ready only after a protected API succeeds', async () => {
    globalThis.fetch = vi.fn(async (input, init) => {
      const url = String(input)
      const body = url.endsWith('/health') ? health : { projects: [] }
      return new Response(JSON.stringify(body), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch
    const element = await mount(pairedConfig())

    expect(element.textContent).toContain('Processready')
    expect(element.textContent).toContain('Schemaready')
    expect(element.textContent).toContain('API/authready')
    expect(element.textContent).toContain('Web/clientready')
    expect(element.textContent).toContain('Runtimeunknown')
    expect(element.textContent).toContain('authenticated_api_verified')
    for (const [, init] of vi.mocked(globalThis.fetch).mock.calls) {
      expect(init?.headers).toMatchObject({
        'X-Loopback-Token': 'process-only-test-token',
      })
    }
    expect(element.textContent).not.toContain('process-only-test-token')
  })

  it('reports an incorrect token as not ready without exposing it', async () => {
    globalThis.fetch = vi.fn(async (input) => {
      const isHealth = String(input).endsWith('/health')
      return new Response(JSON.stringify(isHealth ? health : { detail: 'rejected' }), {
        status: isHealth ? 200 : 403,
        headers: { 'Content-Type': 'application/json' },
      })
    }) as typeof fetch
    const element = await mount(pairedConfig('wrong-process-token'))

    expect(element.textContent).toContain('Web/clientnot_ready')
    expect(element.textContent).toContain('authentication_rejected')
    expect(element.textContent).not.toContain('wrong-process-token')
  })
})
