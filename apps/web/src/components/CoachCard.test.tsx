import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonResponse, mockFetch } from '../test/render'
import { CoachCard } from './CoachCard'

describe('CoachCard', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('pede a avaliação da semana e mostra o texto', async () => {
    const fetchMock = mockFetch({
      '/api/weeks/2026-11-16/analysis': () =>
        jsonResponse({ analysis: 'Semana sólida.\n- Rodagem no pace.' }),
    })
    const user = userEvent.setup()
    render(<CoachCard day="2026-11-16" />)

    await user.click(screen.getByRole('button', { name: 'Avaliar semana' }))

    expect(await screen.findByText(/Semana sólida/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Avaliar de novo' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/weeks/2026-11-16/analysis', { method: 'POST' })
  })

  it('mostra o erro quando a chave não está configurada', async () => {
    mockFetch({
      '/api/weeks/': () =>
        jsonResponse({ detail: 'Configure ANTHROPIC_API_KEY no arquivo .env' }, 400),
    })
    const user = userEvent.setup()
    render(<CoachCard day="2026-11-16" />)

    await user.click(screen.getByRole('button', { name: 'Avaliar semana' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('ANTHROPIC_API_KEY')
  })
})
