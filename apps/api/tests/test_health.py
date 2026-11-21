from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings


def test_health_retorna_ok(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"
    assert body["garmin_configured"] is False


def test_health_indica_garmin_configurado(client: TestClient) -> None:
    configured = Settings(_env_file=None, garmin_client_id="id", garmin_client_secret="secret")
    client.app.dependency_overrides[get_settings] = lambda: configured

    response = client.get("/api/health")

    assert response.json()["garmin_configured"] is True
