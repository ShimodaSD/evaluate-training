import { useState } from 'react'
import { analyzeWeek } from '../api/client'

/** Avaliação da semana escrita pelo Claude, gerada sob demanda. */
export function CoachCard({ day }: { day: string }) {
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleClick() {
    setLoading(true)
    setError(null)
    try {
      setAnalysis((await analyzeWeek(day)).analysis)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível avaliar a semana')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card" aria-labelledby="coach-title" aria-busy={loading}>
      <div className="chart__header">
        <h2 id="coach-title" className="card__label">
          Avaliação do Claude
        </h2>
        <button
          type="button"
          className="button button--secondary"
          onClick={handleClick}
          disabled={loading}
        >
          {loading ? 'Avaliando...' : analysis ? 'Avaliar de novo' : 'Avaliar semana'}
        </button>
      </div>
      {error ? (
        <p className="alert alert--error" role="alert">
          {error}
        </p>
      ) : null}
      {analysis ? (
        <p className="coach__text">{analysis}</p>
      ) : (
        <p className="muted">
          O Claude lê o planejado x realizado da semana e aponta o que foi bem, o que fugiu do plano
          e o que ajustar.
        </p>
      )}
    </section>
  )
}
