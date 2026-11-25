"""Chamadas ao Claude (API da Anthropic) usadas pela avaliação e pela leitura de treinos."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import anthropic
from pydantic import BaseModel, ValidationError


class LLMError(RuntimeError):
    pass


@contextmanager
def _api_errors() -> Iterator[None]:
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
        raise LLMError("o Claude devolveu o treino fora do formato esperado") from exc


def _require(client: anthropic.Anthropic | None) -> anthropic.Anthropic:
    if client is None:
        raise LLMError("configure ANTHROPIC_API_KEY no arquivo .env")
    return client


def _check(response: anthropic.types.Message) -> None:
    if response.stop_reason == "refusal":
        raise LLMError("o Claude não conseguiu responder a este pedido")
    if response.stop_reason == "max_tokens":
        raise LLMError("a resposta do Claude ficou incompleta")


def chat(client: anthropic.Anthropic | None, model: str, system: str, user: str) -> str:
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
    client: anthropic.Anthropic | None, model: str, system: str, user: str, output: type[T]
) -> T:
    """Resposta estruturada: a API segue o JSON Schema do modelo e o SDK valida com Pydantic."""
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
        raise LLMError("o Claude devolveu o treino fora do formato esperado")
    return response.parsed_output
