from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Activity
from app.schemas.activity import ParsedActivity


def find_by_start_time(db: Session, start_time: dt.datetime) -> Activity | None:
    return db.scalar(select(Activity).where(Activity.start_time == start_time))


def save_activity(
    db: Session,
    parsed: ParsedActivity,
    *,
    source: str,
    timezone: str,
    file_name: str | None = None,
    external_id: str | None = None,
) -> Activity | None:
    """Salva a atividade; retorna None se já existir uma com o mesmo início."""
    if find_by_start_time(db, parsed.start_time) is not None:
        return None
    activity = Activity(
        source=source,
        external_id=external_id,
        file_name=file_name,
        start_time=parsed.start_time,
        activity_date=parsed.start_time.astimezone(ZoneInfo(timezone)).date(),
        distance_m=parsed.distance_m,
        duration_s=parsed.duration_s,
        avg_hr=parsed.avg_hr,
        max_hr=parsed.max_hr,
        sport=parsed.sport,
        laps=[lap.model_dump(mode="json", exclude_computed_fields=True) for lap in parsed.laps],
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def list_activities(
    db: Session, start: dt.date | None = None, end: dt.date | None = None
) -> list[Activity]:
    query = select(Activity).order_by(Activity.start_time)
    if start:
        query = query.where(Activity.activity_date >= start)
    if end:
        query = query.where(Activity.activity_date <= end)
    return list(db.scalars(query))
