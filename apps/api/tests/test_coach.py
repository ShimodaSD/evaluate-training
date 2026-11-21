from types import SimpleNamespace

import httpx
import pytest
from anthropic import AuthenticationError, BadRequestError
from fastapi.testclient import TestClient

from app.api.routes.weeks import get_anthropic_client
from app.core.config import Settings, get_settings
from tests.factories import build_fit


class FakeMessages:
    def __init__(self, response=None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def _response(text: str, stop_reason: str = "end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason,
        content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=text)],
    )


def _use_fake(client: TestClient, messages: FakeMessages) -> None:
    fake = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    client.app.dependency_overrides[get_anthropic_client] = lambda: fake


def _seed_week(client: TestClient) -> None:
    import datetime as dt

    client.post(
        "/api/planned-workouts",
        json={"scheduled_date": "2026-11-17", "text": "1. Active\n8.00 km @ 05:19-05:35 min/km"},
    )
    fit = build_fit(dt.datetime(2026, 11, 17, 9, tzinfo=dt.UTC), [(1000, 325, 150)] * 8)
    client.post("/api/activities/upload", files=[("files", ("rodagem.fit", fit))])


def test_analise_envia_a_semana_e_devolve_o_texto(client: TestClient) -> None:
    _seed_week(client)
    messages = FakeMessages(_response("Semana sólida.\n- Rodagem no pace."))
    _use_fake(client, messages)

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 200
    assert response.json() == {"analysis": "Semana sólida.\n- Rodagem no pace."}
    (call,) = messages.calls
    assert call["model"] == "claude-opus-5-5"
    assert call["fallbacks"] == "default"
    assert '"week_start":"2026-11-16"' in call["messages"][0]["content"]
    assert '"adherence_pct":100.0' in call["messages"][0]["content"]


def test_semana_vazia_nao_chama_o_claude(client: TestClient) -> None:
    messages = FakeMessages(_response("x"))
    _use_fake(client, messages)

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 400
    assert messages.calls == []


@pytest.mark.parametrize(
    ("messages", "detail"),
    [
        (FakeMessages(_response("", stop_reason="refusal")), "não conseguiu avaliar"),
        (FakeMessages(_response("  ")), "resposta vazia"),
        (
            FakeMessages(
                error=AuthenticationError(
                    "bad key",
                    response=httpx.Response(
                        401, request=httpx.Request("POST", "https://api.anthropic.com")
                    ),
                    body=None,
                )
            ),
            "ANTHROPIC_API_KEY inválida",
        ),
        (
            FakeMessages(
                error=BadRequestError(
                    "Your credit balance is too low to access the Anthropic API.",
                    response=httpx.Response(
                        400, request=httpx.Request("POST", "https://api.anthropic.com")
                    ),
                    body=None,
                )
            ),
            "sem créditos",
        ),
    ],
)
def test_erros_do_claude_viram_502(client: TestClient, messages: FakeMessages, detail: str) -> None:
    _seed_week(client)
    _use_fake(client, messages)

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 502
    assert detail in response.json()["detail"]


def test_sem_chave_configurada(client: TestClient) -> None:
    client.app.dependency_overrides[get_settings] = lambda: Settings(
        _env_file=None, anthropic_api_key=None
    )

    response = client.post("/api/weeks/2026-11-19/analysis")

    assert response.status_code == 400
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]
