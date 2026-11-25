import json
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registra os modelos no metadata)
from app.api.deps import get_llm_client
from app.core.config import Settings, get_settings
from app.db.session import Base, get_db
from app.main import create_app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def week_text() -> str:
    return (FIXTURES / "trainingpeaks_semana.txt").read_text(encoding="utf-8")


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        garmin_personal_api_key=None,
        timezone="America/Sao_Paulo",
        week_start_weekday=0,
    )


class FakeLLM:
    """API de chat falsa: guarda os pedidos e devolve a resposta configurada (padrão: offline)."""

    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.reply: httpx.Response | Exception = httpx.ConnectError("offline")

    def answer(self, content: str) -> None:
        self.reply = httpx.Response(200, json={"choices": [{"message": {"content": content}}]})

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(json.loads(request.content))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(settings: Settings, db: Session, llm: FakeLLM) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_llm_client] = lambda: httpx.Client(
        base_url="http://llm/v1", transport=httpx.MockTransport(llm.handler)
    )
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
