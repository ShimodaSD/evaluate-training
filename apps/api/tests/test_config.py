import pytest

from app.core.config import Settings


def test_settings_le_credenciais_garmin_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GARMIN_CLIENT_ID", "meu-id")
    monkeypatch.setenv("GARMIN_CLIENT_SECRET", "meu-segredo")

    settings = Settings(_env_file=None)

    assert settings.garmin_client_id == "meu-id"
    assert settings.garmin_client_secret is not None
    assert settings.garmin_client_secret.get_secret_value() == "meu-segredo"
    assert settings.garmin_configured is True


def test_segredo_nao_aparece_na_representacao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GARMIN_CLIENT_SECRET", "meu-segredo")

    settings = Settings(_env_file=None)

    assert "meu-segredo" not in repr(settings)
