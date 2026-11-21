export interface HealthResponse {
  status: string
  version: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`)
  if (!response.ok) {
    throw new Error(`Falha ao consultar a API: ${response.status}`)
  }
  return (await response.json()) as HealthResponse
}
