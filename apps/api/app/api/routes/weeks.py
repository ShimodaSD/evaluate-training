import datetime as dt

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AppSettings, DbSession, LLMClient
from app.schemas.comparison import WeekAnalysis, WeekSummary
from app.services.coach import analyze_week
from app.services.llm import LLMError
from app.services.week import build_week_summary

router = APIRouter(prefix="/weeks", tags=["resumo semanal"])


@router.get("/{day}", response_model=WeekSummary)
def week_summary(day: dt.date, db: DbSession, settings: AppSettings) -> WeekSummary:
    """Planejado x realizado da semana de treino (início em WEEK_START_WEEKDAY) que contém o dia."""
    return build_week_summary(db, day, settings.week_start_weekday)


@router.post("/{day}/analysis", response_model=WeekAnalysis)
def week_analysis(
    day: dt.date,
    db: DbSession,
    settings: AppSettings,
    client: LLMClient,
) -> WeekAnalysis:
    """Avaliação da semana escrita pela IA a partir do planejado x realizado."""
    week = build_week_summary(db, day, settings.week_start_weekday)
    if not week.sports:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Não há treinos nesta semana")
    try:
        return WeekAnalysis(analysis=analyze_week(client, settings.anthropic_model, week))
    except LLMError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
