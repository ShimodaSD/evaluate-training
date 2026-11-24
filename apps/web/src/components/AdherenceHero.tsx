import type { WeekSummary } from '../api/types'
import { SPORT_LABEL, formatClock, formatKm } from '../lib/format'

/** KPI principal no topo à esquerda: aderência da semana com o contexto que dá sentido ao número. */
export function AdherenceHero({ week }: { week: WeekSummary }) {
  const progress = week.planned_workouts
    ? (100 * week.completed_workouts) / week.planned_workouts
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
        {formatClock(week.actual_duration_s)} de treino
      </p>
      <div
        className="progress"
        role="progressbar"
        aria-label="Treinos feitos"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress)}
      >
        <div className="progress__bar" style={{ width: `${progress}%` }} />
      </div>
      <ul className="hero__sports">
        {week.sports.map((s) => (
          <li key={s.sport}>
            {SPORT_LABEL[s.sport]}: {formatKm(s.actual_distance_m)}
            {/* Treinos por tempo (comum no ciclismo) não têm distância planejada. */}
            {s.planned_distance_m > 0 ? ` de ${formatKm(s.planned_distance_m)}` : ''}
          </li>
        ))}
      </ul>
    </section>
  )
}
