import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_llm_client
from app.core.config import Settings, get_settings
from tests.test_plan_ai import AI_WORKOUT, COACH_TEXT


class FakeGemini:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.reply = httpx.Response(500)

    def answer(self, text: str, finish: str = "STOP") -> None:
        candidate = {"content": {"parts": [{"text": text}]}, "finishReason": finish}
        self.reply = httpx.Response(200, json={"candidates": [candidate]})

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.reply


@pytest.fixture
def gemini(client: TestClient) -> FakeGemini:
    fake = FakeGemini()
    client.app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, ai_provider="gemini", gemini_api_key="k", week_start_weekday=0
    )
    client.app.dependency_overrides[get_llm_client] = lambda: httpx.Client(
        base_url="https://gemini/v1beta", transport=httpx.MockTransport(fake.handler)
    )
    return fake


def test_preview_com_gemini_pede_json_no_schema(client: TestClient, gemini: FakeGemini) -> None:
    gemini.answer(json.dumps({"workouts": [AI_WORKOUT]}))

    response = client.post("/api/planned-workouts/preview", json={"text": COACH_TEXT})

    assert response.status_code == 200
    assert response.json()[0]["total_distance_m"] == 1600
    (request,) = gemini.requests
    assert request.url.path == "/v1beta/models/gemini-3.5-flash-lite:generateContent"
    body = json.loads(request.content)
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert "workouts" in body["generationConfig"]["responseJsonSchema"]["properties"]
    assert body["contents"][0]["parts"][0]["text"] == COACH_TEXT


@pytest.mark.parametrize(
    ("reply", "detail"),
    [
        (httpx.Response(400, json={"error": {"message": "API key not valid."}}), "GEMINI_API_KEY"),
        (httpx.Response(429), "limite de uso"),
        (httpx.Response(404), "GEMINI_MODEL"),
        (httpx.Response(200, json={"promptFeedback": {"blockReason": "SAFETY"}}), "não conseguiu"),
    ],
)
def test_erros_do_gemini(client: TestClient, gemini: FakeGemini, reply, detail: str) -> None:
    gemini.reply = reply

    response = client.post("/api/planned-workouts/preview", json={"text": COACH_TEXT})

    assert response.status_code == 422
    assert detail in response.json()["detail"]


def test_resposta_cortada_do_gemini(client: TestClient, gemini: FakeGemini) -> None:
    gemini.answer('{"workouts": [', finish="MAX_TOKENS")

    response = client.post("/api/planned-workouts/preview", json={"text": COACH_TEXT})

    assert "incompleta" in response.json()["detail"]


def test_gemini_e_o_padrao_e_usa_a_chave_do_env() -> None:
    settings = Settings(_env_file=None, gemini_api_key="minha-chave")
    (client,) = list(get_llm_client(settings))
    assert isinstance(client, httpx.Client)
    assert client.headers["x-goog-api-key"] == "minha-chave"
    assert settings.ai_model == "gemini-3.5-flash-lite"
    assert list(get_llm_client(Settings(_env_file=None))) == [None]
