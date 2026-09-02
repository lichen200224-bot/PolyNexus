import { chatgptDriver } from './drivers/chatgpt.js'
import { claudeDriver } from './drivers/claude.js'
import { geminiDriver } from './drivers/gemini.js'
import {
  DRIVER_STATUS,
  SURFACE_ACTION,
  manualFallback,
  normalizeDriverResult,
} from './driver-contract.js'
import { LoopbackClient } from './loopback-client.js'

const drivers = [chatgptDriver, claudeDriver, geminiDriver]
let sessionLoopbackClient = null
const LOOPBACK_SESSION_TYPE = 'POLYNEXUS_LOOPBACK_SESSION'
const LOOPBACK_REQUEST_TYPE = 'POLYNEXUS_LOOPBACK_REQUEST'
const LOOPBACK_REQUEST_PATHS = new Set([
  '/health',
  '/ready',
  '/capabilities',
  '/api/v1/health',
  '/api/v1/ready',
  '/api/v1/capabilities',
])

function isExtensionSender(sender, browser = globalThis.chrome) {
  return typeof browser?.runtime?.id === 'string' && sender?.id === browser.runtime.id
}

function findDriver(message, sender) {
  const requestedId = typeof message?.driver_id === 'string' ? message.driver_id : ''
  const requested = requestedId ? drivers.find((driver) => driver.id === requestedId) : null
  if (requestedId && !requested) return null
  const driver = requested ?? drivers.find((candidate) => candidate.matches(sender.tab?.url ?? ''))
  if (!driver) return null
  if (message.action !== SURFACE_ACTION.LAUNCH && sender.tab?.url && !driver.matches(sender.tab.url)) return null
  return driver
}

async function importClipboard(driver, message) {
  try {
    const text = typeof message?.text === 'string'
      ? message.text
      : typeof globalThis.navigator?.clipboard?.readText === 'function'
        ? await globalThis.navigator.clipboard.readText()
        : ''
    return normalizeDriverResult(driver?.id, { text })
  } catch {
    return manualFallback('manual_clipboard_required')
  }
}

function configureLoopbackSession(message) {
  try {
    sessionLoopbackClient = new LoopbackClient({
      baseUrl: message.base_url,
      token: message.token,
    })
    return { status: DRIVER_STATUS.READY, auth: 'SESSION_MEMORY_ONLY' }
  } catch {
    sessionLoopbackClient = null
    return manualFallback('driver_unavailable')
  }
}

function clearLoopbackSession() {
  sessionLoopbackClient = null
  return { status: DRIVER_STATUS.READY, auth: 'SESSION_CLEARED' }
}

export async function handleLoopbackRequest(message) {
  if (!sessionLoopbackClient || !LOOPBACK_REQUEST_PATHS.has(message?.path)) {
    return { status: DRIVER_STATUS.DEGRADED, reason: 'loopback_request_failed' }
  }
  const method = message.method === undefined ? 'GET' : message.method
  if (!['GET', 'POST'].includes(method)) {
    return { status: DRIVER_STATUS.DEGRADED, reason: 'loopback_request_failed' }
  }
  try {
    return await sessionLoopbackClient.request(message.path, {
      method,
      body: method === 'POST' ? message.body : undefined,
    })
  } catch {
    return { status: DRIVER_STATUS.DEGRADED, reason: 'loopback_request_failed' }
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === LOOPBACK_SESSION_TYPE) {
    if (!isExtensionSender(sender)) {
      sendResponse({ status: DRIVER_STATUS.DEGRADED, reason: 'driver_unavailable' })
      return false
    }
    sendResponse(message.action === 'CLEAR' ? clearLoopbackSession() : configureLoopbackSession(message))
    return false
  }

  if (message?.type === LOOPBACK_REQUEST_TYPE) {
    if (!isExtensionSender(sender)) {
      sendResponse({ status: DRIVER_STATUS.DEGRADED, reason: 'loopback_request_failed' })
      return false
    }
    handleLoopbackRequest(message).then(sendResponse)
    return true
  }

  const action = message?.type === 'POLYNEXUS_DRIVER_HEALTH'
    ? SURFACE_ACTION.HEALTH
    : message?.type === 'POLYNEXUS_SURFACE'
      ? message.action
      : null
  if (!Object.values(SURFACE_ACTION).includes(action)) return false

  const driver = findDriver(message, sender)
  if (!driver) {
    sendResponse(manualFallback('driver_unavailable'))
    return false
  }

  const tabId = sender.tab?.id
  const browser = globalThis.chrome
  const task = action === SURFACE_ACTION.LAUNCH
    ? driver.launch(browser)
    : action === SURFACE_ACTION.HEALTH
      ? driver.health(tabId, browser)
      : action === SURFACE_ACTION.FILL
        ? driver.fill(tabId, message.context, browser)
        : action === SURFACE_ACTION.REQUEST_USER_CONFIRMATION
          ? driver.requestUserConfirmation(tabId, browser)
          : action === SURFACE_ACTION.SEND_CONFIRMED
            ? driver.sendConfirmed(tabId, message.confirmed === true, browser)
            : action === SURFACE_ACTION.CAPTURE
              ? driver.capture(tabId, browser)
              : importClipboard(driver, message)

  Promise.resolve(task).then(sendResponse).catch(() => sendResponse(manualFallback('driver_unavailable')))
  return true
})
