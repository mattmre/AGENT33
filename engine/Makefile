.PHONY: up down build test lint fmt check

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

test:
	pytest tests/ -v

lint:
	ruff check src/ tests/
	mypy src/

fmt:
	ruff format src/ tests/
	ruff check --fix src/ tests/

check: lint test

dev:
	uvicorn agent33.main:app --reload --host 0.0.0.0 --port 8000

pull-model:
	docker compose exec ollama ollama pull $(MODEL)
