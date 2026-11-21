import type { WeekSummary } from '../api/types'
import { formatKm, formatWeekday } from '../lib/format'

interface Props {
  week: WeekSummary
  today: string
  onUpload: () => void
}

/** Camada acionável: diz o que fazer agora em vez de só mostrar números. */
export function NextAction({ week, today, onUpload }: Props) {
  const workouts = week.days.flatMap((d) => d.workouts)
  const missed = workouts.find((w) => w.status === 'missed')
  const next = workouts.find((w) => w.status === 'planned' && w.planned.scheduled_date >= today)

  if (missed) {
    return (
      <section className="card action">
        <h2 className="card__label">Falta registrar</h2>
        <p>
          O treino de <strong>{formatWeekday(missed.planned.scheduled_date)}</strong> (
          {formatKm(missed.planned.total_distance_m)}) ainda não tem atividade. Se você correu,
          envie o arquivo do relógio.
        </p>
        <button type="button" className="button" onClick={onUpload}>
          Enviar atividade
        </button>
      </section>
    )
  }
  if (next) {
    const isToday = next.planned.scheduled_date === today
    return (
      <section className="card action">
        <h2 className="card__label">{isToday ? 'Treino de hoje' : 'Próximo treino'}</h2>
        <p>
          <strong>{isToday ? 'Hoje' : formatWeekday(next.planned.scheduled_date)}</strong>:{' '}
          {formatKm(next.planned.total_distance_m)}
          {next.planned.title ? ` · ${next.planned.title}` : ''}
        </p>
      </section>
    )
  }
  return (
    <section className="card action">
      <h2 className="card__label">Semana</h2>
      <p>Todos os treinos planejados já foram avaliados.</p>
    </section>
  )
}
