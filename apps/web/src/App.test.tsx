import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { emptyWeek, weekWithWorkouts } from './test/fixtures'
import { jsonResponse, mockFetch, renderWithSWR } from './test/render'

describe('App', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 10, 20, 12))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('mostra o estado vazio com uma ação única quando não há plano', async () => {
    mockFetch({ '/api/weeks/': () => jsonResponse(emptyWeek()) })

    renderWithSWR(<App />)

    expect(await screen.findByText('Comece colando o treino da semana')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Colar treino planejado' })).toBeInTheDocument()
  })

  it('mostra aderência, treino pendente e lista da semana', async () => {
    mockFetch({ '/api/weeks/': () => jsonResponse(weekWithWorkouts()) })

    renderWithSWR(<App />)

    expect(await screen.findByText('50%')).toBeInTheDocument()
    expect(screen.getByText(/1 de 2 treinos feitos · 43:20 de treino/)).toBeInTheDocument()
    expect(screen.getByText('Corrida: 8 km de 16 km')).toBeInTheDocument()
    expect(screen.getByText('Falta registrar')).toBeInTheDocument()
    expect(screen.getByText('Cumprido')).toBeInTheDocument()
    expect(screen.getByText('Não feito')).toBeInTheDocument()
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('navega para a semana anterior', async () => {
    const fetchMock = mockFetch({ '/api/weeks/': () => jsonResponse(weekWithWorkouts()) })
    const user = userEvent.setup()

    renderWithSWR(<App />)
    await user.click(await screen.findByRole('button', { name: 'Semana anterior' }))

    expect(fetchMock).toHaveBeenCalledWith('/api/weeks/2026-11-09', undefined)
  })

  it('mostra erro quando a API falha', async () => {
    mockFetch({ '/api/weeks/': () => jsonResponse({ detail: 'fora do ar' }, 500) })

    renderWithSWR(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('fora do ar')
  })
})
