import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiStatus } from './ApiStatus'

describe('ApiStatus', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('mostra a API como online quando o health responde', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok', version: '0.1.0' }),
      }),
    )

    render(<ApiStatus />)

    expect(await screen.findByText('API online (v0.1.0)')).toBeInTheDocument()
  })

  it('mostra a API como indisponível quando a requisição falha', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('network')))

    render(<ApiStatus />)

    expect(await screen.findByText('API indisponível')).toBeInTheDocument()
  })
})
