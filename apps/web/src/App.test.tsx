import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from './App'

describe('App', () => {
  it('renderiza o título do dashboard', () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})))
    render(<App />)
    expect(
      screen.getByRole('heading', { name: 'Avaliação de Treinos de Corrida' }),
    ).toBeInTheDocument()
    vi.unstubAllGlobals()
  })
})
