import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { jsonResponse, mockFetch } from '../test/render'
import { ActivityUpload } from './ActivityUpload'

describe('ActivityUpload', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('envia os arquivos e mostra o que foi criado, ignorado e com erro', async () => {
    const fetchMock = mockFetch({
      '/api/activities/upload': () =>
        jsonResponse({
          created: [
            {
              id: 1,
              source: 'upload',
              file_name: 'a.fit',
              start_time: '2026-11-17T09:00:00Z',
              activity_date: '2026-11-17',
              distance_m: 8000,
              duration_s: 2600,
              avg_hr: null,
              max_hr: null,
              pace_s_per_km: 325,
            },
          ],
          skipped: ['b.fit'],
          errors: { 'c.txt': 'formato não suportado' },
        }),
    })
    const onUploaded = vi.fn()
    const user = userEvent.setup({ applyAccept: false })
    const { container } = render(<ActivityUpload onUploaded={onUploaded} />)

    const input = container.querySelector('input[type="file"]') as HTMLInputElement
    await user.upload(input, [new File(['x'], 'a.fit'), new File(['y'], 'b.fit')])

    expect(await screen.findByText(/8 km · 5:25\/km/)).toBeInTheDocument()
    expect(screen.getByText('Já enviados antes: b.fit')).toBeInTheDocument()
    expect(screen.getByText('c.txt: formato não suportado')).toBeInTheDocument()
    expect(onUploaded).toHaveBeenCalledOnce()
    const form = fetchMock.mock.calls[0][1]?.body as FormData
    expect(form.getAll('files')).toHaveLength(2)
  })

  it('sincroniza com o Garmin e mostra o erro de configuração', async () => {
    const fetchMock = mockFetch({
      '/api/garmin/sync': () =>
        jsonResponse({ detail: 'Configure GARMIN_PERSONAL_API_KEY no arquivo .env' }, 400),
    })
    const user = userEvent.setup()
    render(<ActivityUpload onUploaded={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: /Sincronizar atividades do Garmin/ }))

    expect(await screen.findByRole('alert')).toHaveTextContent('GARMIN_PERSONAL_API_KEY')
    expect(fetchMock).toHaveBeenCalledWith('/api/garmin/sync', { method: 'POST' })
  })
})
