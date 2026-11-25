/** Paces vêm sempre em s/km; o esporte só muda a exibição. */
export type Sport = 'run' | 'bike' | 'swim' | 'other'
export type PaceStatus = 'in_range' | 'fast' | 'slow'
export type WorkoutStatus = 'done' | 'partial' | 'missed' | 'planned'

export interface PlannedStep {
  kind: 'step'
  name: string
  intensity: string | null
  distance_m: number | null
  duration_s: number | null
  pace_min_s_per_km: number | null
  pace_max_s_per_km: number | null
  power_min_w: number | null
  power_max_w: number | null
  zone_min: number | null
  zone_max: number | null
  is_rest: boolean
}

export interface RepeatBlock {
  kind: 'repeat'
  repeat: number
  steps: PlannedStep[]
}

export interface PlannedWorkoutStructure {
  blocks: (PlannedStep | RepeatBlock)[]
  total_distance_m: number
  estimated_duration_s: [number, number] | null
}

export interface PlannedWorkout {
  id: number
  scheduled_date: string
  title: string | null
  raw_text: string
  structure: PlannedWorkoutStructure
  total_distance_m: number
  sport: Sport
}

export interface Activity {
  id: number
  source: string
  file_name: string | null
  start_time: string
  activity_date: string
  distance_m: number
  duration_s: number
  avg_hr: number | null
  max_hr: number | null
  avg_power_w: number | null
  sport: Sport
  pace_s_per_km: number | null
}

export interface StepComparison {
  index: number
  name: string
  intensity: string | null
  is_rest: boolean
  planned_distance_m: number | null
  planned_duration_s: number | null
  target_pace_min_s_per_km: number | null
  target_pace_max_s_per_km: number | null
  target_power_min_w: number | null
  target_power_max_w: number | null
  actual_distance_m: number
  actual_duration_s: number
  actual_pace_s_per_km: number | null
  actual_avg_hr: number | null
  actual_avg_power_w: number | null
  pace_status: PaceStatus | null
}

export interface WorkoutComparison {
  planned_distance_m: number
  actual_distance_m: number
  distance_ratio: number | null
  actual_pace_s_per_km: number | null
  pace_status: PaceStatus | null
  pace_in_range_ratio: number | null
  steps: StepComparison[] | null
  adherence_pct: number
  status: WorkoutStatus
}

export interface PlannedVsDone {
  planned: PlannedWorkout
  activity: Activity | null
  comparison: WorkoutComparison | null
  status: WorkoutStatus
}

export interface DaySummary {
  date: string
  workouts: PlannedVsDone[]
  extra_activities: Activity[]
}

export interface SportTotals {
  sport: Sport
  planned_distance_m: number
  actual_distance_m: number
  actual_duration_s: number
  planned_workouts: number
  completed_workouts: number
}

export interface WeekSummary {
  week_start: string
  week_end: string
  planned_workouts: number
  completed_workouts: number
  adherence_pct: number | null
  actual_duration_s: number
  sports: SportTotals[]
  days: DaySummary[]
}

export interface UploadResult {
  created: Activity[]
  skipped: string[]
  errors: Record<string, string>
}

export interface TodayRecommendation {
  readiness: 'alta' | 'moderada' | 'baixa'
  sport: Sport | 'rest'
  title: string
  duration_min: number | null
  workout: string
  reason: string
  unavailable: string[]
}
