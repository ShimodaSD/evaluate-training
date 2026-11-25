from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração da aplicação, lida de variáveis de ambiente ou do arquivo .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Evaluate Training API"
    version: str = "0.1.0"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://training:training@localhost:5432/training"
    cors_origins: list[str] = ["http://localhost:5173"]
    timezone: str = "America/Sao_Paulo"
    log_file: str = "logs/api.log"
    # Dia em que a semana de treino começa (0 = segunda ... 6 = domingo).
    week_start_weekday: int = Field(default=1, ge=0, le=6)

    # Garmin Connect Personal API: chave criada em
    # https://connect.garmin.com/app/settings/personalApiToken
    garmin_base_url: str = "https://personal.connectapi.garmin.com"
    garmin_personal_api_key: SecretStr | None = None

    # IA da avaliação da semana e da leitura de treinos em qualquer formato.
    # Gemini (chave grátis em https://aistudio.google.com/apikey) ou Claude (https://platform.claude.com)
    ai_provider: Literal["gemini", "anthropic"] = "gemini"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    anthropic_api_key: SecretStr | None = None
    anthropic_model: str = "claude-haiku-5-5"

    @property
    def ai_model(self) -> str:
        return self.gemini_model if self.ai_provider == "gemini" else self.anthropic_model

    @property
    def garmin_configured(self) -> bool:
        return bool(
            self.garmin_personal_api_key and self.garmin_personal_api_key.get_secret_value()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
