export const chatgptDriver = {
  id: 'chatgpt-web',
  matches: (url) => url.startsWith('https://chatgpt.com/'),
  async health() {
    return { status: 'DEGRADED', reason: 'Driver implementation pending V1 integration phase' }
  },
}
