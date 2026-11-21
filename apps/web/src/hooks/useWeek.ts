import useSWR from 'swr'
import { fetcher, weekKey } from '../api/client'
import type { WeekSummary } from '../api/types'

export function useWeek(day: string) {
  return useSWR<WeekSummary, Error>(weekKey(day), fetcher, { keepPreviousData: true })
}
