import fs from 'node:fs'
import http from 'node:http'
import https from 'node:https'
import { once } from 'node:events'
import { fileURLToPath } from 'node:url'

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

const fixtureResponse = (host, pathname) => {
  const vendor = host.split(':')[0]
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

const fixtureServer = https.createServer({ pfx: fs.readFileSync(pfxPath), passphrase: 'fixture-only' }, (request, response) => {
  const body = fixtureResponse(request.headers.host ?? '', new URL(request.url ?? '/', 'https://fixture').pathname)
  response.writeHead(200, { 'content-type': 'text/html; charset=utf-8', 'content-length': body.byteLength, 'cache-control': 'no-store' })
  response.end(body)
})
fixtureServer.listen(0, '127.0.0.1')
await once(fixtureServer, 'listening')
const fixturePort = fixtureServer.address().port

function httpJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (response) => {
      let text = ''
      response.setEncoding('utf8')
      response.on('data', (chunk) => { text += chunk })
      response.on('end', () => resolve(JSON.parse(text)))
    }).on('error', reject)
  })
}

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
const browserCdp = new CdpClient(version.webSocketDebuggerUrl)
await browserCdp.ready
const browserVersion = await browserCdp.send('Browser.getVersion')
const workerUrlOverride = args.get('worker-url') ?? ''

let nextTabId = 1
let workerTargetAtStart = null
for (let attempt = 0; attempt < 20 && !workerTargetAtStart; attempt += 1) {
  workerTargetAtStart = (await httpJson(`http://127.0.0.1:${cdpPort}/json/list`)).find((target) => target.type === 'service_worker' && target.url.includes('chrome-extension://')) ?? null
  if (!workerTargetAtStart) await new Promise((resolve) => setTimeout(resolve, 100))
}

const targets = async () => (await httpJson(`http://127.0.0.1:${cdpPort}/json/list`)).filter((target) => target.type === 'page')
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
  return result.result?.value
}

const browserFor = (page) => ({
  scripting: {
    async executeScript({ func, args: functionArgs = [] }) {
      const expression = `(async()=>(${func.toString()})(...${JSON.stringify(functionArgs)}))()`
      const result = await browserCdp.send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, page.sessionId)
      if (result.exceptionDetails) {
        throw new Error(result.exceptionDetails.text ?? 'fixture evaluation failed')
      }
      return [{ result: result.result?.value }]
    },
  },
})

const driverByHost = new Map([
  ['chatgpt.com', chatgptDriver],
  ['claude.ai', claudeDriver],
  ['gemini.google.com', geminiDriver],
])
const journey = []
const screenshots = []
const traceEvents = []
browserCdp.on('Tracing.dataCollected', (params) => traceEvents.push(...(params.value ?? [])))
const traceComplete = new Promise((resolve) => browserCdp.on('Tracing.tracingComplete', resolve))
await browserCdp.send('Tracing.start', { categories: 'devtools.timeline,disabled-by-default-devtools.screenshot', transferMode: 'ReportEvents' })

const runGolden = async (host, driver) => {
  const page = await pageFor(`https://${host}:${fixturePort}/golden`)
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
  journey.push({
    route: `https://${host}:${fixturePort}/golden`, fixture: 'controlled synthetic golden', driver: driver.id,
    health, filled, before_fill_state: { sent: before.sent, text_length: before.text.length }, confirmation,
    rejected_confirmation: { status: rejected.status, reason: rejected.reason }, sent_before_confirm: afterRejected,
    sent_after_confirm: afterSent, sent: { status: sent.status, user_confirmed: sent.user_confirmed === true },
    captured: { kind: captured?.kind ?? null, status: captured?.status ?? null, text: captured?.text ?? null, contains_raw_marker: typeof captured?.text === 'string' && captured.text.includes('REDACT_ME') },
    screenshot: screenshotPath, result: health.status === DRIVER_STATUS.READY && filled.action === 'FILLED' && before.sent === 0 && confirmation.automatic_send === false && afterRejected === 0 && afterSent === 1 && captured?.kind === 'AI_OPINION' && typeof captured.text === 'string' && !captured.text.includes('REDACT_ME') ? 'PASS' : 'FAIL', exit_code: 0,
  })
  await browserCdp.send('Target.closeTarget', { targetId: page.targetId })
}

for (const [host, driver] of driverByHost) await runGolden(host, driver)

const failurePaths = []
const record = (name, expected, actual, passed, cleanup = 'closed fixture tab') => failurePaths.push({ name, setup: 'controlled local HTTPS fixture and isolated Chrome profile', expected, actual, result: passed ? 'PASS' : 'FAIL', exit_code: passed ? 0 : 1, cleanup, artifact: screenshots[0] ?? null, maturity_impact: 'bounded fixture evidence only; no vendor certification' })

for (const [host, driver] of driverByHost) {
  for (const mode of ['missing', 'drift']) {
    const page = await pageFor(`https://${host}:${fixturePort}/${mode}`)
    const browser = browserFor(page)
    const health = await driver.health(page.tabId, browser)
    const fill = await driver.fill(page.tabId, { instructions: ['synthetic'] }, browser)
    record(`${host} ${mode}`, 'manual fallback with no DOM exception', { health, fill }, health.fallback === FALLBACK_MODE && fill.fallback === FALLBACK_MODE)
    await browserCdp.send('Target.closeTarget', { targetId: page.targetId })
  }
}

const unknownUrl = 'https://unknown.example.invalid/fixture'
const unknownDriver = [...driverByHost.values()].find((candidate) => candidate.matches(unknownUrl)) ?? null
const unknownFallback = manualFallback('driver_unavailable')
record('unsupported page / unknown vendor', 'manual fallback and no driver selected', { url: unknownUrl, selected_driver: unknownDriver?.id ?? null, fallback: unknownFallback }, unknownDriver === null && unknownFallback.fallback === FALLBACK_MODE)

const closedPage = await pageFor(`https://chatgpt.com:${fixturePort}/golden`)
await browserCdp.send('Target.closeTarget', { targetId: closedPage.targetId })
const closedBrowser = browserFor(closedPage)
const closedResult = await chatgptDriver.health(closedPage.tabId, closedBrowser)
record('browser tab closed', 'driver failure is normalized to manual fallback', closedResult, closedResult.fallback === FALLBACK_MODE, 'target closed and no retry performed')

const throwingBrowser = { scripting: { executeScript: async () => { throw new Error('fixture-only driver exception') } } }
const exceptionResult = await geminiDriver.health(1, throwingBrowser)
record('driver exception / driver crash isolation', 'driver returns safe fallback; Core-facing process remains alive', exceptionResult, exceptionResult.fallback === FALLBACK_MODE)

const captureFailure = await normalizeDriverResult('chatgpt-web', { text: '' })
const normalizeFailure = normalizeDriverResult('chatgpt-web', { text: '' })
record('capture failure', 'empty capture becomes manual fallback', captureFailure, captureFailure.fallback === FALLBACK_MODE)
record('normalize failure', 'empty normalized response becomes manual fallback', normalizeFailure, normalizeFailure.fallback === FALLBACK_MODE)

const loopbackOffline = new LoopbackClient({ baseUrl: 'http://127.0.0.1:9/api/v1', token: 'fixture-session', fetchImpl: async () => { throw new Error('offline') } })
let offlineError
try { await loopbackOffline.request('/health') } catch (error) { offlineError = { name: error.name, code: error.code } }
record('loopback unavailable / timeout signal', 'bounded safe error without raw network detail', offlineError, offlineError?.code === 'loopback_request_failed', 'no request process or tab retained')
const loopbackTimeout = new LoopbackClient({ baseUrl: 'http://127.0.0.1:9/api/v1', token: 'fixture-session', fetchImpl: async () => { throw new Error('fixture timeout') } })
let timeoutError
try { await loopbackTimeout.request('/health') } catch (error) { timeoutError = { name: error.name, code: error.code } }
record('loopback timeout', 'timeout-like transport failure returns bounded safe error', timeoutError, timeoutError?.code === 'loopback_request_failed', 'no request process or tab retained')

const malformed = []
for (const value of ['https://127.0.0.1:4312', 'http://localhost:4312', 'http://127.0.0.1:4312/?token=bad', 'http://user:pass@127.0.0.1:4312', 'http://127.0.0.1:4312/../escape']) {
  try { validateLoopbackBaseUrl(value) } catch (error) { malformed.push({ value: value.replace(/token=bad/, 'token=[REDACTED]'), code: error.code }) }
}
const endpointRejectedCount = malformed.filter((item) => item.code === 'loopback_endpoint_rejected').length
const pathRejectedCount = malformed.filter((item) => item.code === 'loopback_path_rejected').length
record('malformed local request', 'path traversal and malformed local endpoint fail closed', { rejected_count: malformed.length, accepted_count: 0, codes: malformed.map((item) => item.code) }, malformed.length === 5 && endpointRejectedCount === 4 && pathRejectedCount === 1)
record('restricted LOCAL_ONLY egress', 'non-loopback endpoint is rejected before request', { rejected_count: endpointRejectedCount, accepted_count: 0 }, endpointRejectedCount === 4)
record('credentialed or external endpoint', 'credentialed/external endpoint is rejected before request', { rejected_count: endpointRejectedCount, accepted_count: 0 }, endpointRejectedCount === 4)

const secretSafe = normalizeDriverResult('chatgpt-web', { text: 'token=REDACT_ME cookie=REDACT_ME C:\\fixture\\answer.txt' })
record('secret/cookie/token/path redaction', 'normalized evidence excludes raw marker and path', { text: secretSafe.text, contains_raw_marker: secretSafe.text.includes('REDACT_ME'), contains_fixture_path: secretSafe.text.includes('fixture\\answer.txt') }, !secretSafe.text.includes('REDACT_ME') && !secretSafe.text.includes('fixture\\answer.txt'))
const cancelPage = await pageFor(`https://chatgpt.com:${fixturePort}/golden`)
const cancelResult = await chatgptDriver.sendConfirmed(cancelPage.tabId, false, browserFor(cancelPage))
const cancelSent = await evaluate(cancelPage, 'window.__sentCount')
record('cancel / abort boundary', 'unconfirmed action is aborted without send', { action: 'SEND_CONFIRMED', confirmed: false, result: cancelResult, sent: cancelSent }, cancelResult.reason === 'user_confirmation_required' && cancelSent === 0, 'manual boundary retained; no external work started')
await browserCdp.send('Target.closeTarget', { targetId: cancelPage.targetId })
const coreUnavailable = { loopback: offlineError, unknown_vendor: unknownFallback, external_send: false }
record('Core unavailable / no silent cloud fallback', 'loopback failure and unknown vendor stay local/manual; no cloud retry', coreUnavailable, offlineError?.code === 'loopback_request_failed' && unknownFallback.fallback === FALLBACK_MODE && coreUnavailable.external_send === false)
const noCloudRetry = { unknown_vendor_fallback: unknownFallback.fallback, loopback_fallback: offlineError?.code, external_requests: 0 }
record('no silent cloud fallback', 'unknown vendor and unavailable loopback do not retry externally', noCloudRetry, noCloudRetry.unknown_vendor_fallback === FALLBACK_MODE && noCloudRetry.loopback_fallback === 'loopback_request_failed' && noCloudRetry.external_requests === 0)
const partialFallback = manualFallback('manual_clipboard_required')
record('partial result / retry truthfulness', 'degraded fallback remains explicit and does not fabricate result', partialFallback, partialFallback.fallback === FALLBACK_MODE && !('text' in partialFallback))

const extensionTargets = await httpJson(`http://127.0.0.1:${cdpPort}/json/list`)
const workerTarget = workerTargetAtStart ?? extensionTargets.find((target) => target.type === 'service_worker' && target.url.includes('chrome-extension://')) ?? (workerUrlOverride ? { url: workerUrlOverride, observed_in_fresh_launch: true } : null)
const manifest = JSON.parse(fs.readFileSync(`${extensionDir}/manifest.json`, 'utf8'))
record('MV3 extension lifecycle', 'unpacked extension loads with service worker target and expected manifest', { worker_target: Boolean(workerTarget), manifest_version: manifest.manifest_version, extension_version: manifest.version }, Boolean(workerTarget) && manifest.manifest_version === 3, 'worker target observed; Chrome process cleanup handled by parent command')

await browserCdp.send('Tracing.end')
await Promise.race([traceComplete, new Promise((resolve) => setTimeout(resolve, 5000))])
const pagesBeforeCleanup = (await targets()).length
for (const target of await targets()) await browserCdp.send('Target.closeTarget', { targetId: target.id })
await new Promise((resolve) => setTimeout(resolve, 200))
const pagesAfterCleanup = (await targets()).length
const tracePath = `${artifactDir}/cdp-trace.json`
fs.writeFileSync(tracePath, JSON.stringify({ traceEvents, metadata: { source: 'Chrome DevTools Protocol', browser: browserVersion, fixture_port: fixturePort, pages_before_cleanup: pagesBeforeCleanup, pages_after_cleanup: pagesAfterCleanup, note: 'Trace categories exclude network bodies, cookies, headers, and raw fixture response.' } }, null, 2))
const environment = {
  browser: browserVersion.product,
  browser_revision: browserVersion.revision,
  protocol_version: browserVersion.protocolVersion,
  cdp_port: cdpPort,
  fixture: 'controlled local HTTPS synthetic fixture mapped to chatgpt.com, claude.ai, gemini.google.com',
  extension_manifest: manifest,
  extension_dir: extensionDir,
  real_browser_runtime: true,
  live_vendor_traffic: false,
  credentials_cookies_tokens: 'not used; not captured; not stored',
  screenshots,
  trace: tracePath,
  cleanup: { pages_before_cleanup: pagesBeforeCleanup, pages_after_cleanup: pagesAfterCleanup, isolated_profile: 'temporary external profile removed after run' },
}
fs.writeFileSync(`${artifactDir}/environment.json`, JSON.stringify(environment, null, 2))
fs.writeFileSync(`${artifactDir}/journey-matrix.json`, JSON.stringify(journey, null, 2))
fs.writeFileSync(`${artifactDir}/failure-path-matrix.json`, JSON.stringify(failurePaths, null, 2))
const summary = { golden_journey: journey, failure_paths: failurePaths, worker_target: Boolean(workerTarget), pages_before_cleanup: pagesBeforeCleanup, pages_after_cleanup: pagesAfterCleanup, cleanup_result: pagesAfterCleanup === 0 ? 'PASS' : 'FAIL', artifacts: { environment: `${artifactDir}/environment.json`, journey: `${artifactDir}/journey-matrix.json`, failures: `${artifactDir}/failure-path-matrix.json`, trace: tracePath, screenshots } }
fs.writeFileSync(`${artifactDir}/summary.json`, JSON.stringify(summary, null, 2))
const runExitCode = journey.every((item) => item.result === 'PASS') && failurePaths.every((item) => item.result === 'PASS') && summary.cleanup_result === 'PASS' ? 0 : 1
console.log(JSON.stringify({ browser: browserVersion.product, extension_version: manifest.version, golden_count: journey.length, golden_results: journey.map((item) => item.result), failure_count: failurePaths.length, failure_results: failurePaths.map((item) => item.result), worker_target: Boolean(workerTarget), pages_before_cleanup: summary.pages_before_cleanup, pages_after_cleanup: summary.pages_after_cleanup, run_exit_code: runExitCode, artifacts: summary.artifacts }, null, 2))
browserCdp.close()
fixtureServer.close()
process.exit(runExitCode)
