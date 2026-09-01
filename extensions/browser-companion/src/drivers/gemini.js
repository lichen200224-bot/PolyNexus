import {
  DRIVER_STATUS,
  executeInTab,
  manualFallback,
  normalizeDriverResult,
  sanitizeContext,
} from '../driver-contract.js'

const launchUrl = 'https://gemini.google.com/'

function pageHasComposer() {
  return Boolean(document.querySelector('textarea, [contenteditable="true"]'))
}

function pageFill(prompt) {
  const field = document.querySelector('textarea, [contenteditable="true"]')
  if (!field) return false
  const value = String(prompt).slice(0, 4096)
  if ('value' in field) field.value = value
  else field.textContent = value
  field.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText' }))
  return true
}

function pageSend() {
  const button = document.querySelector('button[aria-label*="Send"], button[type="submit"]')
  if (!button || button.disabled) return false
  button.click()
  return true
}

function pageCapture() {
  const nodes = document.querySelectorAll('message-content, [data-message-author-role="model"], article')
  const last = nodes[nodes.length - 1]
  return { text: last?.innerText?.slice(0, 4096) ?? '' }
}

export const geminiDriver = {
  id: 'gemini-web',
  matches(url) {
    try {
      const parsed = new URL(url)
      return parsed.protocol === 'https:' && parsed.hostname === 'gemini.google.com'
    } catch {
      return false
    }
  },
  async launch(browser) {
    try {
      await browser.tabs.create({ url: launchUrl })
      return { status: DRIVER_STATUS.READY, action: 'LAUNCHED', driver_id: this.id }
    } catch {
      return manualFallback('driver_unavailable')
    }
  },
  async health(tabId, browser) {
    try {
      return (await executeInTab(browser, tabId, pageHasComposer))
        ? { status: DRIVER_STATUS.READY, driver_id: this.id }
        : manualFallback('driver_unavailable')
    } catch {
      return manualFallback('driver_unavailable')
    }
  },
  async fill(tabId, context, browser) {
    const prompt = sanitizeContext(context)
    if (!prompt) return manualFallback('web_surface_response_invalid')
    try {
      const filled = await executeInTab(browser, tabId, pageFill, [prompt])
      return filled
        ? { status: DRIVER_STATUS.READY, action: 'FILLED', requires_user_confirmation: true }
        : manualFallback('driver_unavailable')
    } catch {
      return manualFallback('manual_clipboard_required')
    }
  },
  async requestUserConfirmation() {
    return { status: DRIVER_STATUS.READY, action: 'READY_TO_SEND', automatic_send: false, requires_user_confirmation: true }
  },
  async sendConfirmed(tabId, confirmed, browser) {
    if (confirmed !== true) return manualFallback('user_confirmation_required')
    try {
      const sent = await executeInTab(browser, tabId, pageSend)
      return sent
        ? { status: DRIVER_STATUS.READY, action: 'SENT', user_confirmed: true }
        : manualFallback('driver_unavailable')
    } catch {
      return manualFallback('manual_clipboard_required')
    }
  },
  async capture(tabId, browser) {
    try {
      return normalizeDriverResult(this.id, await executeInTab(browser, tabId, pageCapture))
    } catch {
      return manualFallback('manual_clipboard_required')
    }
  },
}
