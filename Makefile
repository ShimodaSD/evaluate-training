.PHONY: install up down migrate test test-api test-web lint format

install:
	cd apps/api && uv sync
	cd apps/web && npm install

up:
	docker compose up --build

down:
	docker compose down

migrate:
	cd apps/api && uv run alembic upgrade head

test: test-api test-web

test-api:
	cd apps/api && uv run pytest

test-web:
	cd apps/web && npm test

lint:
	cd apps/api && uv run ruff check . && uv run ruff format --check .
	cd apps/web && npm run lint && npm run format:check && npm run typecheck

format:
	cd apps/api && uv run ruff check --fix . && uv run ruff format .
	cd apps/web && npm run format
