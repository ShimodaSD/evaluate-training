import pytest

from app.schemas.plan import PlannedStep, RepeatBlock
from app.services.plan_parser import PlanParseError, parse_workout, parse_workouts


def test_separa_os_tres_treinos_do_exemplo(week_text: str) -> None:
    workouts = parse_workouts(week_text)

    assert len(workouts) == 3
    assert [w.total_distance_m for w in workouts] == [8000, 11000, 11000]


def test_treino_continuo(week_text: str) -> None:
    workout = parse_workouts(week_text)[0]

    (step,) = workout.blocks
    assert isinstance(step, PlannedStep)
    assert step.name == "Active"
    assert step.intensity is None
    assert step.distance_m == 8000
    assert (step.pace_min_s_per_km, step.pace_max_s_per_km) == (319, 335)
    assert (step.zone_min, step.zone_max) == (2, 2)
    assert workout.estimated_duration_s == (2552, 2680)


def test_treino_intervalado_com_repeticoes_e_pausa(week_text: str) -> None:
    workout = parse_workouts(week_text)[1]

    kinds = [b.kind for b in workout.blocks]
    assert kinds == ["step", "repeat", "step", "repeat", "step"]

    activation = workout.blocks[1]
    assert isinstance(activation, RepeatBlock)
    assert activation.repeat == 3
    assert [s.intensity for s in activation.steps] == ["Z4", "Z1"]
    assert activation.steps[0].distance_m == pytest.approx(200)

    main_set = workout.blocks[3]
    assert isinstance(main_set, RepeatBlock)
    series, rest = main_set.steps
    assert series.name == "Série principal"
    assert series.intensity == "VO2"
    assert (series.zone_min, series.zone_max) == (5, 6)
    assert rest.is_rest is True
    assert rest.duration_s == 150
    assert rest.pace_min_s_per_km is None

    assert len(workout.expanded_steps()) == 1 + 3 * 2 + 1 + 5 * 2 + 1


def test_treino_em_ingles(week_text: str) -> None:
    workout = parse_workouts(week_text)[2]

    names = [s.name for s in workout.expanded_steps()]
    assert names == ["Warm up", "Hard", "Easy", "Hard", "Easy", "Cool down"]


def test_parse_workout_exige_um_unico_treino(week_text: str) -> None:
    with pytest.raises(PlanParseError, match="esperado 1 treino"):
        parse_workout(week_text)


def test_aceita_metros_e_virgula() -> None:
    workout = parse_workout("1. Tiro\n400 m @ 03:50-04:00 min/km\n2. Trote\n0,6 km @ 06:00 min/km")

    first, second = workout.expanded_steps()
    assert first.distance_m == 400
    assert second.distance_m == pytest.approx(600)
    assert (second.pace_min_s_per_km, second.pace_max_s_per_km) == (360, 360)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "nenhum treino"),
        ("8.00 km @ 05:19-05:35 min/km", "Linha 1: esperado um passo numerado"),
        ("1. Active\nqualquer coisa", "Linha 2: linha não reconhecida"),
        ("1. Active\nZona 2", "não tem distância nem duração"),
        ("1. Repeat 2 times\n2. Fim\n1.00 km @ 05:00 min/km", "sem passos"),
    ],
)
def test_erros_informam_o_problema(text: str, message: str) -> None:
    with pytest.raises(PlanParseError, match=message):
        parse_workouts(text)
