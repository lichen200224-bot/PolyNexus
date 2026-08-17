export const claudeDriver = {
  id: 'claude-web',
  matches: (url) => url.startsWith('https://claude.ai/'),
  async health() {
    return { status: 'DEGRADED', reason: 'Driver implementation pending V1 integration phase' }
  },
}
