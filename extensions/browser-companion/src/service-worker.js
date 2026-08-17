import { chatgptDriver } from './drivers/chatgpt.js'
import { claudeDriver } from './drivers/claude.js'
import { geminiDriver } from './drivers/gemini.js'

const drivers = [chatgptDriver, claudeDriver, geminiDriver]

chrome.runtime.onInstalled.addListener(() => {
  console.info('PolyNexus Browser Companion baseline installed')
})

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type !== 'POLYNEXUS_DRIVER_HEALTH') return false

  const url = sender.tab?.url ?? ''
  const driver = drivers.find((candidate) => candidate.matches(url))
  if (!driver) {
    sendResponse({ status: 'UNAVAILABLE', reason: 'No matching WebSurface driver' })
    return false
  }

  Promise.resolve(driver.health(sender.tab?.id)).then(sendResponse)
  return true
})
