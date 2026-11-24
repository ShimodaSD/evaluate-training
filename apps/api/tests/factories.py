"""Geradores de arquivos de atividade para os testes."""

from __future__ import annotations

import datetime as dt

from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.messages.lap_message import LapMessage
from fit_tool.profile.messages.session_message import SessionMessage
from fit_tool.profile.profile_type import FileType, Manufacturer, Sport


def _ms(value: dt.datetime) -> int:
    return round(value.timestamp() * 1000)


def build_fit(
    start: dt.datetime,
    laps: list[tuple[float, float, int | None]],
    *,
    include_session: bool = True,
    sport: Sport = Sport.RUNNING,
    powers: list[int] | None = None,
) -> bytes:
    """Cria um FIT com as voltas (distância m, tempo s, FC média)."""
    file_id = FileIdMessage()
    file_id.type = FileType.ACTIVITY
    file_id.manufacturer = Manufacturer.DEVELOPMENT.value
    file_id.product = 0
    file_id.serial_number = 1
    file_id.time_created = _ms(start)

    builder = FitFileBuilder(auto_define=True)
    builder.add(file_id)

    cursor = start
    for index, (distance, duration, hr) in enumerate(laps):
        lap = LapMessage()
        if powers:
            lap.avg_power = powers[index]
        lap.start_time = _ms(cursor)
        lap.timestamp = _ms(cursor + dt.timedelta(seconds=duration))
        lap.total_distance = distance
        lap.total_timer_time = duration
        lap.total_elapsed_time = duration
        if hr is not None:
            lap.avg_heart_rate = hr
            lap.max_heart_rate = hr + 10
        builder.add(lap)
        cursor += dt.timedelta(seconds=duration)

    if include_session:
        session = SessionMessage()
        session.start_time = _ms(start)
        session.timestamp = _ms(cursor)
        session.sport = sport
        if powers:
            session.avg_power = round(sum(powers) / len(powers))
        session.total_distance = sum(lap[0] for lap in laps)
        session.total_timer_time = sum(lap[1] for lap in laps)
        session.total_elapsed_time = sum(lap[1] for lap in laps)
        hrs = [lap[2] for lap in laps if lap[2] is not None]
        if hrs:
            session.avg_heart_rate = round(sum(hrs) / len(hrs))
            session.max_heart_rate = max(hrs) + 10
        builder.add(session)

    return builder.build().to_bytes()


def build_tcx(start: dt.datetime, laps: list[tuple[float, float, int]]) -> bytes:
    lap_xml = []
    cursor = start
    for distance, duration, hr in laps:
        lap_xml.append(
            f"""<Lap StartTime="{cursor.isoformat().replace("+00:00", "Z")}">
              <TotalTimeSeconds>{duration}</TotalTimeSeconds>
              <DistanceMeters>{distance}</DistanceMeters>
              <AverageHeartRateBpm><Value>{hr}</Value></AverageHeartRateBpm>
              <MaximumHeartRateBpm><Value>{hr + 10}</Value></MaximumHeartRateBpm>
            </Lap>"""
        )
        cursor += dt.timedelta(seconds=duration)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities>
    <Activity Sport="Running">
      <Id>{start.isoformat().replace("+00:00", "Z")}</Id>
      {"".join(lap_xml)}
    </Activity>
  </Activities>
</TrainingCenterDatabase>""".encode()


def build_gpx(start: dt.datetime, points: int = 11, step_m: float = 100, step_s: int = 30) -> bytes:
    """Linha reta para o norte com FC nas extensões (~100 m a cada 30 s)."""
    lat_step = step_m / 111_195  # metros por grau de latitude
    rows = []
    for i in range(points):
        time = (start + dt.timedelta(seconds=i * step_s)).isoformat().replace("+00:00", "Z")
        rows.append(
            f"""<trkpt lat="{-23.5 + i * lat_step:.7f}" lon="-46.6">
              <time>{time}</time>
              <extensions><gpxtpx:TrackPointExtension>
                <gpxtpx:hr>{140 + i}</gpxtpx:hr>
              </gpxtpx:TrackPointExtension></extensions>
            </trkpt>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="tests" xmlns="http://www.topografix.com/GPX/1/1"
  xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">
  <trk><type>running</type><trkseg>{"".join(rows)}</trkseg></trk>
</gpx>""".encode()
