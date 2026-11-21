"""Leitura de atividades realizadas a partir de arquivos FIT, GPX e TCX."""

from __future__ import annotations

import datetime as dt
import io
import math
import xml.etree.ElementTree as ET
from pathlib import PurePath

import fitdecode
import gpxpy

from app.schemas.activity import Lap, ParsedActivity

SUPPORTED_EXTENSIONS = (".fit", ".gpx", ".tcx")


class ActivityParseError(ValueError):
    pass


def parse_activity_file(file_name: str, content: bytes) -> ParsedActivity:
    extension = PurePath(file_name).suffix.lower()
    try:
        if extension == ".fit":
            return parse_fit(content)
        if extension == ".gpx":
            return parse_gpx(content)
        if extension == ".tcx":
            return parse_tcx(content)
    except ActivityParseError:
        raise
    except Exception as exc:  # arquivos corrompidos geram erros variados nas libs
        raise ActivityParseError(f"não foi possível ler o arquivo: {exc}") from exc
    raise ActivityParseError(
        f"formato não suportado: {extension or 'sem extensão'} "
        f"(use {', '.join(SUPPORTED_EXTENSIONS)})"
    )


def _aware(value: dt.datetime | None) -> dt.datetime | None:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=dt.UTC)


# --------------------------------------------------------------------- FIT


def _field(frame: fitdecode.FitDataMessage, name: str):
    return frame.get_value(name, fallback=None)


def parse_fit(content: bytes) -> ParsedActivity:
    session: dict | None = None
    laps: list[Lap] = []

    with fitdecode.FitReader(io.BytesIO(content)) as reader:
        for frame in reader:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue
            if frame.name == "lap":
                laps.append(
                    Lap(
                        start_time=_aware(_field(frame, "start_time")),
                        distance_m=float(_field(frame, "total_distance") or 0),
                        duration_s=float(
                            _field(frame, "total_timer_time")
                            or _field(frame, "total_elapsed_time")
                            or 0
                        ),
                        avg_hr=_field(frame, "avg_heart_rate"),
                        max_hr=_field(frame, "max_heart_rate"),
                    )
                )
            elif frame.name == "session" and session is None:
                session = {
                    "start_time": _aware(_field(frame, "start_time")),
                    "distance_m": _field(frame, "total_distance"),
                    "duration_s": _field(frame, "total_timer_time")
                    or _field(frame, "total_elapsed_time"),
                    "avg_hr": _field(frame, "avg_heart_rate"),
                    "max_hr": _field(frame, "max_heart_rate"),
                    "sport": _field(frame, "sport"),
                }

    if session is None:
        if not laps:
            raise ActivityParseError("arquivo FIT sem sessão nem voltas")
        session = {
            "start_time": laps[0].start_time,
            "distance_m": sum(lap.distance_m for lap in laps),
            "duration_s": sum(lap.duration_s for lap in laps),
            "avg_hr": None,
            "max_hr": max((lap.max_hr for lap in laps if lap.max_hr), default=None),
            "sport": None,
        }
    if session["start_time"] is None:
        raise ActivityParseError("arquivo FIT sem horário de início")

    return ParsedActivity(
        start_time=session["start_time"],
        distance_m=float(session["distance_m"] or 0),
        duration_s=float(session["duration_s"] or 0),
        avg_hr=session["avg_hr"],
        max_hr=session["max_hr"],
        sport=str(session["sport"]) if session["sport"] is not None else None,
        laps=laps,
    )


# --------------------------------------------------------------------- GPX


def _gpx_heart_rate(point: gpxpy.gpx.GPXTrackPoint) -> float | None:
    for extension in point.extensions:
        for element in extension.iter():
            if element.tag.split("}")[-1] == "hr" and element.text:
                return float(element.text)
    return None


def parse_gpx(content: bytes) -> ParsedActivity:
    gpx = gpxpy.parse(content.decode("utf-8"))
    points = [p for track in gpx.tracks for seg in track.segments for p in seg.points]
    if len(points) < 2 or points[0].time is None:
        raise ActivityParseError("arquivo GPX sem pontos com horário")

    distance = gpx.length_3d() if any(p.elevation is not None for p in points) else gpx.length_2d()
    moving = gpx.get_moving_data()
    duration = moving.moving_time if moving and moving.moving_time else None
    if not duration:
        duration = (points[-1].time - points[0].time).total_seconds()

    heart_rates = [hr for p in points if (hr := _gpx_heart_rate(p)) is not None]
    sport = gpx.tracks[0].type if gpx.tracks else None

    return ParsedActivity(
        start_time=_aware(points[0].time),
        distance_m=float(distance),
        duration_s=float(duration),
        avg_hr=round(sum(heart_rates) / len(heart_rates), 1) if heart_rates else None,
        max_hr=max(heart_rates) if heart_rates else None,
        sport=sport,
        laps=[],
    )


# --------------------------------------------------------------------- TCX


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _child(element: ET.Element, name: str) -> ET.Element | None:
    for child in element:
        if _local(child.tag) == name:
            return child
    return None


def _child_float(element: ET.Element, *path: str) -> float | None:
    current: ET.Element | None = element
    for name in path:
        if current is None:
            return None
        current = _child(current, name)
    if current is None or current.text is None:
        return None
    value = float(current.text)
    return None if math.isnan(value) else value


def _parse_iso(value: str) -> dt.datetime:
    return _aware(dt.datetime.fromisoformat(value.replace("Z", "+00:00")))


def parse_tcx(content: bytes) -> ParsedActivity:
    root = ET.fromstring(content)
    activity = next((el for el in root.iter() if _local(el.tag) == "Activity"), None)
    if activity is None:
        raise ActivityParseError("arquivo TCX sem atividade")

    laps: list[Lap] = []
    weighted_hr = 0.0
    hr_time = 0.0
    for lap_el in (el for el in activity if _local(el.tag) == "Lap"):
        duration = _child_float(lap_el, "TotalTimeSeconds") or 0.0
        avg_hr = _child_float(lap_el, "AverageHeartRateBpm", "Value")
        laps.append(
            Lap(
                start_time=_parse_iso(lap_el.attrib["StartTime"])
                if "StartTime" in lap_el.attrib
                else None,
                distance_m=_child_float(lap_el, "DistanceMeters") or 0.0,
                duration_s=duration,
                avg_hr=avg_hr,
                max_hr=_child_float(lap_el, "MaximumHeartRateBpm", "Value"),
            )
        )
        if avg_hr is not None:
            weighted_hr += avg_hr * duration
            hr_time += duration

    if not laps:
        raise ActivityParseError("arquivo TCX sem voltas")

    id_el = _child(activity, "Id")
    start = _parse_iso(id_el.text) if id_el is not None and id_el.text else laps[0].start_time
    if start is None:
        raise ActivityParseError("arquivo TCX sem horário de início")

    max_hrs = [lap.max_hr for lap in laps if lap.max_hr is not None]
    return ParsedActivity(
        start_time=start,
        distance_m=sum(lap.distance_m for lap in laps),
        duration_s=sum(lap.duration_s for lap in laps),
        avg_hr=round(weighted_hr / hr_time, 1) if hr_time else None,
        max_hr=max(max_hrs) if max_hrs else None,
        sport=activity.attrib.get("Sport"),
        laps=laps,
    )
