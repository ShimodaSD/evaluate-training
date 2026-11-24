from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel

from app.schemas.activity import ActivityOut, Sport
from app.schemas.plan import PlannedWorkoutOut

PaceStatus = Literal["in_range", "fast", "slow"]
WorkoutStatus = Literal["done", "partial", "missed", "planned"]


class StepComparison(BaseModel):
    index: int
    name: str
    intensity: str | None
    is_rest: bool
    planned_distance_m: float | None
    planned_duration_s: int | None
    target_pace_min_s_per_km: float | None
    target_pace_max_s_per_km: float | None
    actual_distance_m: float
    actual_duration_s: float
    actual_pace_s_per_km: float | None
    actual_avg_hr: float | None
    pace_status: PaceStatus | None


class WorkoutComparison(BaseModel):
    planned_distance_m: float
    actual_distance_m: float
    distance_ratio: float | None
    planned_duration_s: tuple[float, float] | None
    actual_duration_s: float
    actual_pace_s_per_km: float | None
    pace_status: PaceStatus | None
    pace_in_range_ratio: float | None
    steps: list[StepComparison] | None
    adherence_pct: float
    status: WorkoutStatus


class PlannedVsDone(BaseModel):
    planned: PlannedWorkoutOut
    activity: ActivityOut | None
    comparison: WorkoutComparison | None
    status: WorkoutStatus


class DaySummary(BaseModel):
    date: dt.date
    workouts: list[PlannedVsDone]
    extra_activities: list[ActivityOut]


class SportTotals(BaseModel):
    sport: Sport
    planned_distance_m: float
    actual_distance_m: float
    actual_duration_s: float
    planned_workouts: int
    completed_workouts: int


class WeekSummary(BaseModel):
    week_start: dt.date
    week_end: dt.date
    planned_workouts: int
    completed_workouts: int
    adherence_pct: float | None
    # Carga combinada: tempo é a única medida que soma corrida, ciclismo e natação.
    actual_duration_s: float
    sports: list[SportTotals]
    days: list[DaySummary]


class WeekAnalysis(BaseModel):
    analysis: str
