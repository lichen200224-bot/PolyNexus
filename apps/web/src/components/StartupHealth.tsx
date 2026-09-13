import { useEffect, useState } from 'react'
import {
  AuthError,
  getHealth,
  listProjects,
  type ApiClientConfig,
  type HealthResponse,
} from '../api'

type ClientReadiness = 'checking' | 'ready' | 'not_ready'

export interface StartupHealthProps {
  config: ApiClientConfig
}

export function StartupHealth({ config }: StartupHealthProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [clientReadiness, setClientReadiness] = useState<ClientReadiness>(
    config.authConfigured ? 'checking' : 'not_ready',
  )
  const [reason, setReason] = useState(
    config.authConfigured ? 'verifying_pairing' : 'pairing_not_configured',
  )

  useEffect(() => {
    if (!config.authConfigured) return
    let active = true

    async function verifyStartup() {
      try {
        const observedHealth = await getHealth(config)
        if (!active) return
        setHealth(observedHealth)
        await listProjects(config)
        if (!active) return
        setClientReadiness('ready')
        setReason('authenticated_api_verified')
      } catch (error) {
        if (!active) return
        setClientReadiness('not_ready')
        setReason(error instanceof AuthError ? 'authentication_rejected' : 'core_unavailable')
      }
    }

    void verifyStartup()
    return () => { active = false }
  }, [config])

  const observed = (layer: keyof HealthResponse['layers']) =>
    health?.layers[layer].status ?? 'unknown'

  return (
    <section aria-labelledby="startup-health-heading">
      <h2 id="startup-health-heading">Startup readiness</h2>
      <dl>
        <div><dt>Process</dt><dd>{observed('process')}</dd></div>
        <div><dt>Schema</dt><dd>{observed('schema')}</dd></div>
        <div><dt>Core</dt><dd>{observed('core')}</dd></div>
        <div><dt>API/auth</dt><dd>{observed('api_auth')}</dd></div>
        <div><dt>Web/client</dt><dd>{clientReadiness}</dd></div>
        <div><dt>Runtime</dt><dd>{observed('runtime')}</dd></div>
      </dl>
      <p role="status">Client pairing: {reason}</p>
    </section>
  )
}
