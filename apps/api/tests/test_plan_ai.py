import json

from fastapi.testclient import TestClient

from tests.conftest import FakeLLM

COACH_TEXT = "Aquece 10min leve, depois 4x 400m forte (1:40/km? não, 4:10/km) com 1min parado"
AI_WORKOUT = {
    "blocks": [
        {"kind": "step", "name": "Aquecimento", "duration_s": 600},
        {
            "kind": "repeat",
            "repeat": 4,
            "steps": [
                {
                    "kind": "step",
                    "name": "Tiro",
                    "distance_m": 400,
                    "pace_min_s_per_km": 250,
                    "pace_max_s_per_km": 250,
                },
                {"kind": "step", "name": "Pausa", "duration_s": 60, "is_rest": True},
            ],
        },
    ]
}


def test_preview_usa_a_ia_quando_o_parser_falha(client: TestClient, llm: FakeLLM) -> None:
    llm.answer(json.dumps({"workouts": [AI_WORKOUT]}))

    response = client.post("/api/planned-workouts/preview", json={"text": COACH_TEXT})

    assert response.status_code == 200
    (workout,) = response.json()
    assert workout["total_distance_m"] == 1600
    (call,) = llm.requests
    assert call["output_config"]["format"]["type"] == "json_schema"
    assert call["messages"][0]["content"] == COACH_TEXT


def test_preview_do_trainingpeaks_nao_chama_a_ia(
    client: TestClient, llm: FakeLLM, week_text: str
) -> None:
    assert client.post("/api/planned-workouts/preview", json={"text": week_text}).is_success
    assert llm.requests == []


def test_preview_rejeita_passo_sem_tamanho_vindo_da_ia(client: TestClient, llm: FakeLLM) -> None:
    llm.answer(json.dumps({"workouts": [{"blocks": [{"kind": "step", "name": "Rodagem"}]}]}))

    response = client.post("/api/planned-workouts/preview", json={"text": COACH_TEXT})

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "Linha 1" in detail
    assert "A IA também não conseguiu ler: o Claude devolveu o treino fora do formato" in detail


def test_salva_a_estrutura_conferida_sem_reler_o_texto(client: TestClient, llm: FakeLLM) -> None:
    response = client.post(
        "/api/planned-workouts",
        json={"scheduled_date": "2026-11-17", "text": COACH_TEXT, "structure": AI_WORKOUT},
    )

    assert response.status_code == 201
    assert response.json()["total_distance_m"] == 1600
    assert response.json()["raw_text"] == COACH_TEXT
    assert llm.requests == []
