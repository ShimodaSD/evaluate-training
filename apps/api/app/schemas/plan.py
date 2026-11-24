from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.activity import Sport


class PlannedStep(BaseModel):
    """Um passo do treino: distância ou duração, com faixa de pace e zonas."""

    kind: Literal["step"] = "step"
    name: str
    intensity: str | None = None
    distance_m: float | None = None
    duration_s: int | None = None
    pace_min_s_per_km: float | None = Field(default=None, description="Pace mais rápido da faixa")
    pace_max_s_per_km: float | None = Field(default=None, description="Pace mais lento da faixa")
    zone_min: int | None = None
    zone_max: int | None = None
    is_rest: bool = False

    def estimated_duration_range(self) -> tuple[float, float] | None:
        """Faixa de duração estimada em segundos (rápido, lento)."""
        if self.duration_s is not None:
            return float(self.duration_s), float(self.duration_s)
        if self.distance_m is None or self.pace_min_s_per_km is None:
            return None
        km = self.distance_m / 1000
        return km * self.pace_min_s_per_km, km * (self.pace_max_s_per_km or self.pace_min_s_per_km)


class RepeatBlock(BaseModel):
    kind: Literal["repeat"] = "repeat"
    repeat: int = Field(ge=1)
    steps: list[PlannedStep]


class PlannedWorkoutStructure(BaseModel):
    blocks: list[PlannedStep | RepeatBlock]

    def expanded_steps(self) -> list[PlannedStep]:
        """Lista os passos na ordem em que são executados, com repetições expandidas."""
        result: list[PlannedStep] = []
        for block in self.blocks:
            if isinstance(block, RepeatBlock):
                for _ in range(block.repeat):
                    result.extend(block.steps)
            else:
                result.append(block)
        return result

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_distance_m(self) -> float:
        return sum(s.distance_m or 0 for s in self.expanded_steps())

    @computed_field  # type: ignore[prop-decorator]
    @property
    def estimated_duration_s(self) -> tuple[float, float] | None:
        low = high = 0.0
        for step in self.expanded_steps():
            estimate = step.estimated_duration_range()
            if estimate is None:
                return None
            low += estimate[0]
            high += estimate[1]
        return round(low), round(high)


class PlanTextIn(BaseModel):
    text: str = Field(min_length=1)


class PlannedWorkoutCreate(PlanTextIn):
    scheduled_date: dt.date
    title: str | None = Field(default=None, max_length=200)
    sport: Sport = "run"


class PlannedWorkoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scheduled_date: dt.date
    title: str | None
    raw_text: str
    structure: PlannedWorkoutStructure
    total_distance_m: float
    sport: Sport
