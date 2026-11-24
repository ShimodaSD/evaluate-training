import { useState, type DragEvent } from 'react'
import { syncGarmin, uploadActivities } from '../api/client'
import type { UploadResult } from '../api/types'
import { formatKm, formatPace, formatWeekday } from '../lib/format'

const ACCEPT = '.fit,.gpx,.tcx'

export function ActivityUpload({ onUploaded }: { onUploaded: () => void }) {
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [dragging, setDragging] = useState(false)

  async function run(action: () => Promise<UploadResult>) {
    setUploading(true)
    setError(null)
    try {
      setResult(await action())
      onUploaded()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha no envio')
    } finally {
      setUploading(false)
    }
  }

  function send(files: File[]) {
    if (files.length > 0) void run(() => uploadActivities(files))
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault()
    setDragging(false)
    send(Array.from(event.dataTransfer.files))
  }

  return (
    <div className="form">
      <label
        className={dragging ? 'dropzone dropzone--active' : 'dropzone'}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <input
          type="file"
          multiple
          accept={ACCEPT}
          className="visually-hidden"
          onChange={(e) => send(Array.from(e.target.files ?? []))}
        />
        <strong>{uploading ? 'Enviando...' : 'Arraste os arquivos ou clique para escolher'}</strong>
        <span className="muted">FIT, GPX ou TCX exportados do Garmin Connect</span>
      </label>
      <button
        type="button"
        className="button button--secondary"
        disabled={uploading}
        onClick={() => void run(syncGarmin)}
      >
        Sincronizar atividades do Garmin (últimos 7 dias)
      </button>
      {error ? (
        <p className="alert alert--error" role="alert">
          {error}
        </p>
      ) : null}
      {result ? (
        <div role="status">
          {result.created.length > 0 ? (
            <ul className="alert alert--success upload-list">
              {result.created.map((a) => (
                <li key={a.id}>
                  ✓ {formatWeekday(a.activity_date)}: {formatKm(a.distance_m)} ·{' '}
                  {formatPace(a.pace_s_per_km)}
                </li>
              ))}
            </ul>
          ) : null}
          {result.skipped.length > 0 ? (
            <p className="muted">Já enviados antes: {result.skipped.join(', ')}</p>
          ) : null}
          {Object.entries(result.errors).map(([file, message]) => (
            <p key={file} className="alert alert--error">
              {file}: {message}
            </p>
          ))}
        </div>
      ) : null}
    </div>
  )
}
