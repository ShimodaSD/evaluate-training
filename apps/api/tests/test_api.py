import datetime as dt

from fastapi.testclient import TestClient
from fit_tool.profile.profile_type import Sport

from app.core.config import Settings
from tests.factories import build_fit, build_tcx

MONDAY = dt.date(2026, 11, 16)


def _continuous_text() -> str:
    return "1. Active\n8.00 km @ 05:19-05:35 min/km\nZona 2"


def test_preview_devolve_estrutura_sem_salvar(client: TestClient, week_text: str) -> None:
    response = client.post("/api/planned-workouts/preview", json={"text": week_text})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert body[1]["total_distance_m"] == 11000
    assert client.get("/api/planned-workouts").json() == []


def test_preview_com_texto_invalido(client: TestClient) -> None:
    response = client.post("/api/planned-workouts/preview", json={"text": "bla"})

    assert response.status_code == 422
    assert "Linha 1" in response.json()["detail"]


def test_cria_lista_e_remove_treino_planejado(client: TestClient) -> None:
    created = client.post(
        "/api/planned-workouts",
        json={"scheduled_date": "2026-11-17", "title": "Rodagem", "text": _continuous_text()},
    )
    assert created.status_code == 201
    workout = created.json()
    assert workout["total_distance_m"] == 8000
    assert workout["structure"]["blocks"][0]["pace_min_s_per_km"] == 319

    listed = client.get(
        "/api/planned-workouts", params={"start": "2026-11-16", "end": "2026-11-22"}
    )
    assert [w["id"] for w in listed.json()] == [workout["id"]]
    assert client.get("/api/planned-workouts", params={"start": "2026-11-18"}).json() == []

    assert client.delete(f"/api/planned-workouts/{workout['id']}").status_code == 204
    assert client.get(f"/api/planned-workouts/{workout['id']}").status_code == 404


def test_criar_com_mais_de_um_treino_falha(client: TestClient, week_text: str) -> None:
    response = client.post(
        "/api/planned-workouts", json={"scheduled_date": "2026-11-17", "text": week_text}
    )

    assert response.status_code == 422


def test_upload_de_atividades(client: TestClient) -> None:
    start = dt.datetime(2026, 11, 17, 9, 0, tzinfo=dt.UTC)
    fit = build_fit(start, [(8000, 8 * 325, 150)])
    tcx = build_tcx(start + dt.timedelta(days=1), [(5000, 1500, 145)])

    response = client.post(
        "/api/activities/upload",
        files=[
            ("files", ("rodagem.fit", fit, "application/octet-stream")),
            ("files", ("leve.tcx", tcx, "application/xml")),
            ("files", ("notas.txt", b"oi", "text/plain")),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert [a["file_name"] for a in body["created"]] == ["rodagem.fit", "leve.tcx"]
    assert body["created"][0]["activity_date"] == "2026-11-17"
    assert body["created"][0]["pace_s_per_km"] == 325
    assert "notas.txt" in body["errors"]

    again = client.post(
        "/api/activities/upload",
        files=[("files", ("rodagem.fit", fit, "application/octet-stream"))],
    )
    assert again.json()["skipped"] == ["rodagem.fit"]
    assert len(client.get("/api/activities").json()) == 2


def test_dia_da_atividade_usa_o_fuso_configurado(client: TestClient) -> None:
    # 01:30 UTC do dia 18 ainda é noite do dia 17 em São Paulo
    start = dt.datetime(2026, 11, 18, 1, 30, tzinfo=dt.UTC)
    fit = build_fit(start, [(5000, 1500, 140)])

    response = client.post("/api/activities/upload", files=[("files", ("noite.fit", fit))])

    assert response.json()["created"][0]["activity_date"] == "2026-11-17"


def test_resumo_semanal_planejado_x_realizado(client: TestClient, week_text: str) -> None:
    client.post(
        "/api/planned-workouts", json={"scheduled_date": "2026-11-17", "text": _continuous_text()}
    )
    interval_text = week_text.split("\n\n\n")[2]
    client.post(
        "/api/planned-workouts", json={"scheduled_date": "2026-11-19", "text": interval_text}
    )
    client.post(
        "/api/planned-workouts", json={"scheduled_date": "2026-11-21", "text": _continuous_text()}
    )

    rodagem = build_fit(dt.datetime(2026, 11, 17, 9, 0, tzinfo=dt.UTC), [(1000, 325, 150)] * 8)
    extra = build_fit(dt.datetime(2026, 11, 18, 9, 0, tzinfo=dt.UTC), [(3000, 1080, 130)])
    client.post(
        "/api/activities/upload",
        files=[("files", ("rodagem.fit", rodagem)), ("files", ("extra.fit", extra))],
    )

    response = client.get("/api/weeks/2026-11-20")

    assert response.status_code == 200
    week = response.json()
    assert week["week_start"] == "2026-11-16"
    assert week["week_end"] == "2026-11-22"
    assert week["planned_workouts"] == 3
    assert week["completed_workouts"] == 1
    assert week["sports"] == [
        {
            "sport": "run",
            "planned_distance_m": 27000,
            "actual_distance_m": 11000,
            "actual_duration_s": 8 * 325 + 1080,
            "planned_workouts": 3,
            "completed_workouts": 1,
        }
    ]
    assert week["actual_duration_s"] == 8 * 325 + 1080

    days = {d["date"]: d for d in week["days"]}
    tuesday = days["2026-11-17"]["workouts"][0]
    assert tuesday["status"] == "done"
    assert tuesday["comparison"]["adherence_pct"] == 100
    assert len(days["2026-11-18"]["extra_activities"]) == 1
    # Quinta e sábado ficam "missed" ou "planned" conforme a data atual.
    assert days["2026-11-19"]["workouts"][0]["status"] in {"missed", "planned"}


def test_semana_casa_cada_treino_com_atividade_do_mesmo_esporte(client: TestClient) -> None:
    bike_text = "1. Endurance\n1:00:00 @ 28-32 km/h"
    client.post(
        "/api/planned-workouts",
        json={"scheduled_date": "2026-11-17", "sport": "bike", "text": bike_text},
    )
    client.post(
        "/api/planned-workouts", json={"scheduled_date": "2026-11-17", "text": _continuous_text()}
    )
    # O pedal tem distância mais próxima dos 8 km da corrida, mas só pode casar com o plano de bike.
    bike = build_fit(
        dt.datetime(2026, 11, 17, 18, 0, tzinfo=dt.UTC), [(9000, 1080, 130)], sport=Sport.CYCLING
    )
    run = build_fit(dt.datetime(2026, 11, 17, 9, 0, tzinfo=dt.UTC), [(8000, 2600, 150)])
    client.post(
        "/api/activities/upload",
        files=[("files", ("pedal.fit", bike)), ("files", ("run.fit", run))],
    )

    week = client.get("/api/weeks/2026-11-17").json()

    tuesday = next(d for d in week["days"] if d["date"] == "2026-11-17")
    by_sport = {w["planned"]["sport"]: w for w in tuesday["workouts"]}
    assert by_sport["bike"]["activity"]["file_name"] == "pedal.fit"
    assert by_sport["bike"]["comparison"]["pace_status"] == "in_range"  # 30 km/h
    assert by_sport["run"]["activity"]["file_name"] == "run.fit"
    assert [s["sport"] for s in week["sports"]] == ["run", "bike"]
    assert week["actual_duration_s"] == 2600 + 1080


def test_treino_no_rolo_avaliado_pela_potencia(client: TestClient) -> None:
    text = "1. Aquecimento\n10:00 @ 100-130 W\n2. Sweet spot\n20:00 @ 200-215 W"
    client.post(
        "/api/planned-workouts",
        json={"scheduled_date": "2026-11-22", "sport": "bike", "text": text},
    )
    # Rolo: velocidade virtual; o segundo bloco ficou 20 W abaixo do alvo.
    ride = build_fit(
        dt.datetime(2026, 11, 22, 21, 0, tzinfo=dt.UTC),
        [(4000, 600, 115), (8000, 1200, 135)],
        sport=Sport.CYCLING,
        powers=[120, 180],
    )
    client.post("/api/activities/upload", files=[("files", ("rolo.fit", ride))])

    week = client.get("/api/weeks/2026-11-22").json()

    sunday = next(d for d in week["days"] if d["date"] == "2026-11-22")
    (workout,) = sunday["workouts"]
    assert workout["activity"]["avg_power_w"] == 150
    steps = workout["comparison"]["steps"]
    assert [s["actual_avg_power_w"] for s in steps] == [120, 180]
    assert [s["pace_status"] for s in steps] == ["in_range", "slow"]
    assert workout["comparison"]["distance_ratio"] is None  # só duração: nota só da potência
    assert workout["comparison"]["adherence_pct"] == 50


def test_semana_comeca_no_dia_configurado(client: TestClient, settings: Settings) -> None:
    settings.week_start_weekday = 1  # terça

    week = client.get("/api/weeks/2026-11-16").json()  # segunda é o fim da semana anterior

    assert (week["week_start"], week["week_end"]) == ("2026-11-10", "2026-11-16")
    assert week["days"][0]["date"] == "2026-11-10"
