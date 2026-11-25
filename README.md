# evaluate-training

Dashboard para avaliar treinos de corrida, ciclismo e natação, comparando o treino planejado
da semana (texto copiado do TrainingPeaks) com o que foi realizado (upload de arquivos e API
Garmin).

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
│           ├── lib/         # Formatação de km, pace/velocidade por esporte e datas
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
| `POST` | `/api/planned-workouts/preview` | Interpreta o texto sem salvar (TrainingPeaks; se falhar, IA) |
| `POST` | `/api/planned-workouts` | Salva um treino planejado (`scheduled_date`, `text`, `title`, `sport` e, opcional, a `structure` conferida no preview) |
| `GET` | `/api/planned-workouts?start=&end=` | Lista treinos planejados |
| `DELETE` | `/api/planned-workouts/{id}` | Remove um treino planejado |
| `POST` | `/api/activities/upload` | Upload de arquivos `.fit`, `.gpx` ou `.tcx` (campo `files`) |
| `GET` | `/api/activities?start=&end=` | Lista atividades realizadas |
| `DELETE` | `/api/activities/{id}` | Remove uma atividade |
| `GET` | `/api/weeks/{data}` | Planejado x realizado da semana de treino que contém a data (começa no dia de `WEEK_START_WEEKDAY`; padrão terça) |

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

O alvo pode ser pace (`min/km` na corrida, `min/100m` na natação), velocidade (`km/h`) ou
potência (`150-180 W`, ideal no rolo, onde a velocidade é virtual), sobre distância
(`2.00 km`, `100 m`) ou duração (`1:00:00`). Ao salvar, escolha o esporte (`run`, `bike` ou
`swim`; padrão `run`). Treinos só por duração não têm nota de distância.

### Esportes

- Todo alvo é guardado como pace em s/km; o esporte só muda a exibição (min/km, km/h ou
  min/100m). Para um esporte novo basta um rótulo e uma regra de exibição.
- O esporte da atividade vem do arquivo ou da Garmin (`running`, `cycling`, `lap_swimming`...)
  e é normalizado para `run`, `bike`, `swim` ou `other`. GPX sem tipo conta como corrida.
- Cada treino planejado só casa com uma atividade do mesmo esporte no mesmo dia.
- A carga combinada da semana é o tempo total; distâncias aparecem por esporte.

### Como a aderência é calculada

- Quando a atividade tem uma volta por passo (treino estruturado executado no relógio),
  cada passo é comparado com sua volta. Uma volta extra no final é ignorada.
- Caso contrário, compara-se o total; o pace médio só é avaliado em treinos com um
  único passo de corrida (rodagem contínua).
- Pace dentro da faixa alvo com tolerância de 5 s/km (3 s/100m na natação). Passos de pausa
  não contam.
- Com alvo em W (ciclismo), vale a potência média com tolerância de 5 W em vez do pace.
- Aderência = média entre a nota de distância (`1 - |realizado/planejado - 1|`) e a
  fração de passos no pace alvo. A partir de 80% o treino conta como cumprido.

## Fluxo de trabalho

O projeto usa **gitflow**: funcionalidades em `feature/*` com PR para `develop`;
`release/*` e `hotfix/*` levam para `main`. Padrões de código e regras para agentes
de IA estão em [AGENTS.md](AGENTS.md).

## Integração Garmin

Usa a [Garmin Connect Personal API](https://developer.garmin.com/gc-developer-program/personal/personal-api/).

1. Crie uma chave em https://connect.garmin.com/app/settings/personalApiToken
   (ela aparece uma única vez; validade de 30 dias a 1 ano).
2. Coloque no `.env`: `GARMIN_PERSONAL_API_KEY=sua-chave`.
3. No topo do painel, clique em **Sincronizar Garmin**
   (ou `POST /api/garmin/sync?start=AAAA-MM-DD&end=AAAA-MM-DD`; padrão: últimos 7 dias).

A sincronização busca as corridas, pedais e natações do período (outros tipos, como
musculação, são ignorados), baixa o arquivo FIT original de cada uma
(com as voltas, para a comparação passo a passo) e ignora atividades já importadas,
inclusive as enviadas antes por upload de arquivo. `/api/health` informa em
`garmin_configured` se a chave foi definida.

## IA (avaliação da semana e treinos em qualquer formato)

A IA é o Claude Haiku (`claude-haiku-5-5`, o modelo mais barato da Anthropic), configurado
no `.env`:

1. Crie uma chave em https://platform.claude.com/settings/keys e coloque créditos na conta.
2. No `.env`: `ANTHROPIC_API_KEY=sua-chave` (troque de modelo com `ANTHROPIC_MODEL`).

Cada chamada é paga e só acontece quando o parser do TrainingPeaks falha ou quando você clica
em **Avaliar semana**.

- **Treinos em qualquer formato**: ao salvar, o texto passa primeiro pelo parser do
  TrainingPeaks. Se ele não reconhecer o formato, a IA converte o texto nos passos do treino e o
  formulário mostra o resultado para você conferir antes de **Confirmar e salvar**.
- **Avaliação da semana**: o card **Avaliação da IA** manda o planejado x realizado da semana e
  mostra um parecer curto: veredito, o que foi bem, o que fugiu do plano e uma recomendação.
