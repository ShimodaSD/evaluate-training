import datetime as dt

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.comparison import WeekSummary
from app.services.week import build_week_summary

router = APIRouter(prefix="/weeks", tags=["resumo semanal"])


@router.get("/{day}", response_model=WeekSummary)
def week_summary(day: dt.date, db: DbSession) -> WeekSummary:
    """Planejado x realizado da semana (segunda a domingo) que contém o dia informado."""
    return build_week_summary(db, day)
