from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.activity import Sport


class TodayRecommendation(BaseModel):
    readiness: Literal["alta", "moderada", "baixa"]
    sport: Sport | Literal["rest"]
    title: str = Field(description="Nome curto do treino, ex.: Rodagem leve Z2")
    duration_min: int | None = Field(description="Duração sugerida em minutos; null no descanso")
    workout: str = Field(description="Como fazer o treino: passos, zonas, pace ou potência")
    reason: str = Field(description="Por que este treino hoje, citando os números da Garmin")


class TodayRecommendationOut(TodayRecommendation):
    # Fontes da Garmin que não responderam, para a tela avisar.
    unavailable: list[str]
