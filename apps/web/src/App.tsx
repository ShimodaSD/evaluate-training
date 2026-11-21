import { useState } from 'react'
import { useSWRConfig } from 'swr'
import { deletePlannedWorkout } from './api/client'
import { ActivityUpload } from './components/ActivityUpload'
import { AdherenceHero } from './components/AdherenceHero'
import { CoachCard } from './components/CoachCard'
import { DayList } from './components/DayList'
import { Dialog } from './components/Dialog'
import { DistanceChart } from './components/DistanceChart'
import { EmptyWeek } from './components/EmptyWeek'
import { NextAction } from './components/NextAction'
import { PlanForm } from './components/PlanForm'
import { useWeek } from './hooks/useWeek'
import { addDays, formatShortDate, toIsoDate } from './lib/format'

type Panel = 'plan' | 'upload' | null

function App() {
  const [today] = useState(() => toIsoDate(new Date()))
  const [day, setDay] = useState(today)
  const [panel, setPanel] = useState<Panel>(null)
  const { data: week, error, isLoading } = useWeek(day)
  const { mutate } = useSWRConfig()

  const refreshWeeks = () => mutate((key) => typeof key === 'string' && key.startsWith('/weeks/'))

  async function handleDelete(id: number) {
    await deletePlannedWorkout(id)
    await refreshWeeks()
  }

  const firstFreeDay =
    week?.days.find((d) => d.workouts.length === 0 && d.date >= today)?.date ?? today

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Treinos de corrida</h1>
          {week ? (
            <nav className="week-nav" aria-label="Semana">
              <button
                type="button"
                className="button button--ghost"
                onClick={() => setDay(addDays(week.week_start, -7))}
                aria-label="Semana anterior"
              >
                ←
              </button>
              <span>
                {formatShortDate(week.week_start)} – {formatShortDate(week.week_end)}
              </span>
              <button
                type="button"
                className="button button--ghost"
                onClick={() => setDay(addDays(week.week_start, 7))}
                aria-label="Próxima semana"
              >
                →
              </button>
              {day !== today ? (
                <button
                  type="button"
                  className="button button--ghost"
                  onClick={() => setDay(today)}
                >
                  Hoje
                </button>
              ) : null}
            </nav>
          ) : null}
        </div>
        <div className="topbar__actions">
          <button
            type="button"
            className="button button--secondary"
            onClick={() => setPanel('plan')}
          >
            Colar treino
          </button>
          <button type="button" className="button" onClick={() => setPanel('upload')}>
            Enviar atividade
          </button>
        </div>
      </header>

      <main>
        {error ? (
          <p className="alert alert--error" role="alert">
            Não foi possível carregar a semana: {error.message}
          </p>
        ) : isLoading || !week ? (
          <p role="status">Carregando...</p>
        ) : week.planned_workouts === 0 &&
          week.days.every((d) => d.extra_activities.length === 0) ? (
          <EmptyWeek onAddPlan={() => setPanel('plan')} />
        ) : (
          <div className="grid">
            <AdherenceHero week={week} />
            <NextAction week={week} today={today} onUpload={() => setPanel('upload')} />
            <CoachCard key={week.week_start} day={week.week_start} />
            <DistanceChart days={week.days} />
            <DayList days={week.days} today={today} onDelete={handleDelete} />
          </div>
        )}
      </main>

      <Dialog title="Colar treino planejado" open={panel === 'plan'} onClose={() => setPanel(null)}>
        <PlanForm defaultDate={firstFreeDay} onSaved={refreshWeeks} />
      </Dialog>
      <Dialog title="Enviar atividades" open={panel === 'upload'} onClose={() => setPanel(null)}>
        <ActivityUpload onUploaded={refreshWeeks} />
      </Dialog>
    </div>
  )
}

export default App
