import json
from collections.abc import Iterator
from pathlib import Path

import anthropic
import httpx2 as httpx  # o SDK da Anthropic usa o httpx2
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
        anthropic_api_key=None,
        timezone="America/Sao_Paulo",
        week_start_weekday=0,
    )


class FakeLLM:
    """API da Anthropic falsa: guarda os pedidos e devolve a resposta configurada."""

    def __init__(self) -> None:
        self.requests: list[dict] = []
        self.reply: httpx.Response | Exception = httpx.ConnectError("offline")

    def answer(self, text: str, stop_reason: str = "end_turn") -> None:
        self.reply = httpx.Response(
            200,
            json={
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "model": "claude-haiku-5-5",
                "content": [{"type": "thinking", "thinking": "", "signature": "x"}]
                + [{"type": "text", "text": text}],
                "stop_reason": stop_reason,
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

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
    app.dependency_overrides[get_llm_client] = lambda: anthropic.Anthropic(
        api_key="test",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(llm.handler)),
    )
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
