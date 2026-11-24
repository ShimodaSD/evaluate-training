import datetime as dt

import pytest

from app.services.activities import normalize_sport
from app.services.activity_parser import ActivityParseError, parse_activity_file
from tests.factories import build_fit, build_gpx, build_tcx

START = dt.datetime(2026, 11, 16, 9, 0, tzinfo=dt.UTC)


def test_le_fit_com_sessao_e_voltas() -> None:
    content = build_fit(START, [(2000, 700, 140), (1000, 250, 170)])

    activity = parse_activity_file("treino.FIT", content)

    assert activity.start_time == START
    assert activity.distance_m == 3000
    assert activity.duration_s == 950
    assert activity.sport == "running"
    assert len(activity.laps) == 2
    assert activity.laps[1].pace_s_per_km == pytest.approx(250)
    assert activity.laps[1].avg_hr == 170


def test_le_fit_sem_sessao_somando_voltas() -> None:
    content = build_fit(START, [(1000, 300, 150), (1000, 320, 155)], include_session=False)

    activity = parse_activity_file("treino.fit", content)

    assert activity.distance_m == 2000
    assert activity.duration_s == 620
    assert activity.start_time == START


def test_le_tcx() -> None:
    content = build_tcx(START, [(1000, 300, 150), (1000, 330, 160)])

    activity = parse_activity_file("treino.tcx", content)

    assert activity.start_time == START
    assert activity.distance_m == 2000
    assert activity.duration_s == 630
    assert activity.avg_hr == pytest.approx((150 * 300 + 160 * 330) / 630, abs=0.1)
    assert activity.max_hr == 170
    assert activity.sport == "Running"
    assert len(activity.laps) == 2


def test_le_gpx_com_frequencia_cardiaca() -> None:
    content = build_gpx(START, points=11, step_m=100, step_s=30)

    activity = parse_activity_file("treino.gpx", content)

    assert activity.start_time == START
    assert activity.distance_m == pytest.approx(1000, rel=0.01)
    assert activity.duration_s == pytest.approx(300, abs=1)
    assert activity.avg_hr == 145
    assert activity.max_hr == 150
    assert activity.laps == []


def test_formato_nao_suportado() -> None:
    with pytest.raises(ActivityParseError, match="formato não suportado"):
        parse_activity_file("treino.csv", b"a,b")


def test_arquivo_corrompido() -> None:
    with pytest.raises(ActivityParseError, match="não foi possível ler"):
        parse_activity_file("treino.fit", b"isso nao e um fit")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("running", "run"),
        ("trail_running", "run"),
        ("Biking", "bike"),
        ("cycling", "bike"),
        ("virtual_ride", "bike"),
        ("lap_swimming", "swim"),
        ("strength_training", "other"),
        (None, "run"),
    ],
)
def test_normaliza_o_esporte(raw: str | None, expected: str) -> None:
    assert normalize_sport(raw) == expected
