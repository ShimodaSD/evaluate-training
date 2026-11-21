import datetime as dt

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import AppSettings, DbSession
from app.models import Activity
from app.schemas.activity import ActivityOut, UploadResult
from app.services.activities import list_activities, save_activity
from app.services.activity_parser import ActivityParseError, parse_activity_file

router = APIRouter(prefix="/activities", tags=["atividades realizadas"])

MAX_FILE_BYTES = 25 * 1024 * 1024


@router.post("/upload", response_model=UploadResult)
async def upload(files: list[UploadFile], db: DbSession, settings: AppSettings) -> UploadResult:
    """Recebe arquivos FIT, GPX ou TCX. Atividades já existentes são ignoradas."""
    created: list[ActivityOut] = []
    skipped: list[str] = []
    errors: dict[str, str] = {}
    for upload_file in files:
        name = upload_file.filename or "arquivo"
        content = await upload_file.read(MAX_FILE_BYTES + 1)
        if len(content) > MAX_FILE_BYTES:
            errors[name] = "arquivo maior que 25 MB"
            continue
        try:
            parsed = parse_activity_file(name, content)
        except ActivityParseError as exc:
            errors[name] = str(exc)
            continue
        activity = save_activity(
            db, parsed, source="upload", timezone=settings.timezone, file_name=name
        )
        if activity is None:
            skipped.append(name)
        else:
            created.append(ActivityOut.model_validate(activity))
    return UploadResult(created=created, skipped=skipped, errors=errors)


@router.get("", response_model=list[ActivityOut])
def list_(
    db: DbSession, start: dt.date | None = None, end: dt.date | None = None
) -> list[Activity]:
    return list_activities(db, start, end)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(activity_id: int, db: DbSession) -> None:
    activity = db.get(Activity, activity_id)
    if activity is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Atividade não encontrada")
    db.delete(activity)
    db.commit()
