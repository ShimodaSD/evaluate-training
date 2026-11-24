from functools import lru_cache

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
    # Dia em que a semana de treino começa (0 = segunda ... 6 = domingo).
    week_start_weekday: int = Field(default=1, ge=0, le=6)

    # Garmin Connect Personal API: chave criada em
    # https://connect.garmin.com/app/settings/personalApiToken
    garmin_base_url: str = "https://personal.connectapi.garmin.com"
    garmin_personal_api_key: SecretStr | None = None

    # IA (avaliação da semana e leitura de treinos em qualquer formato) em qualquer API
    # compatível com OpenAI: Ollama local (padrão), LM Studio, DeepSeek, Anthropic...
    ai_base_url: str = "http://localhost:11434/v1"
    ai_api_key: SecretStr | None = None
    ai_model: str = "deepseek-r1:8b"

    @property
    def garmin_configured(self) -> bool:
        return bool(
            self.garmin_personal_api_key and self.garmin_personal_api_key.get_secret_value()
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
