import datetime as dt

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AppSettings, DbSession
from app.integrations.garmin.client import GarminClient, GarminError
from app.schemas.activity import UploadResult
from app.services.garmin_sync import sync_garmin

router = APIRouter(prefix="/garmin", tags=["garmin"])


@router.post("/sync", response_model=UploadResult)
def sync(
    db: DbSession,
    settings: AppSettings,
    start: dt.date | None = None,
    end: dt.date | None = None,
) -> UploadResult:
    """Importa corridas, pedais e natações do Garmin Connect (padrão: últimos 7 dias)."""
    if not settings.garmin_personal_api_key:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Configure GARMIN_PERSONAL_API_KEY no arquivo .env"
        )
    end = end or dt.date.today()
    start = start or end - dt.timedelta(days=7)
    try:
        with GarminClient(
            settings.garmin_personal_api_key.get_secret_value(), settings.garmin_base_url
        ) as client:
            return sync_garmin(db, client, start, end, settings.timezone)
    except GarminError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
