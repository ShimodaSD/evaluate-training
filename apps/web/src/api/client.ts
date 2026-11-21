import type { PlannedWorkout, PlannedWorkoutStructure, UploadResult, WeekSummary } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class ApiError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown } | null
    const detail = typeof body?.detail === 'string' ? body.detail : `Erro ${response.status}`
    throw new ApiError(detail)
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}

const json = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const fetcher = <T>(path: string) => request<T>(path)

export const weekKey = (day: string) => `/weeks/${day}`

export const previewPlan = (text: string) =>
  request<PlannedWorkoutStructure[]>('/planned-workouts/preview', json({ text }))

export const createPlannedWorkout = (scheduled_date: string, text: string) =>
  request<PlannedWorkout>('/planned-workouts', json({ scheduled_date, text }))

export const deletePlannedWorkout = (id: number) =>
  request<void>(`/planned-workouts/${id}`, { method: 'DELETE' })

export function uploadActivities(files: File[]) {
  const form = new FormData()
  for (const file of files) form.append('files', file)
  return request<UploadResult>('/activities/upload', { method: 'POST', body: form })
}

export const analyzeWeek = (day: string) =>
  request<{ analysis: string }>(`/weeks/${day}/analysis`, { method: 'POST' })

export const syncGarmin = () => request<UploadResult>('/garmin/sync', { method: 'POST' })

export type { WeekSummary }
