"""Leitura com IA de treinos em formatos que o parser do TrainingPeaks não reconhece."""

from __future__ import annotations

import anthropic
from pydantic import BaseModel, Field

from app.schemas.plan import PlannedWorkoutStructure
from app.services.llm import parse


class _AIWorkouts(BaseModel):
    workouts: list[PlannedWorkoutStructure] = Field(min_length=1)


SYSTEM_PROMPT = """Você converte treinos de corrida, ciclismo ou natação escritos em qualquer
formato (TrainingPeaks, planilha, mensagem do treinador, português ou inglês) nos passos
estruturados do app, um item em "workouts" por treino.

Regras:
- Cada passo tem distance_m (metros) ou duration_s (segundos), nunca os dois vazios.
- pace_min_s_per_km e pace_max_s_per_km são SEMPRE segundos por km: 5:00 min/km = 300;
  natação 1:45 min/100m = 1050; ciclismo 30 km/h = 120 (3600 / km/h). O pace_min é o mais
  rápido (menor número). Alvo em watts vai em power_min_w e power_max_w.
- Séries ("5x 1 km", "Repeat 5 times") viram um bloco {"kind": "repeat", "repeat": 5,
  "steps": [...]} com o tiro e a pausa dentro.
- Pausa, descanso ou recuperação parada: is_rest true. Zonas ("Z2", "Zona 1-Zona 2") vão em
  zone_min e zone_max.
- name é o nome curto do passo (Aquecimento, Tiro, Pausa, Desaquecimento); intensity é o rótulo
  de intensidade se houver.
- Não invente alvos que o texto não dá: deixe null."""


def parse_workouts_with_ai(
    client: anthropic.Anthropic | None, model: str, text: str
) -> list[PlannedWorkoutStructure]:
    return parse(client, model, SYSTEM_PROMPT, text, _AIWorkouts).workouts
