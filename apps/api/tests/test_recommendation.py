import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes import recommendation as recommendation_route
from app.core.config import Settings, get_settings
from app.integrations.garmin.client import GarminClient
from tests.conftest import FakeLLM

BASE = "https://garmin.test"
AI_ANSWER = {
    "readiness": "moderada",
    "sport": "bike",
    "title": "Pedal Z2",
    "duration_min": 60,
    "workout": "60 min em Z2, potência estável.",
    "reason": "HRV 42 ms, abaixo da base.",
}


calls: list[httpx.Request] = []


def _garmin(request: httpx.Request) -> httpx.Response:
    calls.append(request)
    path = request.url.path
    if path.endswith("/token"):
        return httpx.Response(200, text="jwt")
    if path.startswith("/hrv-service/"):
        return httpx.Response(200, json={"hrvSummaries": [{"lastNightAvg": 42}]})
    if path.endswith("/search/activities"):
        return httpx.Response(
            200, json=[{"activityName": "Rodagem", "activityTrainingLoad": 80, "lapCount": 8}]
        )
    return httpx.Response(404)


@pytest.fixture
def garmin(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        _env_file=None,
        garmin_personal_api_key="chave",
        garmin_base_url=BASE,
        ai_provider="anthropic",
    )
    client.app.dependency_overrides[get_settings] = lambda: settings
    monkeypatch.setattr(
        recommendation_route,
        "GarminClient",
        lambda key, url: GarminClient(key, url, transport=httpx.MockTransport(_garmin)),
    )


def test_recomenda_com_o_que_a_garmin_tem(client: TestClient, llm: FakeLLM, garmin) -> None:
    llm.answer(json.dumps(AI_ANSWER))

    response = client.post("/api/recommendation/today", params={"sport": "run"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Pedal Z2"
    assert "hrv" not in body["unavailable"] and "sono" in body["unavailable"]
    (call,) = llm.requests
    content = call["messages"][0]["content"]
    assert "lastNightAvg" in content and "activityTrainingLoad" in content
    assert "lapCount" not in content  # só os campos de carga das atividades
    assert '"semana"' in content and '"esporte": "run"' in content
    assert "Nunca" in call["system"] and "recomende intensidade na bike" in call["system"]


def test_dias_passados_vem_do_banco(client: TestClient, llm: FakeLLM, garmin) -> None:
    llm.answer(json.dumps(AI_ANSWER))
    client.post("/api/recommendation/today")
    calls.clear()

    client.post("/api/recommendation/today")

    hrv_days = [r.url.path for r in calls if r.url.path.startswith("/hrv-service/")]
    assert len(hrv_days) == 1  # só hoje é buscado de novo
    assert llm.requests[-1]["messages"][0]["content"].count("lastNightAvg") == 7


def test_sem_garmin_configurada(client: TestClient, llm: FakeLLM) -> None:
    response = client.post("/api/recommendation/today")

    assert response.status_code == 400
    assert llm.requests == []
