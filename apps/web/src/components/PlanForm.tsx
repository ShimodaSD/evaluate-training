import { useState, type FormEvent } from 'react'
import { createPlannedWorkout } from '../api/client'
import type { PlannedWorkout, Sport } from '../api/types'
import { SPORT_LABEL, addDays, formatClock, formatKm, formatWeekday } from '../lib/format'

interface Props {
  defaultDate: string
  onSaved: () => void
}

const SPORTS: Sport[] = ['run', 'bike', 'swim']

const PLACEHOLDER: Record<Sport, string> = {
  bike: `1. Aquecimento — Z1
15:00 @ 24-27 km/h
2. Endurance — Z2
1:00:00 @ 28-32 km/h`,
  swim: `1. Aquecimento
200 m @ 02:10-02:20 min/100m
2. Repeat 4 times
   1. Série
100 m @ 01:45-01:50 min/100m
   2. Pausa — Passiva
0:20 @ 00:00 min/100m`,
  other: '',
  run: `1. Aquecimento — Z1
2.00 km @ 05:44-06:23 min/km
Zona 1-Zona 2
2. Repeat 5 times
   1. Série principal — VO2
1.20 km @ 04:08-04:15 min/km
Zona 5-Zona 6
   2. Pausa — Passiva
2:30 @ 00:00 min/km`,
}

export function PlanForm({ defaultDate, onSaved }: Props) {
  const [date, setDate] = useState(defaultDate)
  const [sport, setSport] = useState<Sport>('run')
  const [text, setText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState<PlannedWorkout | null>(null)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const workout = await createPlannedWorkout(date, text, sport)
      setSaved(workout)
      setText('')
      // Avança o dia para colar o próximo treino da semana em sequência.
      setDate(addDays(date, 1))
      onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível salvar')
    } finally {
      setSaving(false)
    }
  }

  const estimate = saved?.structure.estimated_duration_s
  return (
    <form className="form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Dia do treino</span>
        <input type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
      </label>
      <label className="field">
        <span>Esporte</span>
        <select value={sport} onChange={(e) => setSport(e.target.value as Sport)}>
          {SPORTS.map((s) => (
            <option key={s} value={s}>
              {SPORT_LABEL[s]}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Treino copiado do TrainingPeaks</span>
        <textarea
          required
          rows={12}
          value={text}
          placeholder={PLACEHOLDER[sport]}
          onChange={(e) => setText(e.target.value)}
        />
      </label>
      {error ? (
        <p className="alert alert--error" role="alert">
          {error}
        </p>
      ) : null}
      {saved ? (
        <p className="alert alert--success" role="status">
          ✓ {SPORT_LABEL[saved.sport]} de {formatWeekday(saved.scheduled_date)} salvo:{' '}
          {formatKm(saved.total_distance_m)}
          {estimate ? `, cerca de ${formatClock(estimate[0])} a ${formatClock(estimate[1])}` : ''}.
          Cole o próximo treino ou feche.
        </p>
      ) : null}
      <button type="submit" className="button" disabled={saving}>
        {saving ? 'Salvando...' : 'Salvar treino'}
      </button>
    </form>
  )
}
