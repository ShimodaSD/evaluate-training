from typing import Annotated

import anthropic
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_llm_client(settings: AppSettings) -> anthropic.Anthropic | None:
    """Cliente do Claude; None sem chave, para a rota explicar o que configurar."""
    if not settings.anthropic_api_key:
        return None
    return anthropic.Anthropic(api_key=settings.anthropic_api_key.get_secret_value())


LLMClient = Annotated[anthropic.Anthropic | None, Depends(get_llm_client)]
