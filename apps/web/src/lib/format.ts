/** Formatação de distâncias, paces e datas para exibição em pt-BR. */

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

export function formatPace(secondsPerKm: number | null): string {
  return secondsPerKm == null ? '—' : `${formatClock(secondsPerKm)}/km`
}

export function formatPaceRange(min: number | null, max: number | null): string {
  if (min == null) return '—'
  return max == null || max === min ? formatPace(min) : `${formatClock(min)}–${formatClock(max)}/km`
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
