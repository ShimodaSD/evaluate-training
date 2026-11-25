import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { continuous } from '../test/fixtures'
import { jsonResponse, mockFetch } from '../test/render'
import { PlanForm } from './PlanForm'

const LABEL = 'Treino (TrainingPeaks ou qualquer formato)'

describe('PlanForm', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('salva o treino, mostra o resumo e avança o dia', async () => {
    const fetchMock = mockFetch({ '/api/planned-workouts': () => jsonResponse(continuous, 201) })
    const onSaved = vi.fn()
    const user = userEvent.setup()

    render(<PlanForm defaultDate="2026-11-17" onSaved={onSaved} />)
    await user.type(screen.getByLabelText(LABEL), '1. Active')
    await user.click(screen.getByRole('button', { name: 'Salvar treino' }))

    expect(await screen.findByRole('status')).toHaveTextContent('8 km, cerca de 42:32 a 44:40')
    expect(onSaved).toHaveBeenCalledOnce()
    expect(screen.getByLabelText('Dia do treino')).toHaveValue('2026-11-18')
    const body = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(body).toEqual({ scheduled_date: '2026-11-17', text: '1. Active', sport: 'run' })
  })

  it('envia o esporte escolhido', async () => {
    const fetchMock = mockFetch({
      '/api/planned-workouts': () => jsonResponse({ ...continuous, sport: 'bike' }, 201),
    })
    const user = userEvent.setup()

    render(<PlanForm defaultDate="2026-11-17" onSaved={vi.fn()} />)
    await user.selectOptions(screen.getByLabelText('Esporte'), 'Ciclismo')
    await user.type(screen.getByLabelText(LABEL), '1. Endurance')
    await user.click(screen.getByRole('button', { name: 'Salvar treino' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Ciclismo de')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body)).sport).toBe('bike')
  })

  it('mostra o erro do parser sem perder o texto', async () => {
    mockFetch({
      '/api/planned-workouts': () =>
        jsonResponse({ detail: 'Linha 2: linha não reconhecida' }, 422),
    })
    const user = userEvent.setup()

    render(<PlanForm defaultDate="2026-11-17" onSaved={vi.fn()} />)
    await user.type(screen.getByLabelText(LABEL), 'texto')
    await user.click(screen.getByRole('button', { name: 'Salvar treino' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Linha 2')
    expect(screen.getByLabelText(LABEL)).toHaveValue('texto')
  })

  it('quando o parser falha, mostra o treino lido pela IA e salva a estrutura conferida', async () => {
    let created = 0
    const fetchMock = mockFetch({
      '/api/planned-workouts/preview': () => jsonResponse([continuous.structure]),
      '/api/planned-workouts': () =>
        created++ === 0
          ? jsonResponse({ detail: 'Linha 1: linha não reconhecida' }, 422)
          : jsonResponse(continuous, 201),
    })
    const user = userEvent.setup()

    render(<PlanForm defaultDate="2026-11-17" onSaved={vi.fn()} />)
    await user.type(screen.getByLabelText(LABEL), 'rodagem de 8k')
    await user.click(screen.getByRole('button', { name: 'Salvar treino' }))

    expect(await screen.findByRole('status')).toHaveTextContent('a IA leu assim')
    await user.click(screen.getByRole('button', { name: 'Confirmar e salvar' }))

    expect(await screen.findByRole('status')).toHaveTextContent('8 km')
    const body = JSON.parse(String(fetchMock.mock.calls[2][1]?.body))
    expect(body.structure).toEqual(continuous.structure)
  })
})
