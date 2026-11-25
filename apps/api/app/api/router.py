from fastapi import APIRouter

from app.api.routes import (
    activities,
    garmin,
    health,
    planned_workouts,
    recommendation,
    weeks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(planned_workouts.router)
api_router.include_router(activities.router)
api_router.include_router(weeks.router)
api_router.include_router(garmin.router)
api_router.include_router(recommendation.router)
