import datetime as dt

import pytest

from app.schemas.activity import Lap, ParsedActivity
from app.services.comparison import classify_pace, compare_workout
from app.services.plan_parser import parse_workout, parse_workouts

START = dt.datetime(2026, 11, 16, 9, 0, tzinfo=dt.UTC)


def _activity(laps: list[tuple[float, float]]) -> ParsedActivity:
    return ParsedActivity(
        start_time=START,
        distance_m=sum(d for d, _ in laps),
        duration_s=sum(t for _, t in laps),
        laps=[Lap(distance_m=d, duration_s=t) for d, t in laps],
    )


@pytest.mark.parametrize(
    ("pace", "expected"),
    [(300, "in_range"), (290, "in_range"), (280, "fast"), (330, "in_range"), (340, "slow")],
)
def test_classify_pace_com_tolerancia(pace: float, expected: str) -> None:
    assert classify_pace(pace, 295, 330) == expected


def test_classify_pace_sem_alvo() -> None:
    assert classify_pace(300, None, None) is None


def test_rodagem_continua_no_pace_e_distancia(week_text: str) -> None:
    plan = parse_workouts(week_text)[0]  # 8 km @ 05:19-05:35
    activity = _activity([(1000, 325)] * 8)  # voltas automáticas a cada km

    result = compare_workout(plan, activity)

    assert result.steps is None
    assert result.pace_status == "in_range"
    assert result.distance_ratio == 1
    assert result.adherence_pct == 100
    assert result.status == "done"


def test_rodagem_mais_curta_e_rapida(week_text: str) -> None:
    plan = parse_workouts(week_text)[0]
    activity = _activity([(6000, 6 * 290)])

    result = compare_workout(plan, activity)

    assert result.pace_status == "fast"
    assert result.distance_ratio == 0.75
    assert result.adherence_pct == pytest.approx(37.5)
    assert result.status == "partial"


def test_intervalado_compara_volta_a_volta(week_text: str) -> None:
    plan = parse_workouts(week_text)[2]  # 2 km + 2x(3 km forte + 1 km leve) + 1 km
    laps = [
        (2000, 2 * 360),  # aquecimento ok
        (3000, 3 * 260),  # forte ok (04:15-04:28)
        (1000, 360),  # leve ok
        (3000, 3 * 280),  # forte lento (04:40)
        (1000, 360),  # leve ok
        (1000, 360),  # desaquecimento ok
        (5, 3),  # volta extra ao parar o relógio
    ]

    result = compare_workout(plan, _activity(laps))

    assert result.steps is not None
    assert [s.pace_status for s in result.steps] == [
        "in_range",
        "in_range",
        "in_range",
        "slow",
        "in_range",
        "in_range",
    ]
    assert result.pace_in_range_ratio == pytest.approx(5 / 6, abs=0.001)
    assert result.status == "done"


def test_pausa_nao_conta_no_pace() -> None:
    plan = parse_workout(
        "1. Repeat 2 times\n"
        "   1. Tiro\n0.40 km @ 04:00 min/km\n"
        "   2. Pausa — Passiva\n1:00 @ 00:00 min/km"
    )
    laps = [(400, 96), (0, 60), (400, 96), (0, 60)]

    result = compare_workout(plan, _activity(laps))

    assert result.steps is not None
    assert [s.pace_status for s in result.steps] == ["in_range", None, "in_range", None]
    assert result.pace_in_range_ratio == 1
