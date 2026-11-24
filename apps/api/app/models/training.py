from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Date, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PlannedWorkout(Base):
    __tablename__ = "planned_workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scheduled_date: Mapped[dt.date] = mapped_column(Date, index=True)
    title: Mapped[str | None] = mapped_column(String(200))
    raw_text: Mapped[str] = mapped_column(Text)
    structure: Mapped[dict] = mapped_column(JSON)
    total_distance_m: Mapped[float] = mapped_column(Float)
    sport: Mapped[str] = mapped_column(String(10), default="run", server_default="run")
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(20))
    external_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    file_name: Mapped[str | None] = mapped_column(String(255))
    start_time: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), unique=True)
    activity_date: Mapped[dt.date] = mapped_column(Date, index=True)
    distance_m: Mapped[float] = mapped_column(Float)
    duration_s: Mapped[float] = mapped_column(Float)
    avg_hr: Mapped[float | None] = mapped_column(Float)
    max_hr: Mapped[float | None] = mapped_column(Float)
    sport: Mapped[str] = mapped_column(String(50), default="run", server_default="run")
    laps: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
