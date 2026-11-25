from collections.abc import Iterator
from typing import Annotated

import httpx
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_llm_client(settings: AppSettings) -> Iterator[httpx.Client]:
    key = settings.ai_api_key.get_secret_value() if settings.ai_api_key else ""
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    # Modelo local na CPU pode levar minutos para responder.
    with httpx.Client(base_url=settings.ai_base_url, headers=headers, timeout=300) as client:
        yield client


LLMClient = Annotated[httpx.Client, Depends(get_llm_client)]
