import type { DaySummary, PlannedWorkout, WeekSummary } from '../api/types'
import { addDays } from '../lib/format'

export const WEEK_START = '2026-11-16'

export const continuous: PlannedWorkout = {
  id: 1,
  scheduled_date: '2026-11-17',
  title: null,
  raw_text: '1. Active\n8.00 km @ 05:19-05:35 min/km\nZona 2',
  structure: {
    blocks: [
      {
        kind: 'step',
        name: 'Active',
        intensity: null,
        distance_m: 8000,
        duration_s: null,
        pace_min_s_per_km: 319,
        pace_max_s_per_km: 335,
        power_min_w: null,
        power_max_w: null,
        zone_min: 2,
        zone_max: 2,
        is_rest: false,
      },
    ],
    total_distance_m: 8000,
    estimated_duration_s: [2552, 2680],
  },
  total_distance_m: 8000,
  sport: 'run',
}

export function emptyWeek(): WeekSummary {
  return {
    week_start: WEEK_START,
    week_end: addDays(WEEK_START, 6),
    planned_workouts: 0,
    completed_workouts: 0,
    adherence_pct: null,
    actual_duration_s: 0,
    sports: [],
    days: Array.from({ length: 7 }, (_, i) => ({
      date: addDays(WEEK_START, i),
      workouts: [],
      extra_activities: [],
    })),
  }
}

export function weekWithWorkouts(): WeekSummary {
  const week = emptyWeek()
  const tuesday: DaySummary = {
    date: '2026-11-17',
    extra_activities: [],
    workouts: [
      {
        planned: continuous,
        status: 'done',
        activity: {
          id: 10,
          source: 'upload',
          file_name: 'rodagem.fit',
          start_time: '2026-11-17T09:00:00Z',
          activity_date: '2026-11-17',
          distance_m: 8000,
          duration_s: 2600,
          avg_hr: 150,
          max_hr: 165,
          avg_power_w: null,
          sport: 'run',
          pace_s_per_km: 325,
        },
        comparison: {
          planned_distance_m: 8000,
          actual_distance_m: 8000,
          distance_ratio: 1,
          actual_pace_s_per_km: 325,
          pace_status: 'in_range',
          pace_in_range_ratio: 1,
          steps: null,
          adherence_pct: 100,
          status: 'done',
        },
      },
    ],
  }
  const thursday: DaySummary = {
    date: '2026-11-19',
    extra_activities: [],
    workouts: [
      {
        planned: { ...continuous, id: 2, scheduled_date: '2026-11-19', title: 'Intervalado' },
        status: 'missed',
        activity: null,
        comparison: null,
      },
    ],
  }
  week.days[1] = tuesday
  week.days[3] = thursday
  return {
    ...week,
    planned_workouts: 2,
    completed_workouts: 1,
    adherence_pct: 50,
    actual_duration_s: 2600,
    sports: [
      {
        sport: 'run',
        planned_distance_m: 16000,
        actual_distance_m: 8000,
        actual_duration_s: 2600,
        planned_workouts: 2,
        completed_workouts: 1,
      },
    ],
  }
}
