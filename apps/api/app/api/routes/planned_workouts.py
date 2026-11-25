import datetime as dt

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AppSettings, DbSession, LLMClient
from app.models import PlannedWorkout
from app.schemas.plan import (
    PlannedWorkoutCreate,
    PlannedWorkoutOut,
    PlannedWorkoutStructure,
    PlanTextIn,
)
from app.services.llm import LLMError
from app.services.plan_ai import parse_workouts_with_ai
from app.services.plan_parser import PlanParseError, parse_workouts
from app.services.planned_workouts import create_planned_workout, list_planned_workouts

router = APIRouter(prefix="/planned-workouts", tags=["treinos planejados"])


@router.post("/preview", response_model=list[PlannedWorkoutStructure])
def preview(
    payload: PlanTextIn, settings: AppSettings, client: LLMClient
) -> list[PlannedWorkoutStructure]:
    """Interpreta o texto sem salvar, para conferência: TrainingPeaks primeiro, IA se falhar."""
    try:
        return parse_workouts(payload.text)
    except PlanParseError as parse_error:
        try:
            return parse_workouts_with_ai(client, settings.anthropic_model, payload.text)
        except LLMError as exc:
            detail = f"{parse_error}. A IA também não conseguiu ler: {exc}"
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail) from exc


@router.post("", response_model=PlannedWorkoutOut, status_code=status.HTTP_201_CREATED)
def create(payload: PlannedWorkoutCreate, db: DbSession) -> PlannedWorkout:
    try:
        return create_planned_workout(db, payload)
    except PlanParseError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc


@router.get("", response_model=list[PlannedWorkoutOut])
def list_(
    db: DbSession, start: dt.date | None = None, end: dt.date | None = None
) -> list[PlannedWorkout]:
    return list_planned_workouts(db, start, end)


@router.get("/{workout_id}", response_model=PlannedWorkoutOut)
def get(workout_id: int, db: DbSession) -> PlannedWorkout:
    workout = db.get(PlannedWorkout, workout_id)
    if workout is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Treino planejado não encontrado")
    return workout


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(workout_id: int, db: DbSession) -> None:
    workout = db.get(PlannedWorkout, workout_id)
    if workout is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Treino planejado não encontrado")
    db.delete(workout)
    db.commit()
