import type { DaySummary, PlannedVsDone } from '../api/types'
import { SPORT_LABEL, formatKm, formatPace, formatPower, formatWeekday } from '../lib/format'
import { StatusBadge } from './StatusBadge'
import { StepTable } from './StepTable'

interface Props {
  days: DaySummary[]
  today: string
  onDelete: (id: number) => void
}

function WorkoutItem({ item, onDelete }: { item: PlannedVsDone; onDelete: (id: number) => void }) {
  const { planned, activity, comparison } = item
  return (
    <li className="workout">
      <details>
        <summary>
          <span className="workout__title">
            <span className="muted">{SPORT_LABEL[planned.sport]} · </span>
            {planned.title ?? `${formatKm(planned.total_distance_m)} planejado`}
          </span>
          <StatusBadge status={item.status} />
          <span className="workout__numbers">
            {activity
              ? `${formatKm(activity.distance_m)} · ${formatPace(activity.pace_s_per_km, activity.sport)}${activity.avg_power_w != null ? ` · ${formatPower(activity.avg_power_w)}` : ''}`
              : formatKm(planned.total_distance_m)}
          </span>
          {comparison ? (
            <span className="workout__score">{Math.round(comparison.adherence_pct)}%</span>
          ) : null}
        </summary>
        <div className="workout__body">
          {comparison?.steps ? (
            <StepTable steps={comparison.steps} sport={planned.sport} />
          ) : (
            <pre className="workout__plan">{planned.raw_text}</pre>
          )}
          <button
            type="button"
            className="button button--ghost"
            onClick={() => onDelete(planned.id)}
          >
            Remover treino planejado
          </button>
        </div>
      </details>
    </li>
  )
}

export function DayList({ days, today, onDelete }: Props) {
  return (
    <section className="card" aria-labelledby="days-title">
      <h2 id="days-title" className="card__label">
        Planejado x realizado
      </h2>
      <ol className="days">
        {days.map((day) => (
          <li key={day.date} className={day.date === today ? 'day day--today' : 'day'}>
            <span className="day__name">{formatWeekday(day.date)}</span>
            {day.workouts.length === 0 && day.extra_activities.length === 0 ? (
              <span className="muted">Descanso</span>
            ) : (
              <ul className="day__items">
                {day.workouts.map((item) => (
                  <WorkoutItem key={item.planned.id} item={item} onDelete={onDelete} />
                ))}
                {day.extra_activities.map((a) => (
                  <li key={a.id} className="workout workout--extra">
                    <span className="workout__title">
                      Atividade extra <span className="muted">· {SPORT_LABEL[a.sport]}</span>
                    </span>
                    <span className="workout__numbers">
                      {formatKm(a.distance_m)} · {formatPace(a.pace_s_per_km, a.sport)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ol>
    </section>
  )
}
