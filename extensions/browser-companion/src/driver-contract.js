/**
 * @typedef {Object} WebSurfaceDriver
 * @property {string} id
 * @property {(url: string) => boolean} matches
 * @property {(tabId: number) => Promise<object>} health
 * @property {(tabId: number, context: object) => Promise<object>} fill
 * @property {(tabId: number) => Promise<object>} capture
 */

export const DRIVER_STATUS = Object.freeze({
  READY: 'READY',
  DEGRADED: 'DEGRADED',
  UNAVAILABLE: 'UNAVAILABLE',
})
