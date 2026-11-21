import { describe, expect, it } from 'vitest'
import { addDays, formatClock, formatKm, formatPace, formatPaceRange } from './format'

describe('format', () => {
  it('formata distâncias em km', () => {
    expect(formatKm(8000)).toBe('8 km')
    expect(formatKm(1200)).toBe('1,2 km')
    expect(formatKm(21097)).toBe('21,1 km')
  })

  it('formata tempos e paces', () => {
    expect(formatClock(319)).toBe('5:19')
    expect(formatClock(3725)).toBe('1:02:05')
    expect(formatPace(325.4)).toBe('5:25/km')
    expect(formatPace(null)).toBe('—')
    expect(formatPaceRange(319, 335)).toBe('5:19–5:35/km')
    expect(formatPaceRange(360, 360)).toBe('6:00/km')
  })

  it('soma dias atravessando o mês', () => {
    expect(addDays('2026-11-30', 1)).toBe('2026-12-01')
    expect(addDays('2026-11-16', -7)).toBe('2026-11-09')
  })
})
