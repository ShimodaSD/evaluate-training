"""IA (Gemini ou Claude) usada pela avaliação da semana e pela leitura de treinos."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

import anthropic
import httpx
from pydantic import BaseModel, ValidationError

log = logging.getLogger("app.ia")


class LLMError(RuntimeError):
    pass


@contextmanager
def _api_errors() -> Iterator[None]:
    """Traduz os erros do SDK e da validação em LLMError e registra a causa no log."""
    try:
        with _translate_errors():
            yield
    except LLMError as exc:
        log.warning("%s | causa: %r", exc, exc.__cause__)
        raise


@contextmanager
def _translate_errors() -> Iterator[None]:
    try:
        yield
    except anthropic.AuthenticationError as exc:
        raise LLMError("ANTHROPIC_API_KEY inválida") from exc
    except anthropic.RateLimitError as exc:
        raise LLMError("limite de uso da API da Anthropic atingido; tente mais tarde") from exc
    except anthropic.BadRequestError as exc:
        if "credit balance" in str(exc).lower():
            raise LLMError(
                "a conta da Anthropic está sem créditos: "
                "https://platform.claude.com/settings/billing"
            ) from exc
        raise LLMError(f"a API da Anthropic recusou a requisição: {exc.message}") from exc
    except anthropic.APIStatusError as exc:
        raise LLMError(f"a API da Anthropic respondeu {exc.status_code}") from exc
    except anthropic.APIConnectionError as exc:
        raise LLMError("sem conexão com a API da Anthropic") from exc
    except ValidationError as exc:  # regras do schema que o SDK confere do lado do cliente
        raise LLMError("a IA devolveu o treino fora do formato esperado") from exc


# Cliente do provedor escolhido em AI_PROVIDER: httpx para o Gemini, SDK para o Claude.
LLMClient = anthropic.Anthropic | httpx.Client | None


def _require[C](client: C | None) -> C:
    if client is None:
        raise LLMError("configure a chave da IA no .env (GEMINI_API_KEY ou ANTHROPIC_API_KEY)")
    return client


def _gemini(client: httpx.Client, model: str, system: str, user: str, schema: dict | None) -> str:
    config = (
        {"responseMimeType": "application/json", "responseJsonSchema": schema} if schema else {}
    )
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": config,
    }
    try:
        response = client.post(f"/models/{model}:generateContent", json=body)
    except httpx.HTTPError as exc:
        log.warning("Gemini %s: sem conexão: %r", model, exc)
        raise LLMError("sem conexão com a API do Gemini") from exc
    if response.is_error or '"candidates"' not in response.text:
        log.warning("Gemini %s respondeu %s: %s", model, response.status_code, response.text[:2000])

    if response.status_code in (400, 401, 403) and "API key" in response.text:
        raise LLMError("GEMINI_API_KEY inválida")
    if response.status_code == 429:
        raise LLMError("limite de uso do Gemini atingido; tente mais tarde")
    if response.status_code == 404:
        raise LLMError(f"modelo {model!r} não existe no Gemini (ajuste GEMINI_MODEL)")
    if response.is_error:
        raise LLMError(f"a API do Gemini respondeu {response.status_code}")

    try:
        candidate = response.json()["candidates"][0]
    except (ValueError, KeyError, IndexError) as exc:  # pedido bloqueado vem sem candidates
        raise LLMError("o Gemini não conseguiu responder a este pedido") from exc
    if candidate.get("finishReason") == "MAX_TOKENS":
        log.warning("Gemini %s cortou a resposta: %s", model, response.text[:2000])
        raise LLMError("a resposta do Gemini ficou incompleta")
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    if not text:
        log.warning("Gemini %s sem texto: %s", model, response.text[:2000])
        raise LLMError("o Gemini devolveu uma resposta vazia")
    return text


def _check(response: anthropic.types.Message) -> None:
    if response.stop_reason == "refusal":
        raise LLMError("o Claude não conseguiu responder a este pedido")
    if response.stop_reason == "max_tokens":
        raise LLMError("a resposta do Claude ficou incompleta")


def chat(client: LLMClient, model: str, system: str, user: str) -> str:
    if isinstance(client, httpx.Client):
        return _gemini(client, model, system, user, None)
    with _api_errors():
        response = _require(client).messages.create(
            model=model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    _check(response)
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    if not text:
        raise LLMError("o Claude devolveu uma resposta vazia")
    return text


def parse[T: BaseModel](
    client: LLMClient, model: str, system: str, user: str, output: type[T]
) -> T:
    """Resposta estruturada: a API segue o JSON Schema do modelo e o Pydantic valida."""
    if isinstance(client, httpx.Client):
        text = _gemini(client, model, system, user, output.model_json_schema())
        with _api_errors():
            return output.model_validate_json(text)
    with _api_errors():
        response = _require(client).messages.parse(
            model=model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=output,
        )
    _check(response)
    if response.parsed_output is None:
        raise LLMError("a IA devolveu o treino fora do formato esperado")
    return response.parsed_output
