import type { DaySummary } from '../api/types'
import { formatClock, formatWeekday } from '../lib/format'

const HEIGHT = 140
const BAR = 14
const GAP = 2

// Planejado: meio da faixa estimada; passos sem alvo de pace não têm estimativa e contam 0.
const estimate = (range: [number, number] | null) => (range ? (range[0] + range[1]) / 2 : 0)

function dayTotals(day: DaySummary) {
  const planned = day.workouts.reduce(
    (sum, w) => sum + estimate(w.planned.structure.estimated_duration_s),
    0,
  )
  const done =
    day.workouts.reduce((sum, w) => sum + (w.activity?.duration_s ?? 0), 0) +
    day.extra_activities.reduce((sum, a) => sum + a.duration_s, 0)
  return { planned, done }
}

/** Barras agrupadas: tempo planejado x realizado por dia, a medida que soma todos os esportes. */
export function DistanceChart({ days }: { days: DaySummary[] }) {
  const totals = days.map(dayTotals)
  const max = Math.max(1, ...totals.flatMap((t) => [t.planned, t.done]))
  const scale = (m: number) => (m / max) * HEIGHT

  return (
    <section className="card" aria-labelledby="chart-title">
      <div className="chart__header">
        <h2 id="chart-title" className="card__label">
          Tempo por dia
        </h2>
        <ul className="legend">
          <li>
            <span className="legend__swatch legend__swatch--planned" /> Planejado
          </li>
          <li>
            <span className="legend__swatch legend__swatch--done" /> Realizado
          </li>
        </ul>
      </div>
      <div className="chart" role="img" aria-label="Tempo planejado e realizado por dia">
        {days.map((day, i) => {
          const { planned, done } = totals[i]
          return (
            <div
              key={day.date}
              className="chart__day"
              title={`${formatWeekday(day.date)}: ${formatClock(planned)} planejado, ${formatClock(done)} realizado`}
            >
              <svg width={BAR * 2 + GAP} height={HEIGHT} aria-hidden="true">
                <rect
                  className="chart__bar--planned"
                  x={0}
                  y={HEIGHT - scale(planned)}
                  width={BAR}
                  height={scale(planned)}
                  rx={4}
                />
                <rect
                  className="chart__bar--done"
                  x={BAR + GAP}
                  y={HEIGHT - scale(done)}
                  width={BAR}
                  height={scale(done)}
                  rx={4}
                />
              </svg>
              <span className="chart__axis">{formatWeekday(day.date)}</span>
            </div>
          )
        })}
      </div>
      <table className="visually-hidden">
        <caption>Tempo por dia</caption>
        <thead>
          <tr>
            <th>Dia</th>
            <th>Planejado</th>
            <th>Realizado</th>
          </tr>
        </thead>
        <tbody>
          {days.map((day, i) => (
            <tr key={day.date}>
              <td>{formatWeekday(day.date)}</td>
              <td>{formatClock(totals[i].planned)}</td>
              <td>{formatClock(totals[i].done)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
