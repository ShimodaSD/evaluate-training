from functools import lru_cache

from pydantic import SecretStr
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

    # Credenciais da API Garmin Connect (usadas no passo 4)
    garmin_base_url: str = "https://apis.garmin.com"
    garmin_client_id: str | None = None
    garmin_client_secret: SecretStr | None = None
    garmin_access_token: SecretStr | None = None

    @property
    def garmin_configured(self) -> bool:
        return bool(self.garmin_client_id and self.garmin_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
