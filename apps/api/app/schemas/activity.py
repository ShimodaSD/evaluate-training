from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, computed_field

# Pace sempre em s/km; o esporte só muda a exibição (km/h no ciclismo, /100 m na natação).
Sport = Literal["run", "bike", "swim", "other"]


def pace_from(distance_m: float | None, duration_s: float | None) -> float | None:
    """Pace médio em segundos por km, ou None se não for possível calcular."""
    if not distance_m or not duration_s or distance_m <= 0:
        return None
    return duration_s / (distance_m / 1000)


class Lap(BaseModel):
    start_time: dt.datetime | None = None
    distance_m: float
    duration_s: float
    avg_hr: float | None = None
    max_hr: float | None = None
    avg_power_w: float | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pace_s_per_km(self) -> float | None:
        return pace_from(self.distance_m, self.duration_s)


class ParsedActivity(BaseModel):
    """Atividade realizada, extraída de um arquivo FIT, GPX ou TCX (ou da API Garmin)."""

    start_time: dt.datetime
    distance_m: float
    duration_s: float
    avg_hr: float | None = None
    max_hr: float | None = None
    avg_power_w: float | None = None
    sport: str | None = None
    laps: list[Lap] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pace_s_per_km(self) -> float | None:
        return pace_from(self.distance_m, self.duration_s)


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    file_name: str | None
    start_time: dt.datetime
    activity_date: dt.date
    distance_m: float
    duration_s: float
    avg_hr: float | None
    max_hr: float | None
    avg_power_w: float | None
    sport: Sport
    laps: list[Lap]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pace_s_per_km(self) -> float | None:
        return pace_from(self.distance_m, self.duration_s)


class UploadResult(BaseModel):
    created: list[ActivityOut]
    skipped: list[str]
    errors: dict[str, str]
