import datetime as dt

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.conftest import FakeLLM
from tests.factories import build_fit


def _seed_week(client: TestClient) -> None:
    client.post(
        "/api/planned-workouts",
        json={"scheduled_date": "2026-11-17", "text": "1. Active\n8.00 km @ 05:19-05:35 min/km"},
    )
    fit = build_fit(dt.datetime(2026, 11, 17, 9, tzinfo=dt.UTC), [(1000, 325, 150)] * 8)
    client.post("/api/activities/upload", files=[("files", ("rodagem.fit", fit))])


def test_analise_envia_a_semana_e_devolve_o_texto(client: TestClient, llm: FakeLLM) -> None:
    _seed_week(client)
    llm.answer("<think>pensando...</think>\nSemana sólida.\n- Rodagem no pace.")

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 200
    assert response.json() == {"analysis": "Semana sólida.\n- Rodagem no pace."}
    (call,) = llm.requests
    assert call["model"] == "deepseek-r1:8b"
    assert '"week_start":"2026-11-16"' in call["messages"][1]["content"]
    assert '"adherence_pct":100.0' in call["messages"][1]["content"]


def test_semana_vazia_nao_chama_a_ia(client: TestClient, llm: FakeLLM) -> None:
    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 400
    assert llm.requests == []


@pytest.mark.parametrize(
    ("reply", "detail"),
    [
        (httpx.ConnectError("offline"), "o Ollama está rodando?"),
        (httpx.ReadTimeout("lento"), "demorou demais"),
        (httpx.Response(401), "AI_API_KEY inválida"),
        (httpx.Response(402), "sem saldo"),
        (httpx.Response(404), "ollama pull deepseek-r1:8b"),
        (httpx.Response(200, json={"choices": [{"message": {"content": " "}}]}), "vazia"),
        (httpx.Response(200, json={"erro": 1}), "formato inesperado"),
    ],
)
def test_erros_da_ia_viram_502(client: TestClient, llm: FakeLLM, reply, detail: str) -> None:
    _seed_week(client)
    llm.reply = reply

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 502
    assert detail in response.json()["detail"]
