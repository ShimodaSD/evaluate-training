import datetime as dt

import httpx2 as httpx  # o SDK da Anthropic usa o httpx2
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_llm_client
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
    llm.answer("Semana sólida.\n- Rodagem no pace.")

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 200
    assert response.json() == {"analysis": "Semana sólida.\n- Rodagem no pace."}
    (call,) = llm.requests
    assert call["model"] == "claude-haiku-5-5"
    assert "Ciclismo: só manter a Zona 2" in call["system"]
    assert '"week_start":"2026-11-16"' in call["messages"][0]["content"]
    assert '"adherence_pct":100.0' in call["messages"][0]["content"]


def test_semana_vazia_nao_chama_o_claude(client: TestClient, llm: FakeLLM) -> None:
    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 400
    assert llm.requests == []


def _error(status: int, message: str) -> httpx.Response:
    return httpx.Response(
        status, json={"type": "error", "error": {"type": "x", "message": message}}
    )


@pytest.mark.parametrize(
    ("reply", "detail"),
    [
        (httpx.ConnectError("offline"), "sem conexão"),
        (_error(401, "bad key"), "ANTHROPIC_API_KEY inválida"),
        (_error(400, "Your credit balance is too low"), "sem créditos"),
        (_error(429, "slow down"), "limite de uso"),
    ],
)
def test_erros_do_claude_viram_502(client: TestClient, llm: FakeLLM, reply, detail: str) -> None:
    _seed_week(client)
    llm.reply = reply

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 502
    assert detail in response.json()["detail"]


@pytest.mark.parametrize(
    ("text", "stop_reason", "detail"),
    [
        ("", "refusal", "não conseguiu"),
        ("  ", "end_turn", "vazia"),
        ("Sem", "max_tokens", "incompleta"),
    ],
)
def test_respostas_inuteis_viram_502(
    client: TestClient, llm: FakeLLM, text: str, stop_reason: str, detail: str
) -> None:
    _seed_week(client)
    llm.answer(text, stop_reason)

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 502
    assert detail in response.json()["detail"]


def test_sem_chave_configurada(client: TestClient) -> None:
    _seed_week(client)
    client.app.dependency_overrides.pop(get_llm_client)

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 502
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]
