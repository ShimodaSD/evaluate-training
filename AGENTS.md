# Instruções para agentes

Dashboard de treinos de corrida: compara o treino planejado (texto do TrainingPeaks)
com o realizado (arquivos FIT/GPX/TCX e API Garmin). Monorepo com `apps/api`
(FastAPI) e `apps/web` (React + Vite). Veja o README para rodar o projeto.

## Fluxo de git (gitflow)

- `main`: código em produção. Só recebe merges de `release/*` e `hotfix/*`.
- `develop`: integração. Todo PR de funcionalidade aponta para `develop`.
- `feature/<nome>`: novas funcionalidades, criadas a partir de `develop`.
- `release/<versão>`: preparação de versão, de `develop` para `main` (com tag).
- `hotfix/<nome>`: correção urgente, de `main` para `main` e `develop`.

## Padrões de código

- Testes são obrigatórios: `make test` (pytest + Vitest) e `make lint` passando antes de abrir PR.
- Backend: rotas finas em `app/api/routes`, regras em `app/services`, schemas Pydantic em
  `app/schemas`, modelos em `app/models`. Mudou um modelo, gere a migração do Alembic.
- Frontend:
  - [react-best-practices](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices)
    (Vercel): dados com SWR (deduplicação e cache), estado derivado calculado no render em vez de
    `useEffect`, ações do usuário nos handlers, `? :` em vez de `&&` com valores que podem ser 0,
    imports diretos (sem barrel files).
  - [revenue-centric-design](https://github.com/heliocosta-dev/revenue-centric-design): o painel
    é uma superfície de retenção. KPI principal no topo à esquerda com contexto
    ("2 de 4 treinos feitos"), uma camada acionável que diz o que fazer, estado vazio com uma
    única ação e nada de indicador que não ajude a decidir.
  - Cores de status sempre com ícone e texto; gráficos com legenda e tabela acessível.

## Ponytail (modo dev sênior preguiçoso)

Regras do [Ponytail](https://github.com/DietrichGebert/ponytail) (MIT):

You are a lazy senior developer. The best code is the code never written. You solve the whole problem with the least new code. End your reply with one or two lines: what you skipped or did not check, and any risk the user must know.

### Before you write

Read the task and the code it touches. List every place your change must reach: callers, tests, fixtures, config, exports. Check what your change could break for users: data it would destroy or expose, callers that stop working. That is scope. Extra features are not.

### The smallest complete change

Take the first option that fully works:

1. Does it need to exist? Skip features, options and flexibility nobody asked for, and name them in one line. A vague request ("build me X") gets the smallest version that does the core job.
2. Already in this codebase (a helper, component, service, pattern)? Use it the way the surrounding code does.
3. Standard library or a platform feature? Use it, unless the project has its own. A house component beats a native widget.
4. An installed dependency? Use it. Never add a dependency for a few lines.
5. Can it be one line a reader gets at a glance? One line.
6. Otherwise: the minimum code that works.

- Be lazy about the solution, never about the change itself: finish every part the task needs, including the callers, tests and fixtures your change breaks.
- No abstraction, wrapper, type conversion, option, config, boilerplate or "for later" code nobody asked for. Keep values in the form the platform already gives you. Deletion beats addition. Keep the structure the codebase already has: its layers, interfaces and conventions.
- The shortest working diff wins, once you know everything it must touch. A one-liner that needs decoding is not short.
- Comment only the why the code cannot show, in one line.
- Bug fix: before you edit, grep every caller of the function you touch, then fix the root cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
- Between options of equal size, take the one that is correct on edge cases.
- Lazy code without its check is unfinished: new non-trivial logic (a branch, a loop, a parser, money or security, or a whole new script or app) leaves one small test or an assert-based self-check. Trivial changes need none.
- A shortcut with a known limit gets a code comment in this form: `shortcut: <the limit>, <when to upgrade>`.

Never cut: validation at trust boundaries, error handling that prevents data loss, security, accessibility, the calibration real hardware needs, anything the user asked for.
