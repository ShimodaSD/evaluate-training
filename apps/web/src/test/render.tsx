import { render } from '@testing-library/react'
import type { ReactElement } from 'react'
import { SWRConfig } from 'swr'
import { vi } from 'vitest'

/** Renderiza com cache do SWR isolado por teste. */
export function renderWithSWR(ui: ReactElement) {
  return render(
    <SWRConfig value={{ provider: () => new Map(), dedupingInterval: 0 }}>{ui}</SWRConfig>,
  )
}

export function jsonResponse(body: unknown, status = 200) {
  return { ok: status < 400, status, json: async () => body } as Response
}

/** Mock de fetch que responde por rota (prefixo da URL). */
export function mockFetch(routes: Record<string, () => Response>) {
  const fn = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
    const url = String(input)
    const match = Object.keys(routes).find((prefix) => url.startsWith(prefix))
    if (!match) throw new Error(`rota não mockada: ${url}`)
    return routes[match]()
  })
  vi.stubGlobal('fetch', fn)
  return fn
}
