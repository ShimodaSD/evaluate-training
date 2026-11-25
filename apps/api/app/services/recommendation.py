"""Treino recomendado para hoje a partir dos dados da Garmin e da semana planejada."""

from __future__ import annotations

import datetime as dt
import json
import logging

from sqlalchemy.orm import Session

from app.integrations.garmin.client import GarminClient, GarminError
from app.models import GarminWellness
from app.schemas.comparison import WeekSummary
from app.schemas.recommendation import TodayRecommendation
from app.services.llm import LLMClient, parse

log = logging.getLogger("app.garmin")

# Resumos diários da Personal API (os mesmos endpoints do cliente oficial da Garmin).
WELLNESS = {
    "sono": ("/sleep-service/sleep/dailySleepSummariesByDate", "params"),
    "hrv": ("/hrv-service/hrv/daily/{start}/{end}", "path"),
    "body_battery": ("/wellness-service/wellness/bodyBattery/reports/daily", "params"),
    "resumo_diario": ("/usersummary-service/v2/dailysummaries", "params"),
    "estresse": ("/usersummary-service/stats/stress/daily/{start}/{end}", "path"),
    "vo2max": ("/metrics-service/metrics/maxmet/daily/{start}/{end}", "path"),
}
WELLNESS_DAYS = 7
LOAD_DAYS = 28
# shortcut: corta cada fonte em 20 mil caracteres, suba se a IA reclamar de dados faltando.
MAX_CHARS = 20_000
ACTIVITY_KEYS = (
    "activityName",
    "startTimeLocal",
    "activityType",
    "distance",
    "duration",
    "averageHR",
    "maxHR",
    "avgPower",
    "normPower",
    "aerobicTrainingEffect",
    "anaerobicTrainingEffect",
    "trainingEffectLabel",
    "activityTrainingLoad",
)


SYSTEM_PROMPT = """Você é um treinador de endurance experiente recomendando o treino de HOJE
para um amador de corrida, ciclismo e natação. Você recebe, em JSON:
- "garmin": dados brutos da Garmin dos últimos dias (sono, HRV, body battery, resumo diário com
  FC de repouso e estresse, VO2max) e as atividades das últimas 4 semanas com carga e training
  effect. Fontes ausentes aparecem em "indisponivel".
- "esporte": o esporte que o atleta quer treinar hoje (bike ou run). Recomende SÓ esse
  esporte (ou descanso, sport "rest", se a prontidão for baixa).
- "semana": o plano da semana (início na terça) com o planejado x realizado, paces em s/km.

Objetivo de cada esporte para este atleta:
- Ciclismo: só manter a Zona 2 e acumular carga aeróbica, com potência estável. Nunca
  recomende intensidade na bike.
- Corrida: desenvolvimento aeróbico e anaeróbico (rodagens de base e tiros/intervalados).

Regras:
1. Avalie a prontidão (alta, moderada, baixa) pelo sono, HRV em relação à linha de base, FC de
   repouso, body battery, estresse e carga recente.
2. Se há treino planejado para hoje no esporte pedido, parta dele: mantenha se a prontidão
   permite, ou diga como reduzir. Sem plano para hoje, sugira o que encaixa no que falta da semana.
3. Prontidão baixa: descanso ou treino regenerativo curto (sport "rest" no descanso).
4. Corrida em min:ss/km; ciclismo é indoor com medidor de potência, então dê alvos em watts
   e zona (sem FTP conhecido, baseie os watts nos pedais Z2 recentes); natação em min:ss/100m.
5. Escreva em português do Brasil, texto simples, sem Markdown. Em "reason", cite os números
   que pesaram (ex.: "HRV 42 ms, abaixo da base de 50"). Não invente dados que não vieram e não
   dê conselho médico."""


def _fetch(client: GarminClient, path: str, style: str, day: dt.date) -> object:
    if style == "path":
        return client.get_json(path.format(start=day.isoformat(), end=day.isoformat()))
    return client.get_json(path, {"startDate": day.isoformat(), "endDate": day.isoformat()})


def collect_garmin_stats(
    db: Session, client: GarminClient, today: dt.date
) -> tuple[dict, list[str]]:
    """Junta o que a chave da Garmin alcança; cada fonte que falhar vira 'indisponível'.

    Dias passados vêm do banco; só hoje e os dias que faltam são buscados na Garmin.
    """
    days = [today - dt.timedelta(days=n) for n in range(WELLNESS_DAYS - 1, -1, -1)]
    stats: dict = {}
    unavailable: list[str] = []
    for name, (path, style) in WELLNESS.items():
        by_day = {}
        try:
            for day in days:
                row = db.get(GarminWellness, (name, day))
                if row is None or day == today:
                    row = db.merge(
                        GarminWellness(source=name, day=day, data=_fetch(client, path, style, day))
                    )
                by_day[day.isoformat()] = row.data
        except (GarminError, ValueError) as exc:
            log.warning("Garmin sem %s: %s", name, exc)
            unavailable.append(name)
        if by_day:
            stats[name] = json.dumps(by_day)[:MAX_CHARS]
    db.commit()
    try:
        activities = client.search_activities(today - dt.timedelta(days=LOAD_DAYS), today)
        stats["atividades"] = [{k: a[k] for k in ACTIVITY_KEYS if k in a} for a in activities]
    except GarminError as exc:
        log.warning("Garmin sem atividades: %s", exc)
        unavailable.append("atividades")
    stats["indisponivel"] = unavailable
    return stats, unavailable


def recommend_today(
    client: LLMClient, model: str, today: dt.date, sport: str, stats: dict, week: WeekSummary
) -> TodayRecommendation:
    payload = json.dumps(
        {
            "hoje": today.isoformat(),
            "esporte": sport,
            "garmin": stats,
            "semana": week.model_dump(mode="json"),
        },
        ensure_ascii=False,
    )
    return parse(client, model, SYSTEM_PROMPT, payload, TodayRecommendation)
