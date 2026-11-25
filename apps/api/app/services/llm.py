"""Chat com qualquer API compatível com OpenAI (Ollama, LM Studio, DeepSeek, Anthropic...)."""

from __future__ import annotations

import re

import httpx

# Modelos de raciocínio (ex.: deepseek-r1 no Ollama) podem mandar o pensamento no texto.
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class LLMError(RuntimeError):
    pass


def chat(
    client: httpx.Client, model: str, system: str, user: str, *, json_mode: bool = False
) -> str:
    body: dict = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        response = client.post("/chat/completions", json=body)
    except httpx.TimeoutException as exc:
        raise LLMError("a IA demorou demais para responder") from exc
    except httpx.HTTPError as exc:
        raise LLMError(
            f"sem conexão com a IA em {client.base_url} (o Ollama está rodando?)"
        ) from exc

    if response.status_code == 401:
        raise LLMError("AI_API_KEY inválida")
    if response.status_code == 402:
        raise LLMError("a conta da IA está sem saldo")
    if response.status_code == 404:
        raise LLMError(f"modelo {model!r} não encontrado (no Ollama: ollama pull {model})")
    if response.is_error:
        raise LLMError(f"a IA respondeu {response.status_code}: {response.text[:200]}")

    try:
        content = response.json()["choices"][0]["message"]["content"] or ""
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError("a IA devolveu uma resposta em formato inesperado") from exc
    text = _THINK_RE.sub("", content).strip()
    if not text:
        raise LLMError("a IA devolveu uma resposta vazia")
    return text
