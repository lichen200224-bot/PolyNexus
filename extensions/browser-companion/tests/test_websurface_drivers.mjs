import assert from 'node:assert/strict'
import test from 'node:test'

import {
  FALLBACK_MODE,
  DRIVER_STATUS,
  executeInTab,
  manualFallback,
  normalizeDriverResult,
  sanitizeContext,
  sanitizeWebText,
} from '../src/driver-contract.js'
import { LoopbackClient, LoopbackClientError, validateLoopbackBaseUrl } from '../src/loopback-client.js'
import { chatgptDriver } from '../src/drivers/chatgpt.js'
import { claudeDriver } from '../src/drivers/claude.js'
import { geminiDriver } from '../src/drivers/gemini.js'

function fakeBrowser(result = true) {
  const calls = []
  return {
    calls,
    scripting: {
      async executeScript(request) {
        calls.push(request)
        return [{ result: typeof result === 'function' ? result(request) : result }]
      },
    },
  }
}

function fakeComposerDocument({ answer = 'safe answer', sendable = true } = {}) {
  let sent = 0
  const field = {
    value: '',
    disabled: false,
    dispatchEvent() {},
  }
  const send = {
    disabled: !sendable,
    click() { sent += 1 },
  }
  const originalDocument = globalThis.document
  const originalInputEvent = globalThis.InputEvent
  globalThis.document = {
    querySelector(selector) {
      if (selector.includes('send') || selector.includes('Send') || selector.includes('submit')) return send
      return field
    },
    querySelectorAll() {
      return [{ innerText: answer }]
    },
  }
  globalThis.InputEvent = class InputEvent {}
  return {
    field,
    get sent() { return sent },
    restore() {
      globalThis.document = originalDocument
      globalThis.InputEvent = originalInputEvent
    },
  }
}

test('sanitizes bounded web text and context', () => {
  const value = sanitizeWebText('api_key=hidden-value C:\\private\\file.txt ' + 'x'.repeat(5000), 128)
  assert.equal(value.includes('hidden-value'), false)
  assert.equal(value.includes('C:\\private\\file.txt'), false)
  assert.equal(value.length <= 128, true)
  assert.equal(sanitizeContext({ instructions: ['Keep it short'], constraints: ['No secrets'] }), 'Keep it short\nNo secrets')
})

test('redacts POSIX paths and file URIs without corrupting ordinary URLs', () => {
  const value = sanitizeWebText('/home/user/secret.txt file:///var/lib/app/state.json')
  assert.equal(value.includes('/home/user/secret.txt'), false)
  assert.equal(value.includes('file:///var/lib/app/state.json'), false)
  assert.equal(value.includes('[PATH_REDACTED]'), true)
  assert.equal(sanitizeWebText('https://example.test/api/v1'), 'https://example.test/api/v1')
})

test('driver URL matching is exact and launch is fixed to approved vendor origin', async () => {
  assert.equal(chatgptDriver.matches('https://chatgpt.com/c/1'), true)
  assert.equal(chatgptDriver.matches('https://evil-chatgpt.com/c/1'), false)
  assert.equal(claudeDriver.matches('https://claude.ai/new'), true)
  assert.equal(geminiDriver.matches('https://gemini.google.com/app'), true)
  const opened = []
  const result = await chatgptDriver.launch({ tabs: { create: async (tab) => opened.push(tab) } })
  assert.deepEqual(result, { status: DRIVER_STATUS.READY, action: 'LAUNCHED', driver_id: 'chatgpt-web' })
  assert.deepEqual(opened, [{ url: 'https://chatgpt.com/' }])
})

test('assisted flow fills, pauses for confirmation, and sends only when confirmed', async () => {
  const page = fakeComposerDocument({ answer: 'captured answer' })
  try {
    const browser = fakeBrowser(({ func, args }) => func(...args))
    const filled = await chatgptDriver.fill(7, { instructions: ['Answer safely'] }, browser)
    assert.equal(filled.action, 'FILLED')
    assert.equal(filled.requires_user_confirmation, true)
    assert.equal(page.sent, 0)

    const pending = await chatgptDriver.requestUserConfirmation()
    assert.equal(pending.automatic_send, false)
    assert.equal(pending.requires_user_confirmation, true)

    const rejected = await chatgptDriver.sendConfirmed(7, false, browser)
    assert.deepEqual(rejected, {
      status: DRIVER_STATUS.DEGRADED,
      fallback: FALLBACK_MODE,
      reason: 'user_confirmation_required',
    })
    assert.equal(page.sent, 0)

    const sent = await chatgptDriver.sendConfirmed(7, true, browser)
    assert.equal(sent.action, 'SENT')
    assert.equal(sent.user_confirmed, true)
    assert.equal(page.sent, 1)
  } finally {
    page.restore()
  }
})

test('capture normalizes to bounded AI opinion and driver failures use manual fallback', async () => {
  const page = fakeComposerDocument({ answer: 'captured answer' })
  try {
    const captured = await claudeDriver.capture(3, fakeBrowser({ text: 'token=hidden C:\\secret\\answer.txt' }))
    assert.equal(captured.kind, 'AI_OPINION')
    assert.equal(captured.text.includes('hidden'), false)
    assert.equal(captured.text.includes('C:\\secret\\answer.txt'), false)

    const failed = await geminiDriver.health(3, {
      scripting: { executeScript: async () => { throw new Error('vendor detail') } },
    })
    assert.deepEqual(failed, manualFallback('driver_unavailable'))
  } finally {
    page.restore()
  }
})

test('normalization rejects empty output and strips unsafe fields', () => {
  assert.deepEqual(normalizeDriverResult('chatgpt-web', { text: '' }), manualFallback('web_surface_response_invalid'))
  const normalized = normalizeDriverResult('chatgpt-web', { text: 'safe\napi-key: hidden' })
  assert.equal(normalized.kind, 'AI_OPINION')
  assert.equal(normalized.text.includes('hidden'), false)
})

test('loopback client is local-only, session-memory, bounded, and no redirect', async () => {
  assert.equal(validateLoopbackBaseUrl('http://127.0.0.1:4312/api/v1').hostname, '127.0.0.1')
  for (const value of [
    'https://127.0.0.1:4312',
    'http://localhost:4312',
    'http://127.0.0.1:4312/?token=bad',
    'http://user:pass@127.0.0.1:4312',
    'http://127.0.0.1:4312/../escape',
  ]) {
    assert.throws(() => validateLoopbackBaseUrl(value), LoopbackClientError)
  }

  const requests = []
  const client = new LoopbackClient({
    baseUrl: 'http://127.0.0.1:4312/api/v1',
    token: 'session-token-value',
    fetchImpl: async (url, init) => {
      requests.push({ url, init })
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'content-type': 'application/json' },
      })
    },
  })
  const result = await client.request('/health')
  assert.deepEqual(result, { ok: true })
  assert.equal(requests[0].url, 'http://127.0.0.1:4312/api/v1/health')
  assert.equal(requests[0].init.headers['X-Loopback-Token'], 'session-token-value')
  assert.equal(requests[0].init.redirect, 'error')
  assert.equal(requests[0].init.credentials, 'omit')
  assert.equal(requests[0].url.includes('session-token-value'), false)
  await assert.rejects(client.request('/health', { method: 'PUT' }), (error) => error.code === 'loopback_path_rejected')
  await assert.rejects(
    client.request('/health', { method: 'POST', body: { value: 'x'.repeat(70000) } }),
    (error) => error.code === 'loopback_request_too_large',
  )
})

test('loopback response over limit fails closed before JSON parsing', async () => {
  const client = new LoopbackClient({
    baseUrl: 'http://127.0.0.1:4312',
    token: 'session-token-value',
    fetchImpl: async () => new Response('too-large', {
      status: 200,
      headers: { 'content-length': '262145' },
    }),
  })
  await assert.rejects(client.request('/health'), (error) => error.code === 'loopback_response_too_large')
})

test('executeInTab rejects missing scripting runtime without raw error', async () => {
  await assert.rejects(executeInTab({}, 1, () => true), (error) => error.code === 'browser_scripting_unavailable')
})
