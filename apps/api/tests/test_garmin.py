import datetime as dt
import io
import zipfile

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.routes import garmin as garmin_route
from app.core.config import Settings, get_settings
from app.integrations.garmin.client import GarminClient
from tests.factories import build_fit

BASE = "https://garmin.test"
START = dt.datetime(2026, 11, 17, 9, 0, tzinfo=dt.UTC)


def _zip(name: str, content: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, content)
    return buffer.getvalue()


class FakeGarmin:
    """Simula a Personal API: token, busca de atividades e download do ZIP."""

    def __init__(self, activities: list[dict], files: dict[int, bytes], token_status: int = 200):
        self.activities = activities
        self.files = files
        self.token_status = token_status
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        if path.endswith("/personal-api-key/token"):
            return httpx.Response(self.token_status, text="jwt-token")
        if path.endswith("/search/activities"):
            start = int(request.url.params["start"])
            limit = int(request.url.params["limit"])
            return httpx.Response(200, json=self.activities[start : start + limit])
        if path.startswith("/download-service/files/activity/"):
            return httpx.Response(200, content=self.files[int(path.rsplit("/", 1)[1])])
        return httpx.Response(404)

    def client(self) -> GarminClient:
        return GarminClient("chave", BASE, transport=httpx.MockTransport(self))


def test_cliente_troca_a_chave_por_token_e_usa_bearer() -> None:
    fake = FakeGarmin([], {})

    with fake.client() as client:
        client.search_running_activities(dt.date(2026, 11, 16), dt.date(2026, 11, 22))

    token_request, search_request = fake.requests
    assert token_request.method == "POST"
    assert token_request.headers["Authorization"] == "ApiKey chave"
    assert search_request.headers["Authorization"] == "Bearer jwt-token"
    assert search_request.url.params["activityType"] == "running"
    assert search_request.url.params["startDate"] == "2026-11-16"


def test_busca_pagina_ate_acabar() -> None:
    fake = FakeGarmin([{"activityId": n} for n in range(150)], {})

    with fake.client() as client:
        result = client.search_running_activities(dt.date(2026, 11, 1), dt.date(2026, 11, 30))

    assert len(result) == 150
    assert [r.url.params["start"] for r in fake.requests[1:]] == ["0", "100"]


def test_download_extrai_o_fit_do_zip() -> None:
    fit = build_fit(START, [(1000, 300, 150)])
    fake = FakeGarmin([], {7: _zip("7_ACTIVITY.fit", fit)})

    with fake.client() as client:
        assert client.download_fit(7) == fit
    assert fake.requests[-1].headers["Accept"] == "*/*"


@pytest.fixture
def garmin_settings(client: TestClient) -> Settings:
    settings = Settings(_env_file=None, garmin_personal_api_key="chave", garmin_base_url=BASE)
    client.app.dependency_overrides[get_settings] = lambda: settings
    return settings


def _patch_transport(monkeypatch: pytest.MonkeyPatch, fake: FakeGarmin) -> None:
    monkeypatch.setattr(
        garmin_route,
        "GarminClient",
        lambda key, url: GarminClient(key, url, transport=httpx.MockTransport(fake)),
    )


def test_sync_importa_e_nao_duplica(
    client: TestClient, garmin_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeGarmin(
        [
            {"activityId": 1, "activityName": "Rodagem"},
            {"activityId": 2, "activityName": "Sem FIT"},
        ],
        {1: _zip("1.fit", build_fit(START, [(1000, 325, 150)] * 8)), 2: _zip("1.txt", b"x")},
    )
    _patch_transport(monkeypatch, fake)

    first = client.post("/api/garmin/sync", params={"start": "2026-11-16", "end": "2026-11-22"})

    assert first.status_code == 200
    body = first.json()
    assert [a["file_name"] for a in body["created"]] == ["Rodagem"]
    assert body["created"][0]["source"] == "garmin"
    assert body["created"][0]["distance_m"] == 8000
    assert "Sem FIT" in body["errors"]

    second = client.post("/api/garmin/sync", params={"start": "2026-11-16", "end": "2026-11-22"})
    assert second.json()["skipped"] == ["Rodagem"]


def test_sync_ignora_corrida_ja_enviada_por_arquivo(
    client: TestClient, garmin_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    fit = build_fit(START, [(5000, 1500, 140)])
    client.post("/api/activities/upload", files=[("files", ("corrida.fit", fit))])
    _patch_transport(monkeypatch, FakeGarmin([{"activityId": 9}], {9: _zip("9.fit", fit)}))

    response = client.post("/api/garmin/sync")

    assert response.json()["skipped"] == ["9"]


def test_sync_sem_chave_configurada(client: TestClient) -> None:
    response = client.post("/api/garmin/sync")

    assert response.status_code == 400
    assert "GARMIN_PERSONAL_API_KEY" in response.json()["detail"]


def test_sync_com_chave_invalida(
    client: TestClient, garmin_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_transport(monkeypatch, FakeGarmin([], {}, token_status=401))

    response = client.post("/api/garmin/sync")

    assert response.status_code == 502
    assert "inválida ou expirada" in response.json()["detail"]
