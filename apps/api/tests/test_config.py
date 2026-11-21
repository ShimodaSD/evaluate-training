import pytest

from app.core.config import Settings


def test_settings_le_a_chave_garmin_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GARMIN_PERSONAL_API_KEY", "minha-chave")

    settings = Settings(_env_file=None)

    assert settings.garmin_personal_api_key is not None
    assert settings.garmin_personal_api_key.get_secret_value() == "minha-chave"
    assert settings.garmin_configured is True


def test_chave_vazia_nao_conta_como_configurada(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GARMIN_PERSONAL_API_KEY", "")

    assert Settings(_env_file=None).garmin_configured is False


def test_chave_nao_aparece_na_representacao(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GARMIN_PERSONAL_API_KEY", "minha-chave")

    assert "minha-chave" not in repr(Settings(_env_file=None))
