"use strict"

const MAX_RESPONSE_BYTES = 262144
const MAX_REQUEST_BYTES = 65536
const MAX_PATH_LENGTH = 256
const LOOPBACK_HOST = '127.0.0.1'

export class LoopbackClientError extends Error {
  constructor(code = 'loopback_request_failed') {
    const safeCode = [
      'loopback_endpoint_rejected',
      'loopback_path_rejected',
      'loopback_auth_required',
      'loopback_fetch_unavailable',
      'loopback_response_too_large',
      'loopback_request_too_large',
      'loopback_request_failed',
      'loopback_response_invalid',
    ].includes(code) ? code : 'loopback_request_failed'
    super(safeCode)
    this.code = safeCode
    this.name = 'LoopbackClientError'
  }
}

export function validateLoopbackBaseUrl(value) {
  if (typeof value !== 'string' || value.length === 0 || value.length > 256) {
    throw new LoopbackClientError('loopback_endpoint_rejected')
  }
  let parsed
  try {
    parsed = new URL(value)
  } catch {
    throw new LoopbackClientError('loopback_endpoint_rejected')
  }
  if (
    parsed.protocol !== 'http:' ||
    parsed.hostname !== LOOPBACK_HOST ||
    parsed.username ||
    parsed.password ||
    parsed.search ||
    parsed.hash
    || value.includes('..')
    || parsed.pathname.includes('..')
    || parsed.pathname.includes('\\')
    || parsed.pathname.includes('//')
    || /%2e|%2f|%5c/i.test(parsed.pathname)
  ) {
    throw new LoopbackClientError('loopback_endpoint_rejected')
  }
  return parsed
}

function validatePath(path) {
  if (
    typeof path !== 'string' ||
    path.length < 2 ||
    path.length > MAX_PATH_LENGTH ||
    !path.startsWith('/') ||
    path.includes('?') ||
    path.includes('#') ||
    path.includes('..') ||
    path.includes('\\') ||
    path.includes('//') ||
    /%2e|%2f|%5c/i.test(path)
  ) {
    throw new LoopbackClientError('loopback_path_rejected')
  }
  return path
}

async function readBoundedText(response) {
  const declared = response.headers?.get?.('content-length')
  if (declared !== null && declared !== undefined) {
    const length = Number(declared)
    if (!Number.isFinite(length) || length < 0 || length > MAX_RESPONSE_BYTES) {
      throw new LoopbackClientError('loopback_response_too_large')
    }
  }
  const reader = response.body?.getReader?.()
  if (!reader) throw new LoopbackClientError('loopback_response_invalid')
  const chunks = []
  let size = 0
  while (true) {
    const item = await reader.read()
    if (item.done) break
    size += item.value.byteLength
    if (size > MAX_RESPONSE_BYTES) {
      await reader.cancel()
      throw new LoopbackClientError('loopback_response_too_large')
    }
    chunks.push(item.value)
  }
  const combined = new Uint8Array(size)
  let offset = 0
  for (const chunk of chunks) {
    combined.set(chunk, offset)
    offset += chunk.byteLength
  }
  return new TextDecoder().decode(combined)
}

export class LoopbackClient {
  #baseUrl
  #token
  #fetch

  constructor({ baseUrl, token, fetchImpl = globalThis.fetch } = {}) {
    this.#baseUrl = validateLoopbackBaseUrl(baseUrl)
    if (typeof token !== 'string' || token.length === 0 || token.length > 512) {
      throw new LoopbackClientError('loopback_auth_required')
    }
    if (typeof fetchImpl !== 'function') {
      throw new LoopbackClientError('loopback_fetch_unavailable')
    }
    // Session-only memory.  Never write this token to storage, logs, or URLs.
    this.#token = token
    this.#fetch = fetchImpl
  }

  async request(path, { method = 'GET', body } = {}) {
    const relativePath = validatePath(path)
    if (!['GET', 'POST'].includes(method)) throw new LoopbackClientError('loopback_path_rejected')
    const basePath = this.#baseUrl.pathname === '/'
      ? ''
      : this.#baseUrl.pathname.replace(/\/+$/, '')
    const url = new URL(`${basePath}${relativePath}`, this.#baseUrl.origin)
    if (url.hostname !== LOOPBACK_HOST || url.origin !== this.#baseUrl.origin) {
      throw new LoopbackClientError('loopback_endpoint_rejected')
    }
    const headers = { 'X-Loopback-Token': this.#token }
    const init = {
      method,
      headers,
      redirect: 'error',
      credentials: 'omit',
      cache: 'no-store',
    }
    if (body !== undefined) {
      let serialized
      try {
        serialized = JSON.stringify(body)
      } catch {
        throw new LoopbackClientError('loopback_request_failed')
      }
      if (new TextEncoder().encode(serialized).byteLength > MAX_REQUEST_BYTES) {
        throw new LoopbackClientError('loopback_request_too_large')
      }
      headers['Content-Type'] = 'application/json'
      init.body = serialized
    }
    let response
    try {
      response = await this.#fetch(url.toString(), init)
    } catch {
      throw new LoopbackClientError('loopback_request_failed')
    }
    const text = await readBoundedText(response)
    if (!response.ok) throw new LoopbackClientError('loopback_request_failed')
    if (!text) return null
    try {
      return JSON.parse(text)
    } catch {
      throw new LoopbackClientError('loopback_response_invalid')
    }
  }
}
