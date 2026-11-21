import type { WeekSummary } from '../api/types'
import { formatKm } from '../lib/format'

/** KPI principal no topo à esquerda: aderência da semana com o contexto que dá sentido ao número. */
export function AdherenceHero({ week }: { week: WeekSummary }) {
  const progress = week.planned_distance_m
    ? Math.min(100, (100 * week.actual_distance_m) / week.planned_distance_m)
    : 0
  return (
    <section className="card hero" aria-labelledby="hero-title">
      <h2 id="hero-title" className="card__label">
        Aderência da semana
      </h2>
      <p className="hero__value">
        {week.adherence_pct == null ? '—' : `${Math.round(week.adherence_pct)}%`}
      </p>
      <p className="hero__context">
        {week.completed_workouts} de {week.planned_workouts} treinos feitos ·{' '}
        {formatKm(week.actual_distance_m)} de {formatKm(week.planned_distance_m)}
      </p>
      <div
        className="progress"
        role="progressbar"
        aria-label="Volume realizado"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress)}
      >
        <div className="progress__bar" style={{ width: `${progress}%` }} />
      </div>
    </section>
  )
}
