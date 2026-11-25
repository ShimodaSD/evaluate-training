import datetime as dt
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AppSettings, DbSession, LLMClient
from app.integrations.garmin.client import GarminClient, GarminError
from app.schemas.recommendation import TodayRecommendationOut
from app.services.llm import LLMError
from app.services.recommendation import collect_garmin_stats, recommend_today
from app.services.week import build_week_summary

router = APIRouter(prefix="/recommendation", tags=["recomendação"])


@router.post("/today", response_model=TodayRecommendationOut)
def today_recommendation(
    db: DbSession,
    settings: AppSettings,
    client: LLMClient,
    sport: Literal["run", "bike"] = "bike",
) -> TodayRecommendationOut:
    """Treino de hoje sugerido pela IA com sono, HRV, carga e o plano da semana."""
    if not settings.garmin_configured:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Configure GARMIN_PERSONAL_API_KEY no arquivo .env"
        )
    today = dt.datetime.now(ZoneInfo(settings.timezone)).date()
    try:
        with GarminClient(
            settings.garmin_personal_api_key.get_secret_value(), settings.garmin_base_url
        ) as garmin:
            stats, unavailable = collect_garmin_stats(db, garmin, today)
        week = build_week_summary(db, today, settings.week_start_weekday)
        result = recommend_today(client, settings.ai_model, today, sport, stats, week)
    except (GarminError, LLMError) as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
    return TodayRecommendationOut(**result.model_dump(), unavailable=unavailable)
