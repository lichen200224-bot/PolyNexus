export const DRIVER_STATUS = Object.freeze({
  READY: 'READY',
  DEGRADED: 'DEGRADED',
  UNAVAILABLE: 'UNAVAILABLE',
})

export const SURFACE_ACTION = Object.freeze({
  LAUNCH: 'LAUNCH',
  HEALTH: 'HEALTH',
  FILL: 'FILL',
  REQUEST_USER_CONFIRMATION: 'REQUEST_USER_CONFIRMATION',
  SEND_CONFIRMED: 'SEND_CONFIRMED',
  CAPTURE: 'CAPTURE',
  CLIPBOARD_IMPORT: 'CLIPBOARD_IMPORT',
})

export const FALLBACK_MODE = 'MANUAL_CLIPBOARD'
export const MAX_WEB_TEXT_LENGTH = 4096
export const MAX_CONTEXT_ITEMS = 16

const SAFE_DRIVER_ID = /^[a-z][a-z0-9-]{0,63}$/
const REDACTED = '[REDACTED]'
const TRUNCATED = '[TRUNCATED]'
const SAFE_FAILURES = new Set([
  'browser_scripting_unavailable',
  'driver_unavailable',
  'manual_clipboard_required',
  'user_confirmation_required',
  'web_surface_response_invalid',
])

export class WebSurfaceError extends Error {
  constructor(code = 'driver_unavailable') {
    const safeCode = SAFE_FAILURES.has(code) ? code : 'driver_unavailable'
    super(safeCode)
    this.code = safeCode
    this.name = 'WebSurfaceError'
  }
}

/** Sanitize bounded web text before it can cross the extension boundary. */
export function sanitizeWebText(value, maxLength = MAX_WEB_TEXT_LENGTH) {
  let text = typeof value === 'string' ? value : ''
  text = text
    .replace(/\b(?:api[_ -]?key|access[_ -]?token|authorization|bearer|cookie|credential|password|secret|token)\s*[:=]\s*[^\s,;]+/gi, REDACTED)
    .replace(/\bBearer\s+[^\s,;]+/gi, `Bearer ${REDACTED}`)
    .replace(/\b(?:secret|token|password|credential|api[_-]?key)[_-][A-Za-z0-9][A-Za-z0-9._-]*\b/gi, REDACTED)
    .replace(/(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\s,;]+/g, '[PATH_REDACTED]')
    .replace(/(?<![A-Za-z0-9_])\\\\[^\s,;]+/g, '[PATH_REDACTED]')
  if (maxLength < 1) return ''
  if (text.length <= maxLength) return text
  return `${text.slice(0, Math.max(0, maxLength - TRUNCATED.length - 1))} ${TRUNCATED}`
}

export function manualFallback(code = 'manual_clipboard_required') {
  return Object.freeze({
    status: DRIVER_STATUS.DEGRADED,
    fallback: FALLBACK_MODE,
    reason: SAFE_FAILURES.has(code) ? code : 'manual_clipboard_required',
  })
}

export function normalizeDriverResult(driverId, captured) {
  const safeDriverId = typeof driverId === 'string' && SAFE_DRIVER_ID.test(driverId)
    ? driverId
    : 'unknown-driver'
  const text = sanitizeWebText(captured?.text)
  if (!text) return manualFallback('web_surface_response_invalid')
  return Object.freeze({
    driver_id: safeDriverId,
    kind: 'AI_OPINION',
    status: 'NORMALIZED',
    text,
    fallback: null,
  })
}

/** Execute only a driver-owned page function in the selected tab. */
export async function executeInTab(browser, tabId, pageFunction, args = []) {
  const runtime = browser ?? globalThis.chrome
  if (!Number.isInteger(tabId) || typeof pageFunction !== 'function' || !runtime?.scripting?.executeScript) {
    throw new WebSurfaceError('browser_scripting_unavailable')
  }
  try {
    const results = await runtime.scripting.executeScript({
      target: { tabId },
      func: pageFunction,
      args,
    })
    return results?.[0]?.result ?? null
  } catch {
    throw new WebSurfaceError('driver_unavailable')
  }
}

export function sanitizeContext(context) {
  if (!context || typeof context !== 'object') return ''
  const values = []
  for (const key of ['instructions', 'constraints']) {
    if (!Array.isArray(context[key])) continue
    for (const item of context[key].slice(0, MAX_CONTEXT_ITEMS)) {
      const safe = sanitizeWebText(item, 768)
      if (safe) values.push(safe)
    }
  }
  return sanitizeWebText(values.join('\n'), MAX_WEB_TEXT_LENGTH)
}
