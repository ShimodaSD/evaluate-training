"""Parser do texto de treinos copiado do TrainingPeaks.

Formato esperado (um ou mais treinos, cada um começando em "1."):

    1. Aquecimento — Z1
    2.00 km @ 05:44-06:23 min/km
    Zona 1-Zona 2
    2. Repeat 3 times
       1. Ativação — Z4
    0.20 km @ 04:28-04:42 min/km
    Zona 4-Zona 5
       2. Pausa — Passiva
    2:30 @ 00:00 min/km

Cada passo tem um cabeçalho numerado (com indentação quando está dentro de
um bloco "Repeat N times"), uma linha de alvo (distância ou duração e faixa
de pace) e, opcionalmente, uma linha de zonas.
"""

from __future__ import annotations

import re

from app.schemas.plan import PlannedStep, PlannedWorkoutStructure, RepeatBlock


class PlanParseError(ValueError):
    """Erro ao interpretar o texto do treino, com o número da linha."""

    def __init__(self, message: str, line_number: int | None = None) -> None:
        self.line_number = line_number
        prefix = f"Linha {line_number}: " if line_number is not None else ""
        super().__init__(f"{prefix}{message}")


_HEADER_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<num>\d+)\.\s+(?P<title>.+?)\s*$")
_REPEAT_RE = re.compile(
    r"^(?:repeat|repetir)\s+(?P<count>\d+)\s*(?:times|vezes|x)?$", re.IGNORECASE
)
_PACE = r"(?P<pmin>\d{1,2}:\d{2})(?:\s*-\s*(?P<pmax>\d{1,2}:\d{2}))?\s*min/km"
_DISTANCE_TARGET_RE = re.compile(
    rf"^(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>km|m)\s*(?:@\s*{_PACE})?\s*$", re.IGNORECASE
)
_DURATION_TARGET_RE = re.compile(
    rf"^(?P<duration>\d{{1,2}}:\d{{2}}(?::\d{{2}})?)\s*(?:@\s*{_PACE})?\s*$", re.IGNORECASE
)
_ZONE_RE = re.compile(r"^zona\s*(?P<zmin>\d+)(?:\s*-\s*zona\s*(?P<zmax>\d+))?\s*$", re.IGNORECASE)
_REST_WORDS = ("pausa", "passiva", "rest", "descanso", "recovery")


def _clock_to_seconds(value: str) -> int:
    parts = [int(p) for p in value.split(":")]
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds


def _split_title(title: str) -> tuple[str, str | None]:
    for sep in (" — ", " – ", " - "):
        if sep in title:
            name, label = title.split(sep, 1)
            return name.strip(), label.strip() or None
    return title.strip(), None


class _Builder:
    """Acumula os passos de um treino enquanto as linhas são lidas."""

    def __init__(self) -> None:
        self.blocks: list[PlannedStep | RepeatBlock] = []
        self.current_repeat: RepeatBlock | None = None
        self.repeat_indent: int = -1
        self.current_step: PlannedStep | None = None

    def add_header(self, indent: int, title: str, line_number: int) -> None:
        if self.current_repeat is not None and indent <= self.repeat_indent:
            self._close_repeat(line_number)

        repeat_match = _REPEAT_RE.match(title)
        if repeat_match:
            if self.current_repeat is not None:
                raise PlanParseError("blocos 'Repeat' aninhados não são suportados", line_number)
            self.current_repeat = RepeatBlock(repeat=int(repeat_match["count"]), steps=[])
            self.repeat_indent = indent
            self.current_step = None
            return

        name, label = _split_title(title)
        step = PlannedStep(name=name, intensity=label)
        if self.current_repeat is not None:
            self.current_repeat.steps.append(step)
        else:
            self.blocks.append(step)
        self.current_step = step

    def add_target(self, line: str, line_number: int) -> None:
        step = self._require_step(line_number)
        if match := _DISTANCE_TARGET_RE.match(line):
            value = float(match["value"].replace(",", "."))
            step.distance_m = value * 1000 if match["unit"].lower() == "km" else value
        elif match := _DURATION_TARGET_RE.match(line):
            step.duration_s = _clock_to_seconds(match["duration"])
        else:  # pragma: no cover - protegido por is_target_line
            raise PlanParseError(f"alvo não reconhecido: {line!r}", line_number)

        if match["pmin"]:
            low = _clock_to_seconds(match["pmin"])
            high = _clock_to_seconds(match["pmax"]) if match["pmax"] else low
            if low == 0 and high == 0:
                step.is_rest = True
            else:
                step.pace_min_s_per_km, step.pace_max_s_per_km = sorted((low, high))

    def add_zone(self, match: re.Match[str], line_number: int) -> None:
        step = self._require_step(line_number)
        step.zone_min = int(match["zmin"])
        step.zone_max = int(match["zmax"]) if match["zmax"] else step.zone_min

    def finish(self, line_number: int) -> PlannedWorkoutStructure:
        if self.current_repeat is not None:
            self._close_repeat(line_number)
        for step in _iter_steps(self.blocks):
            if step.distance_m is None and step.duration_s is None:
                raise PlanParseError(f"o passo '{step.name}' não tem distância nem duração")
            if not step.is_rest and step.intensity:
                step.is_rest = any(w in step.intensity.lower() for w in _REST_WORDS)
        return PlannedWorkoutStructure(blocks=self.blocks)

    def _close_repeat(self, line_number: int) -> None:
        assert self.current_repeat is not None
        if not self.current_repeat.steps:
            raise PlanParseError("bloco 'Repeat' sem passos", line_number)
        self.blocks.append(self.current_repeat)
        self.current_repeat = None
        self.repeat_indent = -1
        self.current_step = None

    def _require_step(self, line_number: int) -> PlannedStep:
        if self.current_step is None:
            raise PlanParseError("linha de alvo ou zona sem um passo antes dela", line_number)
        return self.current_step


def _iter_steps(blocks: list[PlannedStep | RepeatBlock]):
    for block in blocks:
        if isinstance(block, RepeatBlock):
            yield from block.steps
        else:
            yield block


def parse_workouts(text: str) -> list[PlannedWorkoutStructure]:
    """Interpreta um texto com um ou mais treinos.

    Um novo treino começa quando aparece um passo "1." sem indentação depois
    de outro treino já iniciado.
    """
    workouts: list[PlannedWorkoutStructure] = []
    builder: _Builder | None = None
    last_line = 0

    for line_number, raw in enumerate(text.splitlines(), start=1):
        last_line = line_number
        if not raw.strip():
            continue
        line = raw.strip()

        header = _HEADER_RE.match(raw.expandtabs(4))
        if header and not _DURATION_TARGET_RE.match(line):
            indent = len(header["indent"])
            if indent == 0 and header["num"] == "1" and builder is not None:
                workouts.append(builder.finish(line_number))
                builder = None
            if builder is None:
                builder = _Builder()
            builder.add_header(indent, header["title"], line_number)
            continue

        if builder is None:
            raise PlanParseError(
                f"esperado um passo numerado (ex.: '1. Aquecimento'): {line!r}", line_number
            )

        if _DISTANCE_TARGET_RE.match(line) or _DURATION_TARGET_RE.match(line):
            builder.add_target(line, line_number)
        elif zone := _ZONE_RE.match(line):
            builder.add_zone(zone, line_number)
        else:
            raise PlanParseError(f"linha não reconhecida: {line!r}", line_number)

    if builder is not None:
        workouts.append(builder.finish(last_line))
    if not workouts:
        raise PlanParseError("nenhum treino encontrado no texto")
    return workouts


def parse_workout(text: str) -> PlannedWorkoutStructure:
    """Interpreta um texto que deve conter exatamente um treino."""
    workouts = parse_workouts(text)
    if len(workouts) != 1:
        raise PlanParseError(f"esperado 1 treino, encontrados {len(workouts)}")
    return workouts[0]
