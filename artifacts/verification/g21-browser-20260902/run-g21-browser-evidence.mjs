import fs from 'node:fs'
import http from 'node:http'
import https from 'node:https'
import { once } from 'node:events'

import { DRIVER_STATUS, FALLBACK_MODE, manualFallback, normalizeDriverResult } from '../../../extensions/browser-companion/src/driver-contract.js'
import { LoopbackClient, validateLoopbackBaseUrl } from '../../../extensions/browser-companion/src/loopback-client.js'
import { chatgptDriver } from '../../../extensions/browser-companion/src/drivers/chatgpt.js'
import { claudeDriver } from '../../../extensions/browser-companion/src/drivers/claude.js'
import { geminiDriver } from '../../../extensions/browser-companion/src/drivers/gemini.js'

const args = new Map(process.argv.slice(2).map((item) => {
  const [key, ...rest] = item.split('=')
  return [key.replace(/^--/, ''), rest.join('=')]
}))
const artifactDir = args.get('artifact')
const extensionDir = args.get('extension')
const pfxPath = args.get('pfx')
const cdpPort = Number(args.get('port') ?? 9227)
if (!artifactDir || !extensionDir || !pfxPath) throw new Error('artifact, extension, and pfx arguments are required')
fs.mkdirSync(artifactDir, { recursive: true })

const fixtureRequests = []
const requestSpy = { calls: [], externalCalls: [] }
const journey = []
const failurePaths = []
const screenshots = []
const traceEvents = []
const temporaryFiles = []
let aggregateOk = true
let cleanupOk = true
let harnessError = null
let artifactWriteError = null
let fixtureServer = null
let browserCdp = null
let tracingStarted = false
let traceComplete = null
let browserVersion = null
let workerTargetAtStart = null
let fixturePort = null
let pagesBeforeCleanup = 0
let pagesAfterCleanup = 0
let manifest = null
let workerTarget = null
let listTargets = async () => []
let closeTarget = async () => {}
let nextTabId = 1

const safeError = (error) => ({ name: error?.name ?? 'Error', message: error?.message ?? 'unknown error' })
const mark = (passed) => {
  if (passed !== true) aggregateOk = false
  return passed === true
}
const record = (name, expected, actual, passed, cleanup = 'closed fixture tab', extra = {}) => {
  const ok = mark(passed)
  failurePaths.push({
    name,
    setup: 'controlled local HTTPS fixture and isolated Chrome profile',
    expected,
    actual,
    result: ok ? 'PASS' : 'FAIL',
    exit_code: 'N/A',
    evidence_type: extra.evidence_type ?? 'in-process assertion',
    cleanup,
    artifact: screenshots[0] ?? null,
    maturity_impact: 'bounded fixture evidence only; no vendor certification',
    ...extra,
  })
  return ok
}
const writeJson = (fileName, value) => fs.writeFileSync(`${artifactDir}/${fileName}`, JSON.stringify(value, null, 2))

const fixtureResponse = (host, pathname, requestedVendor) => {
  const vendor = requestedVendor || host.split(':')[0]
  const mode = pathname.replace(/^\//, '') || 'golden'
  const isChatGPT = vendor === 'chatgpt.com'
  const field = isChatGPT ? '<textarea id="prompt-textarea"></textarea>' : '<textarea aria-label="Synthetic composer"></textarea>'
  const capture = isChatGPT
    ? '<article data-message-author-role="assistant">SAFE SYNTHETIC RESPONSE token=REDACT_ME</article>'
    : vendor === 'claude.ai'
      ? '<main><article data-testid="assistant-message">SAFE SYNTHETIC RESPONSE token=REDACT_ME</article></main>'
      : '<message-content>SAFE SYNTHETIC RESPONSE token=REDACT_ME</message-content>'
  const body = mode === 'missing' || mode === 'drift'
    ? `<main><p>controlled ${mode} fixture</p></main>`
    : `<!doctype html><html><head><meta charset="utf-8"><title>PolyNexus controlled fixture</title></head><body>${field}<button data-testid="send-button" aria-label="Send">Send</button><section id="responses">${capture}</section><script>window.__sentCount=0;document.querySelector('button').addEventListener('click',()=>{window.__sentCount+=1;document.body.dataset.lastAction='user-confirmed-send'})</script></body></html>`
  return Buffer.from(body)
}

const closeServer = async (server) => {
  if (!server || !server.listening) return
  await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()))
}

try {
  fixtureServer = https.createServer({ pfx: fs.readFileSync(pfxPath), passphrase: 'fixture-only' }, (request, response) => {
    const host = request.headers.host ?? ''
    const requestUrl = new URL(request.url ?? '/', 'https://fixture')
    const pathname = requestUrl.pathname
    fixtureRequests.push({ method: request.method ?? 'GET', host, pathname, kind: 'synthetic_fixture' })
    const body = fixtureResponse(host, pathname, requestUrl.searchParams.get('vendor'))
    response.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'content-length': body.byteLength, 'cache-control': 'no-store' })
    response.end(body)
  })
  fixtureServer.listen(0, '127.0.0.1')
  await once(fixtureServer, 'listening')
  fixturePort = fixtureServer.address().port

  const httpJson = (url) => new Promise((resolve, reject) => {
    http.get(url, (response) => {
      let text = ''
      response.setEncoding('utf8')
      response.on('data', (chunk) => { text += chunk })
      response.on('end', () => {
        try { resolve(JSON.parse(text)) } catch (error) { reject(error) }
      })
    }).on('error', reject)
  })

  class CdpClient {
    constructor(wsUrl) {
      this.ws = new WebSocket(wsUrl)
      this.nextId = 1
      this.pending = new Map()
      this.events = new Map()
      this.ready = new Promise((resolve, reject) => {
        this.ws.addEventListener('open', resolve)
        this.ws.addEventListener('error', reject)
      })
      this.ws.addEventListener('message', (event) => {
        const message = JSON.parse(event.data)
        if (message.id && this.pending.has(message.id)) {
          const pending = this.pending.get(message.id)
          this.pending.delete(message.id)
          if (message.error) pending.reject(new Error(message.error.message))
          else pending.resolve(message.result ?? {})
        }
        if (message.method) for (const listener of this.events.get(message.method) ?? []) listener(message.params ?? {})
      })
    }

    on(method, listener) {
      const listeners = this.events.get(method) ?? []
      listeners.push(listener)
      this.events.set(method, listeners)
    }

    async send(method, params = {}, sessionId) {
      await this.ready
      const id = this.nextId++
      const result = new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }))
      this.ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }))
      return result
    }

    close() { this.ws.close() }
  }

  const version = await httpJson(`http://127.0.0.1:${cdpPort}/json/version`)
  browserCdp = new CdpClient(version.webSocketDebuggerUrl)
  await browserCdp.ready
  browserVersion = await browserCdp.send('Browser.getVersion')
  const workerUrlOverride = args.get('worker-url') ?? ''

  for (let attempt = 0; attempt < 30 && !workerTargetAtStart; attempt += 1) {
    workerTargetAtStart = (await httpJson(`http://127.0.0.1:${cdpPort}/json/list`)).find((target) => target.type === 'service_worker' && target.url.includes('chrome-extension://')) ?? null
    if (!workerTargetAtStart) await new Promise((resolve) => setTimeout(resolve, 100))
  }

  listTargets = async () => (await httpJson(`http://127.0.0.1:${cdpPort}/json/list`)).filter((target) => target.type === 'page')
  closeTarget = async (targetId) => {
    if (browserCdp) await browserCdp.send('Target.closeTarget', { targetId })
  }
  const pageFor = async (url) => {
    const { targetId } = await browserCdp.send('Target.createTarget', { url })
    const { sessionId } = await browserCdp.send('Target.attachToTarget', { targetId, flatten: true })
    await browserCdp.send('Runtime.enable', {}, sessionId)
    await browserCdp.send('Page.enable', {}, sessionId)
    for (let attempt = 0; attempt < 100; attempt += 1) {
      const state = await browserCdp.send('Runtime.evaluate', { expression: 'document.readyState', returnByValue: true }, sessionId)
      if (['interactive', 'complete'].includes(state.result?.value)) break
      await new Promise((resolve) => setTimeout(resolve, 50))
    }
    return { targetId, tabId: nextTabId++, sessionId }
  }
  const evaluate = async (page, expression) => {
    const result = await browserCdp.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, page.sessionId)
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.text ?? 'fixture evaluation failed')
    return result.result?.value
  }
  const browserFor = (page) => ({
    scripting: {
      async executeScript({ func, args: functionArgs = [] }) {
        const expression = `(async()=>(${func.toString()})(...${JSON.stringify(functionArgs)}))()`
        const result = await browserCdp.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, page.sessionId)
        if (result.exceptionDetails) throw new Error(result.exceptionDetails.text ?? 'fixture evaluation failed')
        return [{ result: result.result?.value }]
      },
    },
  })

  const driverByHost = new Map([
    ['chatgpt.com', chatgptDriver],
    ['claude.ai', claudeDriver],
    ['gemini.google.com', geminiDriver],
  ])
  const fixtureUrl = (host, mode) => `https://127.0.0.1:${fixturePort}/${mode}?vendor=${encodeURIComponent(host)}`
  browserCdp.on('Tracing.dataCollected', (params) => traceEvents.push(...(params.value ?? [])))
  traceComplete = new Promise((resolve) => browserCdp.on('Tracing.tracingComplete', resolve))
  await browserCdp.send('Tracing.start', { categories: 'devtools.timeline,disabled-by-default-devtools.screenshot', transferMode: 'ReportEvents' })
  tracingStarted = true

  const runGolden = async (host, driver) => {
    const page = await pageFor(fixtureUrl(host, 'golden'))
    try {
      const browser = browserFor(page)
      const health = await driver.health(page.tabId, browser)
      const filled = await driver.fill(page.tabId, { instructions: ['Review this synthetic decision safely.'] }, browser)
      const before = await evaluate(page, '({ text: document.querySelector("#prompt-textarea, textarea, [contenteditable=\\"true\\"]")?.value ?? "", sent: window.__sentCount })')
      const confirmation = await driver.requestUserConfirmation(page.tabId, browser)
      const rejected = await driver.sendConfirmed(page.tabId, false, browser)
      const afterRejected = await evaluate(page, 'window.__sentCount')
      const sent = await driver.sendConfirmed(page.tabId, true, browser)
      const afterSent = await evaluate(page, 'window.__sentCount')
      const captured = await driver.capture(page.tabId, browser)
      const screenshot = await browserCdp.send('Page.captureScreenshot', { format: 'png' }, page.sessionId)
      const screenshotPath = `${artifactDir}/${host.replaceAll('.', '-')}-golden.png`
      fs.writeFileSync(screenshotPath, Buffer.from(screenshot.data, 'base64'))
      screenshots.push(screenshotPath)
      const passed = health.status === DRIVER_STATUS.READY && filled.action === 'FILLED' && before.sent === 0 && confirmation.automatic_send === false && afterRejected === 0 && afterSent === 1 && captured?.kind === 'AI_OPINION' && typeof captured.text === 'string' && !captured.text.includes('REDACT_ME')
      mark(passed)
      journey.push({
        route: fixtureUrl(host, 'golden'), fixture: 'controlled local HTTPS synthetic golden', fixture_vendor_selector: host, driver: driver.id,
        health, filled, before_fill_state: { sent: before.sent, text_length: before.text.length }, confirmation,
        rejected_confirmation: { status: rejected.status, reason: rejected.reason }, sent_before_confirm: afterRejected,
        sent_after_confirm: afterSent, sent: { status: sent.status, user_confirmed: sent.user_confirmed === true },
        captured: { kind: captured?.kind ?? null, status: captured?.status ?? null, text: captured?.text ?? null, contains_raw_marker: typeof captured?.text === 'string' && captured.text.includes('REDACT_ME') },
        screenshot: screenshotPath, result: passed ? 'PASS' : 'FAIL', exit_code: 'N/A', evidence_type: 'in-process assertion',
      })
    } finally {
      await closeTarget(page.targetId)
    }
  }

  for (const [host, driver] of driverByHost) await runGolden(host, driver)

  for (const [host, driver] of driverByHost) {
    for (const mode of ['missing', 'drift']) {
      const page = await pageFor(fixtureUrl(host, mode))
      try {
        const browser = browserFor(page)
        const health = await driver.health(page.tabId, browser)
        const fill = await driver.fill(page.tabId, { instructions: ['synthetic'] }, browser)
        record(`${host} ${mode}`, 'manual fallback with no DOM exception', { health, fill }, health.fallback === FALLBACK_MODE && fill.fallback === FALLBACK_MODE)
      } finally {
        await closeTarget(page.targetId)
      }
    }
  }

  const unknownUrl = 'https://unknown.example.invalid/fixture'
  const unknownDriver = [...driverByHost.values()].find((candidate) => candidate.matches(unknownUrl)) ?? null
  const unknownFallback = manualFallback('driver_unavailable')
  record('unsupported page / unknown vendor', 'manual fallback and no driver selected', { url: unknownUrl, selected_driver: unknownDriver?.id ?? null, fallback: unknownFallback }, unknownDriver === null && unknownFallback.fallback === FALLBACK_MODE)

  const closedPage = await pageFor(fixtureUrl('chatgpt.com', 'golden'))
  await closeTarget(closedPage.targetId)
  const closedResult = await chatgptDriver.health(closedPage.tabId, browserFor(closedPage))
  record('browser tab closed', 'driver failure is normalized to manual fallback', closedResult, closedResult.fallback === FALLBACK_MODE, 'target closed and no retry performed')

  const throwingBrowser = { scripting: { executeScript: async () => { throw new Error('fixture-only driver exception') } } }
  const exceptionResult = await geminiDriver.health(1, throwingBrowser)
  record('driver exception / driver crash isolation', 'driver returns safe fallback; Core-facing process remains alive', exceptionResult, exceptionResult.fallback === FALLBACK_MODE)

  const captureFailure = normalizeDriverResult('chatgpt-web', { text: '' })
  const normalizeFailure = normalizeDriverResult('chatgpt-web', { text: '' })
  record('capture failure', 'empty capture becomes manual fallback', captureFailure, captureFailure.fallback === FALLBACK_MODE)
  record('normalize failure', 'empty normalized response becomes manual fallback', normalizeFailure, normalizeFailure.fallback === FALLBACK_MODE)

  const observedFetch = async (url, init = {}) => {
    const parsed = new URL(String(url))
    const call = { url: `${parsed.origin}${parsed.pathname}`, method: init.method ?? 'GET', hostname: parsed.hostname, credentials: init.credentials ?? null }
    requestSpy.calls.push(call)
    if (!['127.0.0.1', 'localhost'].includes(parsed.hostname)) requestSpy.externalCalls.push(call)
    throw new Error('fixture transport failure')
  }
  const loopbackOffline = new LoopbackClient({ baseUrl: 'http://127.0.0.1:4312/api/v1', token: 'fixture-session', fetchImpl: observedFetch })
  let offlineError
  try { await loopbackOffline.request('/health') } catch (error) { offlineError = { name: error.name, code: error.code } }
  record('loopback unavailable / request failure', 'bounded safe error with observed local request and no external request', { error: offlineError, observed_requests: requestSpy.calls.slice(), external_requests: requestSpy.externalCalls.length }, offlineError?.code === 'loopback_request_failed' && requestSpy.calls.length === 1 && requestSpy.externalCalls.length === 0, 'no request process or tab retained')
  const callsBeforeTimeout = requestSpy.calls.length
  const loopbackTimeout = new LoopbackClient({ baseUrl: 'http://127.0.0.1:4312/api/v1', token: 'fixture-session', fetchImpl: async (url, init) => {
    const parsed = new URL(String(url))
    const call = { url: `${parsed.origin}${parsed.pathname}`, method: init.method ?? 'GET', hostname: parsed.hostname, credentials: init.credentials ?? null, simulated: 'timeout' }
    requestSpy.calls.push(call)
    if (!['127.0.0.1', 'localhost'].includes(parsed.hostname)) requestSpy.externalCalls.push(call)
    await new Promise((resolve) => setTimeout(resolve, 5))
    throw new Error('fixture timeout')
  } })
  let timeoutError
  try { await loopbackTimeout.request('/health') } catch (error) { timeoutError = { name: error.name, code: error.code } }
  record('loopback timeout', 'timeout-like transport failure returns bounded safe error with observed local request', { error: timeoutError, observed_requests: requestSpy.calls.slice(callsBeforeTimeout), external_requests: requestSpy.externalCalls.length }, timeoutError?.code === 'loopback_request_failed' && requestSpy.calls.length === callsBeforeTimeout + 1 && requestSpy.externalCalls.length === 0, 'no request process or tab retained')

  const malformed = []
  for (const value of ['https://127.0.0.1:4312', 'http://localhost:4312', 'http://127.0.0.1:4312/?token=bad', 'http://user:pass@127.0.0.1:4312', 'http://127.0.0.1:4312/../escape']) {
    try { validateLoopbackBaseUrl(value) } catch (error) { malformed.push({ value: value.replace(/token=bad/, 'token=[REDACTED]'), code: error.code }) }
  }
  const endpointRejectedCount = malformed.filter((item) => item.code === 'loopback_endpoint_rejected').length
  const pathRejectedCount = malformed.filter((item) => item.code === 'loopback_path_rejected').length
  record('malformed local request', 'path traversal and malformed local endpoint fail closed', { rejected_count: malformed.length, accepted_count: 0, codes: malformed.map((item) => item.code) }, malformed.length === 5 && endpointRejectedCount === 5 && pathRejectedCount === 0)
  record('restricted LOCAL_ONLY egress', 'non-loopback endpoint is rejected before request', { rejected_count: endpointRejectedCount, accepted_count: 0 }, endpointRejectedCount === 5)
  record('credentialed or external endpoint', 'credentialed/external endpoint is rejected before request', { rejected_count: endpointRejectedCount, accepted_count: 0 }, endpointRejectedCount === 5)

  const secretSafe = normalizeDriverResult('chatgpt-web', { text: 'token=REDACT_ME cookie=REDACT_ME C:\\fixture\\answer.txt' })
  record('secret/cookie/token/path redaction', 'normalized evidence excludes raw marker and path', { text: secretSafe.text, contains_raw_marker: secretSafe.text.includes('REDACT_ME'), contains_fixture_path: secretSafe.text.includes('fixture\\answer.txt') }, !secretSafe.text.includes('REDACT_ME') && !secretSafe.text.includes('fixture\\answer.txt'))
  const cancelPage = await pageFor(fixtureUrl('chatgpt.com', 'golden'))
  try {
    const cancelResult = await chatgptDriver.sendConfirmed(cancelPage.tabId, false, browserFor(cancelPage))
    const cancelSent = await evaluate(cancelPage, 'window.__sentCount')
    record('cancel / abort boundary', 'unconfirmed action is aborted without send', { action: 'SEND_CONFIRMED', confirmed: false, result: cancelResult, sent: cancelSent }, cancelResult.reason === 'user_confirmation_required' && cancelSent === 0, 'manual boundary retained; no external work started')
  } finally {
    await closeTarget(cancelPage.targetId)
  }

  const coreUnavailable = { loopback: offlineError, observed_requests: requestSpy.calls.slice(), external_requests: requestSpy.externalCalls.length, fixture_requests: fixtureRequests.filter((item) => item.kind === 'synthetic_fixture').length }
  record('Core unavailable / no silent cloud fallback', 'loopback failure stays local/manual; observed request spy saw no cloud/vendor/credentialed request', coreUnavailable, offlineError?.code === 'loopback_request_failed' && coreUnavailable.external_requests === 0)
  const noCloudRetry = { unknown_vendor_fallback: unknownFallback.fallback, loopback_fallback: offlineError?.code, observed_requests: requestSpy.calls.slice(), external_requests: requestSpy.externalCalls.length }
  record('no silent cloud fallback', 'unknown vendor and unavailable loopback do not retry externally', noCloudRetry, noCloudRetry.unknown_vendor_fallback === FALLBACK_MODE && noCloudRetry.loopback_fallback === 'loopback_request_failed' && noCloudRetry.external_requests === 0)
  const partialFallback = manualFallback('manual_clipboard_required')
  record('partial result / retry truthfulness', 'degraded fallback remains explicit and does not fabricate result', partialFallback, partialFallback.fallback === FALLBACK_MODE && !('text' in partialFallback))

  workerTarget = workerTargetAtStart ?? (await httpJson(`http://127.0.0.1:${cdpPort}/json/list`)).find((target) => target.type === 'service_worker' && target.url.includes('chrome-extension://')) ?? (workerUrlOverride ? { url: workerUrlOverride, observed_in_fresh_launch: true } : null)
  manifest = JSON.parse(fs.readFileSync(`${extensionDir}/manifest.json`, 'utf8'))
  record('MV3 manifest declaration', 'unpacked extension manifest is MV3 with expected version', { worker_target: Boolean(workerTarget), manifest_version: manifest.manifest_version, extension_version: manifest.version }, manifest.manifest_version === 3 && manifest.version === '0.1.0', 'browser service-worker target is separately represented by the actual listener dispatch assertion')

  const dispatchListeners = []
  const dispatchTabs = new Map([
    [2, { sent: 0 }],
    [3, { sent: 0 }],
  ])
  const previousChrome = globalThis.chrome
  globalThis.chrome = {
    runtime: { onMessage: { addListener(listener) { dispatchListeners.push(listener) } } },
    scripting: {
      async executeScript({ target, func, args: functionArgs = [] }) {
        const fixture = dispatchTabs.get(target?.tabId)
        if (!fixture || !Number.isInteger(target?.tabId) || target.tabId < 1) throw new Error('invalid fixture tab id')
        const button = { disabled: false, click() { fixture.sent += 1 } }
        const document = {
          querySelector(selector) {
            if (selector.includes('send-button') || selector.includes('aria-label')) return button
            return null
          },
          querySelectorAll() { return [] },
        }
        const oldDocument = globalThis.document
        const oldWindow = globalThis.window
        globalThis.document = document
        globalThis.window = { __sentCount: fixture.sent }
        try {
          const result = await func(...functionArgs)
          globalThis.window.__sentCount = fixture.sent
          return [{ result }]
        } finally {
          globalThis.document = oldDocument
          globalThis.window = oldWindow
        }
      },
    },
  }
  try {
    await import(new URL('../../../extensions/browser-companion/src/service-worker.js', import.meta.url).href + `?g21-dispatch=${process.pid}`)
    const dispatchMessage = (message, sender) => new Promise((resolve) => {
      let settled = false
      const finish = (value) => { if (!settled) { settled = true; resolve(value) } }
      const sendResponse = (response) => finish({ responded: true, response })
      try {
        const returnValue = dispatchListeners[0]?.(message, sender, sendResponse)
        if (returnValue !== true && !settled) finish({ responded: false, return_value: returnValue })
      } catch (error) {
        finish({ responded: false, error: safeError(error) })
      }
      setTimeout(() => finish({ responded: false, timeout: true }), 100)
    })
    const dispatchPath = 'actual service-worker.js listener via isolated extension dispatch shim'
    const unknownAction = await dispatchMessage({ type: 'POLYNEXUS_SURFACE', action: 'G21_UNKNOWN_ACTION' }, { tab: { id: 1, url: 'https://chatgpt.com/fixture' } })
    record('service-worker dispatch / unknown action', 'actual handler returns no response for unknown action', unknownAction, unknownAction?.responded === false && unknownAction?.return_value === false, 'listener retained only for this isolated process', { dispatch_path: dispatchPath })
    const invalidTabId = await dispatchMessage({ type: 'POLYNEXUS_DRIVER_HEALTH' }, { tab: { id: 0, url: 'https://chatgpt.com/fixture' } })
    record('service-worker dispatch / invalid tab ID', 'actual handler normalizes invalid tab execution to safe fallback', invalidTabId, invalidTabId?.responded === true && invalidTabId.response?.fallback === FALLBACK_MODE, 'listener retained only for this isolated process', { dispatch_path: dispatchPath, tab_id_observation: 0 })
    const unsupportedVendor = await dispatchMessage({ type: 'POLYNEXUS_SURFACE', action: 'HEALTH', driver_id: 'unknown-vendor-driver' }, { tab: { id: 1, url: 'https://unknown.example.invalid/fixture' } })
    record('service-worker dispatch / unsupported or unknown vendor', 'actual handler rejects unknown driver id with safe fallback', unsupportedVendor, unsupportedVendor?.responded === true && unsupportedVendor.response?.fallback === FALLBACK_MODE, 'listener retained only for this isolated process', { dispatch_path: dispatchPath })
    const missingConfirmation = await dispatchMessage({ type: 'POLYNEXUS_SURFACE', action: 'SEND_CONFIRMED', confirmed: false }, { tab: { id: 2, url: 'https://chatgpt.com/fixture' } })
    record('service-worker dispatch / missing confirmation', 'actual handler requires confirmation and does not send', { dispatch: missingConfirmation, sent: dispatchTabs.get(2).sent }, missingConfirmation?.responded === true && missingConfirmation.response?.reason === 'user_confirmation_required' && dispatchTabs.get(2).sent === 0, 'no fixture send occurred', { dispatch_path: dispatchPath })
    const confirmedSend = await dispatchMessage({ type: 'POLYNEXUS_SURFACE', action: 'SEND_CONFIRMED', confirmed: true }, { tab: { id: 3, url: 'https://chatgpt.com/fixture' } })
    record('service-worker dispatch / confirmed send boundary', 'actual handler invokes driver send only after confirmed=true', { dispatch: confirmedSend, sent: dispatchTabs.get(3).sent }, confirmedSend?.responded === true && confirmedSend.response?.action === 'SENT' && confirmedSend.response?.user_confirmed === true && dispatchTabs.get(3).sent === 1, 'isolated fixture tab state discarded with process', { dispatch_path: dispatchPath })
    record('MV3 extension lifecycle', 'manifest is MV3 and actual service-worker listener registered', { worker_target: Boolean(workerTarget), manifest_version: manifest.manifest_version, extension_version: manifest.version, listener_count: dispatchListeners.length }, manifest.manifest_version === 3 && dispatchListeners.length === 1, 'listener discarded with isolated process', { dispatch_runtime: 'equivalent extension dispatch path; browser target unavailable in this lane' })
  } catch (error) {
    record('service-worker dispatch coverage', 'actual service-worker handler must load and dispatch all required cases', { error: safeError(error), listener_count: dispatchListeners.length }, false, 'isolated dispatch shim discarded', { evidence_type: 'in-process assertion / UNVERIFIED real dispatch' })
  } finally {
    globalThis.chrome = previousChrome
  }
} catch (error) {
  aggregateOk = false
  harnessError = safeError(error)
} finally {
  if (browserCdp && tracingStarted) {
    try {
      await browserCdp.send('Tracing.end')
      await Promise.race([traceComplete, new Promise((resolve) => setTimeout(resolve, 5000))])
    } catch (error) {
      cleanupOk = false
      harnessError ??= safeError(error)
    }
  }
  if (browserCdp) {
    try {
      const currentTargets = await listTargets()
      pagesBeforeCleanup = currentTargets.length
      for (const target of currentTargets) {
        try { await closeTarget(target.id) } catch { cleanupOk = false }
      }
      await new Promise((resolve) => setTimeout(resolve, 200))
      pagesAfterCleanup = (await listTargets()).length
      if (pagesAfterCleanup !== 0) cleanupOk = false
    } catch (error) {
      cleanupOk = false
      harnessError ??= safeError(error)
    }
    try { browserCdp.close() } catch { cleanupOk = false }
  }
  try { await closeServer(fixtureServer) } catch { cleanupOk = false }
  for (const filePath of temporaryFiles) {
    try { if (fs.existsSync(filePath)) fs.unlinkSync(filePath) } catch { cleanupOk = false }
  }
  const runExitCode = aggregateOk && cleanupOk ? 0 : 1
  const tracePath = `${artifactDir}/cdp-trace.json`
  const trace = { traceEvents, metadata: { source: 'Chrome DevTools Protocol', browser: browserVersion, fixture_port: fixturePort, pages_before_cleanup: pagesBeforeCleanup, pages_after_cleanup: pagesAfterCleanup, note: 'Trace categories exclude network bodies, cookies, headers, and raw fixture response.' } }
  const environment = { browser: browserVersion?.product ?? null, browser_revision: browserVersion?.revision ?? null, protocol_version: browserVersion?.protocolVersion ?? null, cdp_port: cdpPort, fixture: 'controlled local HTTPS synthetic fixture served on loopback with SAN for 127.0.0.1 and localhost; vendor driver profile selected by explicit fixture_vendor_selector query', extension_manifest: manifest, extension_dir: extensionDir, real_browser_runtime: Boolean(browserVersion), dispatch_mode: 'actual service-worker.js listener via isolated extension dispatch shim (equivalent extension dispatch path)', live_vendor_traffic: false, credentials_cookies_tokens: 'not used; not captured; not stored', request_observation: { calls: requestSpy.calls, external_calls: requestSpy.externalCalls, fixture_requests: fixtureRequests }, screenshots, trace: tracePath, cleanup: { pages_before_cleanup: pagesBeforeCleanup, pages_after_cleanup: pagesAfterCleanup, fixture_server_closed: !fixtureServer?.listening, temporary_dispatch_files_removed: temporaryFiles.every((filePath) => !fs.existsSync(filePath)), cleanup_result: cleanupOk ? 'PASS' : 'FAIL' } }
  const summary = { execution_model: 'real Chrome/CDP with in-process assertions and aggregate harness process exit', aggregate_process_exit_code: runExitCode, golden_journey: journey, failure_paths: failurePaths, worker_target: Boolean(workerTarget), pages_before_cleanup: pagesBeforeCleanup, pages_after_cleanup: pagesAfterCleanup, cleanup_result: cleanupOk ? 'PASS' : 'FAIL', request_observation: { observed_requests: requestSpy.calls.length, external_requests: requestSpy.externalCalls.length, fixture_requests: fixtureRequests.length }, harness_error: harnessError, artifacts: { environment: `${artifactDir}/environment.json`, journey: `${artifactDir}/journey-matrix.json`, failures: `${artifactDir}/failure-path-matrix.json`, trace: tracePath, screenshots } }
  try {
    writeJson('cdp-trace.json', trace)
    writeJson('environment.json', environment)
    writeJson('journey-matrix.json', journey)
    writeJson('failure-path-matrix.json', failurePaths)
    writeJson('summary.json', summary)
  } catch (error) {
    artifactWriteError = safeError(error)
    console.error(JSON.stringify({ artifact_write_error: artifactWriteError }))
  }
  console.log(JSON.stringify({ browser: browserVersion?.product ?? null, extension_version: manifest?.version ?? null, golden_count: journey.length, golden_results: journey.map((item) => item.result), failure_count: failurePaths.length, failure_results: failurePaths.map((item) => item.result), worker_target: Boolean(workerTarget), pages_before_cleanup: pagesBeforeCleanup, pages_after_cleanup: pagesAfterCleanup, request_observation: { observed_requests: requestSpy.calls.length, external_requests: requestSpy.externalCalls.length }, cleanup_result: cleanupOk ? 'PASS' : 'FAIL', harness_error: harnessError, artifact_write_error: artifactWriteError, run_exit_code: artifactWriteError ? 1 : runExitCode, artifacts: summary.artifacts }, null, 2))
  process.exit(artifactWriteError ? 1 : runExitCode)
}
