from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PlannedWorkout
from app.schemas.plan import PlannedWorkoutCreate
from app.services.plan_parser import parse_workout


def create_planned_workout(db: Session, data: PlannedWorkoutCreate) -> PlannedWorkout:
    structure = data.structure or parse_workout(data.text)
    workout = PlannedWorkout(
        scheduled_date=data.scheduled_date,
        title=data.title,
        raw_text=data.text.strip(),
        structure=structure.model_dump(mode="json", exclude_computed_fields=True),
        total_distance_m=structure.total_distance_m,
        sport=data.sport,
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout


def list_planned_workouts(
    db: Session, start: dt.date | None = None, end: dt.date | None = None
) -> list[PlannedWorkout]:
    query = select(PlannedWorkout).order_by(PlannedWorkout.scheduled_date, PlannedWorkout.id)
    if start:
        query = query.where(PlannedWorkout.scheduled_date >= start)
    if end:
        query = query.where(PlannedWorkout.scheduled_date <= end)
    return list(db.scalars(query))
