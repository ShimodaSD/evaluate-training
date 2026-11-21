from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.garmin.client import GarminClient, GarminError
from app.models import Activity
from app.schemas.activity import ActivityOut, UploadResult
from app.services.activities import save_activity
from app.services.activity_parser import ActivityParseError, parse_fit


def sync_garmin(
    db: Session, client: GarminClient, start: dt.date, end: dt.date, timezone: str
) -> UploadResult:
    """Importa as corridas do período. Atividades já importadas são ignoradas."""
    created: list[ActivityOut] = []
    skipped: list[str] = []
    errors: dict[str, str] = {}
    for summary in client.search_running_activities(start, end):
        activity_id = str(summary["activityId"])
        name = summary.get("activityName") or activity_id
        if db.scalar(select(Activity.id).where(Activity.external_id == activity_id)):
            skipped.append(name)
            continue
        try:
            parsed = parse_fit(client.download_fit(activity_id))
        except (GarminError, ActivityParseError) as exc:
            errors[name] = str(exc)
            continue
        activity = save_activity(
            db,
            parsed,
            source="garmin",
            timezone=timezone,
            file_name=name,
            external_id=activity_id,
        )
        if activity is None:  # mesma corrida já enviada por upload de arquivo
            skipped.append(name)
        else:
            created.append(ActivityOut.model_validate(activity))
    return UploadResult(created=created, skipped=skipped, errors=errors)
