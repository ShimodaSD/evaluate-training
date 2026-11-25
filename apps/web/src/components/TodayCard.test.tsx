import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonResponse, mockFetch } from '../test/render'
import { TodayCard } from './TodayCard'

describe('TodayCard', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('pede a recomendação e mostra treino, prontidão e motivo', async () => {
    const fetchMock = mockFetch({
      '/api/recommendation/today': () =>
        jsonResponse({
          readiness: 'baixa',
          sport: 'bike',
          title: 'Pedal regenerativo',
          duration_min: 40,
          workout: '40 min em Z1.',
          reason: 'HRV 38 ms, abaixo da base.',
          unavailable: ['vo2max'],
        }),
    })
    const user = userEvent.setup()
    render(<TodayCard />)

    await user.click(screen.getByRole('button', { name: 'Recomendar treino' }))

    expect(await screen.findByText(/Pedal regenerativo/)).toHaveTextContent('40 min')
    expect(screen.getByText(/Prontidão baixa/)).toBeInTheDocument()
    expect(screen.getByText(/HRV 38 ms/)).toBeInTheDocument()
    expect(screen.getByText(/Sem dados da Garmin de: vo2max/)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/recommendation/today?sport=bike', {
      method: 'POST',
    })
  })

  it('mostra o erro quando a Garmin não está configurada', async () => {
    mockFetch({
      '/api/recommendation/today': () =>
        jsonResponse({ detail: 'Configure GARMIN_PERSONAL_API_KEY no arquivo .env' }, 400),
    })
    const user = userEvent.setup()
    render(<TodayCard />)

    await user.click(screen.getByRole('button', { name: 'Recomendar treino' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('GARMIN_PERSONAL_API_KEY')
  })
})
