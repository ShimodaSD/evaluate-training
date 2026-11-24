"""Resumo semanal: casa cada treino planejado com a atividade do mesmo dia."""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Activity, PlannedWorkout
from app.schemas.activity import ActivityOut, Sport
from app.schemas.comparison import DaySummary, PlannedVsDone, SportTotals, WeekSummary
from app.schemas.plan import PlannedWorkoutOut, PlannedWorkoutStructure
from app.services.activities import list_activities
from app.services.comparison import compare_workout
from app.services.planned_workouts import list_planned_workouts


def week_bounds(day: dt.date, start_weekday: int = 0) -> tuple[dt.date, dt.date]:
    """Semana de 7 dias, começando em start_weekday (0 = segunda), que contém o dia."""
    start = day - dt.timedelta(days=(day.weekday() - start_weekday) % 7)
    return start, start + dt.timedelta(days=6)


def _match_day(
    planned: list[PlannedWorkout], activities: list[Activity], today: dt.date
) -> tuple[list[PlannedVsDone], list[ActivityOut]]:
    remaining = [ActivityOut.model_validate(a) for a in activities]
    results: list[PlannedVsDone] = []
    # Treinos mais longos escolhem primeiro a atividade de distância mais próxima.
    for workout in sorted(planned, key=lambda w: -w.total_distance_m):
        planned_out = PlannedWorkoutOut.model_validate(workout)
        same_sport = [a for a in remaining if a.sport == workout.sport]
        if same_sport:
            activity = min(same_sport, key=lambda a: abs(a.distance_m - workout.total_distance_m))
            remaining.remove(activity)
            comparison = compare_workout(
                PlannedWorkoutStructure.model_validate(workout.structure), activity
            )
            results.append(
                PlannedVsDone(
                    planned=planned_out,
                    activity=activity,
                    comparison=comparison,
                    status=comparison.status,
                )
            )
        else:
            status = "planned" if workout.scheduled_date >= today else "missed"
            results.append(
                PlannedVsDone(planned=planned_out, activity=None, comparison=None, status=status)
            )
    results.sort(key=lambda r: r.planned.id)
    return results, remaining


def build_week_summary(
    db: Session, day: dt.date, start_weekday: int = 0, today: dt.date | None = None
) -> WeekSummary:
    today = today or dt.date.today()
    start, end = week_bounds(day, start_weekday)
    planned_by_day: dict[dt.date, list[PlannedWorkout]] = defaultdict(list)
    for workout in list_planned_workouts(db, start, end):
        planned_by_day[workout.scheduled_date].append(workout)
    activities_by_day: dict[dt.date, list[Activity]] = defaultdict(list)
    for activity in list_activities(db, start, end):
        activities_by_day[activity.activity_date].append(activity)

    days: list[DaySummary] = []
    for offset in range(7):
        date = start + dt.timedelta(days=offset)
        workouts, extras = _match_day(planned_by_day[date], activities_by_day[date], today)
        days.append(DaySummary(date=date, workouts=workouts, extra_activities=extras))

    all_workouts = [w for d in days for w in d.workouts]
    all_activities = [w.activity for w in all_workouts if w.activity] + [
        a for d in days for a in d.extra_activities
    ]
    evaluated = [w.comparison.adherence_pct for w in all_workouts if w.comparison] + [
        0.0 for w in all_workouts if w.status == "missed"
    ]
    return WeekSummary(
        week_start=start,
        week_end=end,
        planned_workouts=len(all_workouts),
        completed_workouts=sum(1 for w in all_workouts if w.activity),
        adherence_pct=round(sum(evaluated) / len(evaluated), 1) if evaluated else None,
        actual_duration_s=sum(a.duration_s for a in all_activities),
        sports=_sport_totals(all_workouts, all_activities),
        days=days,
    )


def _sport_totals(
    workouts: list[PlannedVsDone], activities: list[ActivityOut]
) -> list[SportTotals]:
    sports: list[Sport] = ["run", "bike", "swim", "other"]
    totals = []
    for sport in sports:
        planned = [w for w in workouts if w.planned.sport == sport]
        done = [a for a in activities if a.sport == sport]
        if planned or done:
            totals.append(
                SportTotals(
                    sport=sport,
                    planned_distance_m=sum(w.planned.total_distance_m for w in planned),
                    actual_distance_m=sum(a.distance_m for a in done),
                    actual_duration_s=sum(a.duration_s for a in done),
                    planned_workouts=len(planned),
                    completed_workouts=sum(1 for w in planned if w.activity),
                )
            )
    return totals
