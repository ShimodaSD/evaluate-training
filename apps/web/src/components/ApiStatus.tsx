import { useEffect, useState } from 'react'
import { fetchHealth } from '../api/client'

type Status = 'loading' | 'online' | 'offline'

export function ApiStatus() {
  const [status, setStatus] = useState<Status>('loading')
  const [version, setVersion] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    fetchHealth()
      .then((data) => {
        if (!active) return
        setStatus('online')
        setVersion(data.version)
      })
      .catch(() => {
        if (active) setStatus('offline')
      })
    return () => {
      active = false
    }
  }, [])

  if (status === 'loading') return <p role="status">Verificando API...</p>
  if (status === 'offline') return <p role="status">API indisponível</p>
  return <p role="status">API online (v{version})</p>
}
