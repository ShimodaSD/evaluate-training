from collections.abc import Iterator
from typing import Annotated

import anthropic
import httpx
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services import llm

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_llm_client(settings: AppSettings) -> Iterator[llm.LLMClient]:
    """Cliente do provedor de IA do .env; None sem chave, para a rota explicar o que configurar."""
    if settings.ai_provider == "anthropic":
        key = settings.anthropic_api_key
        yield anthropic.Anthropic(api_key=key.get_secret_value()) if key else None
    elif not settings.gemini_api_key:
        yield None
    else:
        with httpx.Client(
            base_url="https://generativelanguage.googleapis.com/v1beta",
            headers={"x-goog-api-key": settings.gemini_api_key.get_secret_value()},
            timeout=120,
        ) as client:
            yield client


LLMClient = Annotated[llm.LLMClient, Depends(get_llm_client)]
