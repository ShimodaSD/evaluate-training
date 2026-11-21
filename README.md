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
│           ├── api/         # Cliente HTTP da API
│           ├── components/  # Componentes (com testes *.test.tsx)
│           └── test/        # Setup do Vitest
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

## Integração Garmin

As credenciais da API Garmin Connect são lidas do `.env`
(`GARMIN_CLIENT_ID`, `GARMIN_CLIENT_SECRET`, `GARMIN_ACCESS_TOKEN`).
O endpoint `/api/health` informa em `garmin_configured` se elas foram definidas.
