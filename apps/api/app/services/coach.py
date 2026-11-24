"""Avaliação da semana de treinos escrita pelo Claude."""

from __future__ import annotations

import anthropic

from app.schemas.comparison import WeekSummary

SYSTEM_PROMPT = """Você é um treinador de endurance experiente avaliando a semana de um amador
de corrida, ciclismo e natação. Você recebe, em JSON, o plano da semana (copiado do
TrainingPeaks) e o que foi realizado (arquivos do relógio Garmin), com a comparação já
calculada: distâncias em metros, paces em segundos por km, tempos em segundos e, quando
disponível, a comparação volta a volta de cada passo do treino (pace_status: in_range, fast ou
slow). O campo sport diz o esporte (run, bike, swim, other) e "sports" traz os totais da semana
por esporte; actual_duration_s é a carga total da semana em tempo.

Escreva em português do Brasil, em texto simples (sem Markdown, sem títulos com #), com no
máximo 250 palavras:
1. Um parágrafo curto com o veredito da semana.
2. De 2 a 4 linhas começando com "- " apontando o que foi bem e o que fugiu do plano, citando
   treinos e números concretos: corrida em min:ss/km, ciclismo em km/h (3600 / pace), natação
   em min:ss/100m (pace / 10); distâncias em km, ou em metros na natação.
3. Uma linha final começando com "Próxima semana:" com uma recomendação prática.

Baseie-se só nos dados. Se faltarem dados (treino não feito, sem voltas, sem FC), diga isso em
vez de supor. Não dê conselho médico."""


class CoachError(RuntimeError):
    pass


def analyze_week(client: anthropic.Anthropic, model: str, week: WeekSummary) -> str:
    try:
        response = client.beta.messages.create(
            model=model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            output_config={"effort": "medium"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{"role": "user", "content": week.model_dump_json()}],
        )
    except anthropic.AuthenticationError as exc:
        raise CoachError("ANTHROPIC_API_KEY inválida") from exc
    except anthropic.RateLimitError as exc:
        raise CoachError("limite de uso da API da Anthropic atingido; tente mais tarde") from exc
    except anthropic.BadRequestError as exc:
        if "credit balance" in str(exc).lower():
            raise CoachError(
                "a conta da Anthropic está sem créditos: "
                "https://platform.claude.com/settings/billing"
            ) from exc
        raise CoachError(f"a API da Anthropic recusou a requisição: {exc.message}") from exc
    except anthropic.APIStatusError as exc:
        raise CoachError(f"a API da Anthropic respondeu {exc.status_code}") from exc
    except anthropic.APIConnectionError as exc:
        raise CoachError("sem conexão com a API da Anthropic") from exc

    if response.stop_reason == "refusal":
        raise CoachError("o Claude não conseguiu avaliar esta semana")
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if not text:
        raise CoachError("o Claude devolveu uma resposta vazia")
    return text
