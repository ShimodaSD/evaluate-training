/** Formatação de distâncias, paces e datas para exibição em pt-BR. */
import type { Sport } from '../api/types'

export const SPORT_LABEL: Record<Sport, string> = {
  run: 'Corrida',
  bike: 'Ciclismo',
  swim: 'Natação',
  other: 'Outro',
}

export function formatKm(meters: number): string {
  const km = meters / 1000
  return `${km.toLocaleString('pt-BR', { maximumFractionDigits: km < 10 ? 2 : 1 })} km`
}

export function formatClock(totalSeconds: number): string {
  const s = Math.round(totalSeconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = String(s % 60).padStart(2, '0')
  return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${sec}` : `${m}:${sec}`
}

const speed = (secondsPerKm: number) =>
  (3600 / secondsPerKm).toLocaleString('pt-BR', { maximumFractionDigits: 1 })

/** Pace em s/km exibido como o esporte usa: min/km, km/h ou min/100 m. */
export function formatPace(secondsPerKm: number | null, sport: Sport = 'run'): string {
  if (secondsPerKm == null) return '—'
  if (sport === 'bike') return `${speed(secondsPerKm)} km/h`
  if (sport === 'swim') return `${formatClock(secondsPerKm / 10)}/100m`
  return `${formatClock(secondsPerKm)}/km`
}

export function formatPaceRange(min: number | null, max: number | null, sport: Sport = 'run') {
  if (min == null) return '—'
  if (max == null || max === min) return formatPace(min, sport)
  // No ciclismo o pace mais lento (max) é a menor velocidade.
  if (sport === 'bike') return `${speed(max)}–${speed(min)} km/h`
  if (sport === 'swim') return `${formatClock(min / 10)}–${formatClock(max / 10)}/100m`
  return `${formatClock(min)}–${formatClock(max)}/km`
}

/** Datas ISO (AAAA-MM-DD) tratadas como datas locais, sem fuso. */
export function parseDate(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function toIsoDate(date: Date): string {
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${m}-${d}`
}

export function addDays(iso: string, days: number): string {
  const date = parseDate(iso)
  date.setDate(date.getDate() + days)
  return toIsoDate(date)
}

const weekdayFormat = new Intl.DateTimeFormat('pt-BR', { weekday: 'short', day: '2-digit' })
const shortFormat = new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short' })

export const formatWeekday = (iso: string) => weekdayFormat.format(parseDate(iso)).replace('.', '')
export const formatShortDate = (iso: string) => shortFormat.format(parseDate(iso)).replace('.', '')
