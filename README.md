# evaluate-training

Dashboard para avaliar treinos de corrida, comparando o treino planejado da semana
(texto copiado do TrainingPeaks) com o que foi realizado (upload de arquivos e API Garmin).

## Estrutura

```
.
├── apps/
│   ├── api/                 # Backend Python (FastAPI)
│   │   ├── app/
│   │   │   ├── api/         # Rotas HTTP
│   │   │   ├── core/        # Configuração (lida do .env)
│   │   │   ├── db/          # Sessão e base do SQLAlchemy
│   │   │   ├── models/      # Modelos do banco
│   │   │   ├── schemas/     # Schemas Pydantic (entrada/saída)
│   │   │   ├── services/    # Regras de negócio (ex.: planejado x realizado)
│   │   │   └── integrations/garmin/  # Cliente da API Garmin
│   │   └── tests/           # Testes com pytest
│   └── web/                 # Frontend React + TypeScript (Vite)
│       └── src/
│           ├── api/         # Cliente HTTP e tipos da API
│           ├── components/  # Painel, gráfico, formulários (com testes *.test.tsx)
│           ├── hooks/       # Hooks de dados (SWR)
│           ├── lib/         # Formatação de km, pace e datas
│           └── test/        # Setup, fixtures e helpers do Vitest
├── docker-compose.yml       # Postgres + API + Web
├── Makefile                 # Atalhos de desenvolvimento
└── .env.example             # Variáveis de ambiente (inclui credenciais Garmin)
```

## Requisitos

- Docker e Docker Compose, **ou**
- Python 3.12+ com [uv](https://docs.astral.sh/uv/) e Node.js 22+

## Como rodar

```bash
cp .env.example .env   # preencha as credenciais da Garmin
make up                # sobe Postgres, API (8000) e Web (5173)
```

- Frontend: http://localhost:5173
- API: http://localhost:8000/api/health
- Documentação da API: http://localhost:8000/docs

Sem Docker:

```bash
make install
cd apps/api && uv run uvicorn app.main:app --reload
cd apps/web && npm run dev
```

## Testes e qualidade

```bash
make test     # pytest (api) + vitest (web)
make lint     # ruff + oxlint + prettier + tsc
make format   # formata o código
```

## Banco de dados

As migrações ficam em `apps/api/migrations` (Alembic) e rodam automaticamente
ao subir a API pelo Docker. Sem Docker: `make migrate`.

Para criar uma nova migração depois de alterar os modelos:

```bash
cd apps/api && uv run alembic revision --autogenerate -m "descricao"
```

## API

| Método | Rota | Descrição |
| --- | --- | --- |
| `POST` | `/api/planned-workouts/preview` | Interpreta o texto do TrainingPeaks sem salvar |
| `POST` | `/api/planned-workouts` | Salva um treino planejado (`scheduled_date`, `text`, `title`) |
| `GET` | `/api/planned-workouts?start=&end=` | Lista treinos planejados |
| `DELETE` | `/api/planned-workouts/{id}` | Remove um treino planejado |
| `POST` | `/api/activities/upload` | Upload de arquivos `.fit`, `.gpx` ou `.tcx` (campo `files`) |
| `GET` | `/api/activities?start=&end=` | Lista atividades realizadas |
| `DELETE` | `/api/activities/{id}` | Remove uma atividade |
| `GET` | `/api/weeks/{data}` | Planejado x realizado da semana (seg a dom) que contém a data |

### Formato do treino planejado

Texto copiado do TrainingPeaks, um passo por cabeçalho numerado:

```
1. Aquecimento — Z1
2.00 km @ 05:44-06:23 min/km
Zona 1-Zona 2
2. Repeat 5 times
   1. Série principal — VO2
1.20 km @ 04:08-04:15 min/km
Zona 5-Zona 6
   2. Pausa — Passiva
2:30 @ 00:00 min/km
```

### Como a aderência é calculada

- Quando a atividade tem uma volta por passo (treino estruturado executado no relógio),
  cada passo é comparado com sua volta. Uma volta extra no final é ignorada.
- Caso contrário, compara-se o total; o pace médio só é avaliado em treinos com um
  único passo de corrida (rodagem contínua).
- Pace dentro da faixa alvo com tolerância de 5 s/km. Passos de pausa não contam.
- Aderência = média entre a nota de distância (`1 - |realizado/planejado - 1|`) e a
  fração de passos no pace alvo. A partir de 80% o treino conta como cumprido.

## Fluxo de trabalho

O projeto usa **gitflow**: funcionalidades em `feature/*` com PR para `develop`;
`release/*` e `hotfix/*` levam para `main`. Padrões de código e regras para agentes
de IA estão em [AGENTS.md](AGENTS.md).

## Integração Garmin

As credenciais da API Garmin Connect são lidas do `.env`
(`GARMIN_CLIENT_ID`, `GARMIN_CLIENT_SECRET`, `GARMIN_ACCESS_TOKEN`).
O endpoint `/api/health` informa em `garmin_configured` se elas foram definidas.
