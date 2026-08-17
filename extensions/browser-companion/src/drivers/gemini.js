export const geminiDriver = {
  id: 'gemini-web',
  matches: (url) => url.startsWith('https://gemini.google.com/'),
  async health() {
    return { status: 'DEGRADED', reason: 'Driver implementation pending V1 integration phase' }
  },
}
