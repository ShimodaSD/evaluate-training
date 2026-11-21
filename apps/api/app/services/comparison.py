"""Comparação entre o treino planejado e a atividade realizada.

Regras:
- Se a atividade tem uma volta (lap) por passo do treino (o padrão quando o
  treino estruturado é executado no relógio Garmin), cada passo é comparado
  com sua volta. Uma volta extra no final (relógio parado depois) é ignorada.
- Caso contrário, compara-se apenas o total; o pace médio só é avaliado
  quando o treino tem um único passo de corrida (ex.: rodagem contínua).
- Aderência (0 a 100) = média entre a nota de distância
  (1 - |realizado/planejado - 1|) e a fração de passos dentro do pace alvo.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.schemas.activity import Lap, pace_from
from app.schemas.comparison import PaceStatus, StepComparison, WorkoutComparison
from app.schemas.plan import PlannedStep, PlannedWorkoutStructure

PACE_TOLERANCE_S = 5
DONE_THRESHOLD_PCT = 80.0


class ActivityLike(Protocol):
    distance_m: float
    duration_s: float
    laps: Sequence[Lap]


def classify_pace(
    pace: float | None, low: int | None, high: int | None, tolerance: int = PACE_TOLERANCE_S
) -> PaceStatus | None:
    """Classifica o pace realizado em relação à faixa alvo (low = mais rápido)."""
    if pace is None or low is None:
        return None
    high = high if high is not None else low
    if pace < low - tolerance:
        return "fast"
    if pace > high + tolerance:
        return "slow"
    return "in_range"


def _aligned_laps(steps: list[PlannedStep], laps: Sequence[Lap]) -> Sequence[Lap] | None:
    if len(steps) <= 1 or not laps:
        return None
    if len(laps) == len(steps):
        return laps
    if len(laps) == len(steps) + 1:
        return laps[: len(steps)]
    return None


def _compare_steps(steps: list[PlannedStep], laps: Sequence[Lap]) -> list[StepComparison]:
    result = []
    for index, (step, lap) in enumerate(zip(steps, laps, strict=True)):
        pace = pace_from(lap.distance_m, lap.duration_s)
        result.append(
            StepComparison(
                index=index,
                name=step.name,
                intensity=step.intensity,
                is_rest=step.is_rest,
                planned_distance_m=step.distance_m,
                planned_duration_s=step.duration_s,
                target_pace_min_s_per_km=step.pace_min_s_per_km,
                target_pace_max_s_per_km=step.pace_max_s_per_km,
                actual_distance_m=lap.distance_m,
                actual_duration_s=lap.duration_s,
                actual_pace_s_per_km=pace,
                actual_avg_hr=lap.avg_hr,
                pace_status=None
                if step.is_rest
                else classify_pace(pace, step.pace_min_s_per_km, step.pace_max_s_per_km),
            )
        )
    return result


def compare_workout(plan: PlannedWorkoutStructure, activity: ActivityLike) -> WorkoutComparison:
    steps = plan.expanded_steps()
    planned_distance = plan.total_distance_m
    distance_ratio = activity.distance_m / planned_distance if planned_distance else None
    overall_pace = pace_from(activity.distance_m, activity.duration_s)

    step_comparisons: list[StepComparison] | None = None
    pace_status: PaceStatus | None = None
    pace_ratio: float | None = None

    laps = _aligned_laps(steps, activity.laps)
    if laps is not None:
        step_comparisons = _compare_steps(steps, laps)
        evaluated = [s for s in step_comparisons if s.pace_status is not None]
        if evaluated:
            pace_ratio = sum(s.pace_status == "in_range" for s in evaluated) / len(evaluated)
    else:
        running = [s for s in steps if not s.is_rest]
        if len(running) == 1:
            target = running[0]
            pace_status = classify_pace(
                overall_pace, target.pace_min_s_per_km, target.pace_max_s_per_km
            )
            if pace_status is not None:
                pace_ratio = 1.0 if pace_status == "in_range" else 0.0

    scores = []
    if distance_ratio is not None:
        scores.append(max(0.0, 1 - abs(distance_ratio - 1)))
    if pace_ratio is not None:
        scores.append(pace_ratio)
    adherence = round(100 * sum(scores) / len(scores), 1) if scores else 0.0

    return WorkoutComparison(
        planned_distance_m=planned_distance,
        actual_distance_m=activity.distance_m,
        distance_ratio=round(distance_ratio, 3) if distance_ratio is not None else None,
        planned_duration_s=plan.estimated_duration_s,
        actual_duration_s=activity.duration_s,
        actual_pace_s_per_km=overall_pace,
        pace_status=pace_status,
        pace_in_range_ratio=round(pace_ratio, 3) if pace_ratio is not None else None,
        steps=step_comparisons,
        adherence_pct=adherence,
        status="done" if adherence >= DONE_THRESHOLD_PCT else "partial",
    )
