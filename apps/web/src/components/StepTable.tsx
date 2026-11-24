import type { PaceStatus, Sport, StepComparison } from '../api/types'
import { formatClock, formatKm, formatPace, formatPaceRange } from '../lib/format'

const PACE_LABEL: Record<PaceStatus, string> = {
  in_range: '✓ no alvo',
  fast: '↑ rápido',
  slow: '↓ lento',
}

export function StepTable({ steps, sport }: { steps: StepComparison[]; sport: Sport }) {
  return (
    <div className="table-wrap">
      <table className="steps">
        <thead>
          <tr>
            <th>Passo</th>
            <th>Planejado</th>
            <th>Alvo</th>
            <th>Realizado</th>
            <th>{sport === 'bike' ? 'Velocidade' : 'Pace'}</th>
          </tr>
        </thead>
        <tbody>
          {steps.map((step) => (
            <tr key={step.index} className={step.is_rest ? 'steps__rest' : undefined}>
              <td>
                {step.name}
                {step.intensity ? <span className="muted"> · {step.intensity}</span> : null}
              </td>
              <td>
                {step.planned_distance_m != null
                  ? formatKm(step.planned_distance_m)
                  : formatClock(step.planned_duration_s ?? 0)}
              </td>
              <td>
                {formatPaceRange(
                  step.target_pace_min_s_per_km,
                  step.target_pace_max_s_per_km,
                  sport,
                )}
              </td>
              <td>
                {formatKm(step.actual_distance_m)} · {formatClock(step.actual_duration_s)}
              </td>
              <td>
                {formatPace(step.actual_pace_s_per_km, sport)}
                {step.pace_status ? (
                  <span className={`pace pace--${step.pace_status}`}>
                    {' '}
                    {PACE_LABEL[step.pace_status]}
                  </span>
                ) : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
