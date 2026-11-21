import datetime as dt
from typing import Annotated

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import AppSettings, DbSession
from app.schemas.comparison import WeekAnalysis, WeekSummary
from app.services.coach import CoachError, analyze_week
from app.services.week import build_week_summary

router = APIRouter(prefix="/weeks", tags=["resumo semanal"])


def get_anthropic_client(settings: AppSettings) -> anthropic.Anthropic:
    if not settings.anthropic_api_key:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Configure ANTHROPIC_API_KEY no arquivo .env"
        )
    return anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value())


@router.get("/{day}", response_model=WeekSummary)
def week_summary(day: dt.date, db: DbSession) -> WeekSummary:
    """Planejado x realizado da semana (segunda a domingo) que contém o dia informado."""
    return build_week_summary(db, day)


@router.post("/{day}/analysis", response_model=WeekAnalysis)
def week_analysis(
    day: dt.date,
    db: DbSession,
    settings: AppSettings,
    client: Annotated[anthropic.Anthropic, Depends(get_anthropic_client)],
) -> WeekAnalysis:
    """Avaliação da semana escrita pelo Claude a partir do planejado x realizado."""
    week = build_week_summary(db, day)
    if week.planned_workouts == 0 and week.actual_distance_m == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Não há treinos nesta semana")
    try:
        return WeekAnalysis(analysis=analyze_week(client, settings.anthropic_model, week))
    except CoachError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
