import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonResponse, mockFetch } from '../test/render'
import { GarminSync } from './GarminSync'

describe('GarminSync', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('sincroniza, mostra o resumo e atualiza a semana', async () => {
    const fetchMock = mockFetch({
      '/api/garmin/sync': () =>
        jsonResponse({ created: [{}, {}], skipped: ['Rodagem'], errors: { x: 'sem FIT' } }),
    })
    const onSynced = vi.fn()
    const user = userEvent.setup()
    render(<GarminSync onSynced={onSynced} />)

    await user.click(screen.getByRole('button', { name: 'Sincronizar Garmin' }))

    expect(await screen.findByRole('status')).toHaveTextContent(
      '2 novas · 1 já importadas · ✕ 1 com erro',
    )
    expect(onSynced).toHaveBeenCalledOnce()
    expect(fetchMock).toHaveBeenCalledWith('/api/garmin/sync', { method: 'POST' })
  })

  it('mostra o erro de configuração', async () => {
    mockFetch({
      '/api/garmin/sync': () =>
        jsonResponse({ detail: 'Configure GARMIN_PERSONAL_API_KEY no arquivo .env' }, 400),
    })
    const user = userEvent.setup()
    render(<GarminSync onSynced={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: 'Sincronizar Garmin' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('GARMIN_PERSONAL_API_KEY')
  })
})
