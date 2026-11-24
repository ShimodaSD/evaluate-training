import { useState } from 'react'
import { syncGarmin } from '../api/client'
import type { UploadResult } from '../api/types'

/** Botão do topo: importa as atividades dos últimos 7 dias do Garmin Connect. */
export function GarminSync({ onSynced }: { onSynced: () => void }) {
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)

  async function handleSync() {
    setSyncing(true)
    setError(null)
    setResult(null)
    try {
      setResult(await syncGarmin())
      onSynced()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha na sincronização')
    } finally {
      setSyncing(false)
    }
  }

  const failed = result ? Object.keys(result.errors).length : 0
  return (
    <div className="garmin-sync">
      <button
        type="button"
        className="button button--secondary"
        disabled={syncing}
        onClick={handleSync}
      >
        {syncing ? 'Sincronizando...' : 'Sincronizar Garmin'}
      </button>
      {error ? (
        <p className="alert alert--error" role="alert">
          {error}
        </p>
      ) : result ? (
        <p className="muted" role="status">
          ✓ {result.created.length} novas · {result.skipped.length} já importadas
          {failed > 0 ? ` · ✕ ${failed} com erro` : ''}
        </p>
      ) : null}
    </div>
  )
}
