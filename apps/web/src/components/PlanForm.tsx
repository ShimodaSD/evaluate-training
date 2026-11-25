import { useState, type FormEvent } from 'react'
import { ApiError, createPlannedWorkout, previewPlan } from '../api/client'
import type { PlannedStep, PlannedWorkout, PlannedWorkoutStructure, Sport } from '../api/types'
import {
  SPORT_LABEL,
  addDays,
  formatClock,
  formatKm,
  formatPaceRange,
  formatPower,
  formatWeekday,
} from '../lib/format'

interface Props {
  defaultDate: string
  onSaved: () => void
}

const SPORTS: Sport[] = ['run', 'bike', 'swim']

const PLACEHOLDER: Record<Sport, string> = {
  bike: `1. Aquecimento — Z1
15:00 @ 24-27 km/h
2. Sweet spot — Z3 (no rolo, use watts)
20:00 @ 200-215 W
3. Endurance — Z2
30:00 @ 28-32 km/h`,
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

function describeStep(step: PlannedStep, sport: Sport): string {
  const size =
    step.distance_m != null ? formatKm(step.distance_m) : formatClock(step.duration_s ?? 0)
  const target = step.is_rest
    ? 'pausa'
    : step.power_min_w != null
      ? formatPower(step.power_min_w, step.power_max_w)
      : step.pace_min_s_per_km != null
        ? formatPaceRange(step.pace_min_s_per_km, step.pace_max_s_per_km, sport)
        : null
  return `${step.name} · ${size}${target ? ` @ ${target}` : ''}`
}

const errorMessage = (err: unknown) =>
  err instanceof Error ? err.message : 'Não foi possível salvar'

export function PlanForm({ defaultDate, onSaved }: Props) {
  const [date, setDate] = useState(defaultDate)
  const [sport, setSport] = useState<Sport>('run')
  const [text, setText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState<PlannedWorkout | null>(null)
  const [busy, setBusy] = useState<'saving' | 'reading' | null>(null)
  // Treino lido pela IA, mostrado para o usuário conferir antes de salvar.
  const [aiPreview, setAiPreview] = useState<PlannedWorkoutStructure | null>(null)

  async function readWithAI() {
    setBusy('reading')
    try {
      const [first, ...rest] = await previewPlan(text)
      if (rest.length) setError('Encontrei mais de um treino: cole um por vez.')
      else setAiPreview(first)
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy('saving')
    setError(null)
    setSaved(null)
    try {
      const workout = await createPlannedWorkout(date, text, sport, aiPreview ?? undefined)
      setSaved(workout)
      setText('')
      setAiPreview(null)
      // Avança o dia para colar o próximo treino da semana em sequência.
      setDate(addDays(date, 1))
      onSaved()
    } catch (err) {
      // Formato que o parser do TrainingPeaks não reconhece: tenta com a IA.
      if (!aiPreview && err instanceof ApiError && err.status === 422) await readWithAI()
      else setError(errorMessage(err))
    } finally {
      setBusy(null)
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
        <span>Treino (TrainingPeaks ou qualquer formato)</span>
        <textarea
          required
          rows={12}
          value={text}
          placeholder={PLACEHOLDER[sport]}
          onChange={(e) => {
            setText(e.target.value)
            setAiPreview(null)
          }}
        />
      </label>
      {error ? (
        <p className="alert alert--error" role="alert">
          {error}
        </p>
      ) : null}
      {aiPreview ? (
        <div className="alert" role="status">
          <p>Não era formato do TrainingPeaks, então a IA leu assim. Confira antes de salvar:</p>
          <ul>
            {aiPreview.blocks.map((block, i) =>
              block.kind === 'repeat' ? (
                <li key={i}>
                  {block.repeat}x: {block.steps.map((s) => describeStep(s, sport)).join(' + ')}
                </li>
              ) : (
                <li key={i}>{describeStep(block, sport)}</li>
              ),
            )}
          </ul>
          <p>
            Total: {formatKm(aiPreview.total_distance_m)}. Se algo estiver errado, ajuste o texto.
          </p>
        </div>
      ) : null}
      {saved ? (
        <p className="alert alert--success" role="status">
          ✓ {SPORT_LABEL[saved.sport]} de {formatWeekday(saved.scheduled_date)} salvo:{' '}
          {formatKm(saved.total_distance_m)}
          {estimate ? `, cerca de ${formatClock(estimate[0])} a ${formatClock(estimate[1])}` : ''}.
          Cole o próximo treino ou feche.
        </p>
      ) : null}
      <button type="submit" className="button" disabled={busy !== null}>
        {busy === 'reading'
          ? 'Lendo com IA...'
          : busy === 'saving'
            ? 'Salvando...'
            : aiPreview
              ? 'Confirmar e salvar'
              : 'Salvar treino'}
      </button>
    </form>
  )
}
