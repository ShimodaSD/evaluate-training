import { useState } from 'react'
import { recommendToday } from '../api/client'
import type { TodayRecommendation } from '../api/types'
import { SPORT_LABEL } from '../lib/format'

// Reaproveita as cores do StatusBadge: prontidão alta = cumprido, baixa = não feito.
const READINESS = {
  alta: { icon: '✓', badge: 'done' },
  moderada: { icon: '◐', badge: 'partial' },
  baixa: { icon: '✕', badge: 'missed' },
} as const

/** Treino de hoje sugerido pela IA com os dados da Garmin, gerado sob demanda. */
export function TodayCard() {
  const [rec, setRec] = useState<TodayRecommendation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [sport, setSport] = useState<'bike' | 'run'>('bike')

  async function handleClick() {
    setLoading(true)
    setError(null)
    try {
      setRec(await recommendToday(sport))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível recomendar o treino')
    } finally {
      setLoading(false)
    }
  }

  const readiness = rec ? READINESS[rec.readiness] : null

  return (
    <section className="card" aria-labelledby="today-title" aria-busy={loading}>
      <div className="chart__header">
        <h2 id="today-title" className="card__label">
          Treino de hoje
        </h2>
        <label>
          Esporte{' '}
          <select value={sport} onChange={(e) => setSport(e.target.value as 'bike' | 'run')}>
            <option value="bike">{SPORT_LABEL.bike}</option>
            <option value="run">{SPORT_LABEL.run}</option>
          </select>
        </label>
        <button
          type="button"
          className="button button--secondary"
          onClick={handleClick}
          disabled={loading}
        >
          {loading ? 'Lendo a Garmin...' : rec ? 'Recomendar de novo' : 'Recomendar treino'}
        </button>
      </div>
      {error ? (
        <p className="alert alert--error" role="alert">
          {error}
        </p>
      ) : null}
      {rec && readiness ? (
        <>
          <p>
            <span className={`badge badge--${readiness.badge}`}>
              <span aria-hidden="true">{readiness.icon}</span> Prontidão {rec.readiness}
            </span>
          </p>
          <h3>
            {rec.title}
            {rec.sport !== 'rest' ? ` · ${SPORT_LABEL[rec.sport]}` : null}
            {rec.duration_min ? ` · ${rec.duration_min} min` : null}
          </h3>
          <p className="coach__text">{rec.workout}</p>
          <p className="coach__text muted">{rec.reason}</p>
          {rec.unavailable.length > 0 ? (
            <p className="muted">Sem dados da Garmin de: {rec.unavailable.join(', ')}.</p>
          ) : null}
        </>
      ) : (
        <p className="muted">
          A IA lê sono, HRV, body battery, estresse e sua carga recente na Garmin, junto com o plano
          da semana, e diz o que treinar hoje.
        </p>
      )}
    </section>
  )
}
