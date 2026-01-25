.PHONY: help install dev test test-cov lint format typecheck pre-commit docker-up docker-down

help:
	@echo "Vibomat Development Commands"
	@echo "  make test       Run tests (excludes CI-only)"
	@echo "  make test-cov   Run tests with coverage"
	@echo "  make lint       Run linters"
	@echo "  make format     Auto-format code"
	@echo "  make typecheck  Run type checker"
	@echo "  make dev        Start dev server"
	@echo "  make docker-up  Start Docker services"
	@echo "  make docker-down Stop Docker services"

test:
	PYTHONPATH=. uv run pytest backend/tests/ -m 'not ci' -v

test-cov:
	PYTHONPATH=. uv run pytest --cov=backend/core --cov=backend/app \
		--cov-fail-under=90 --cov-report=html backend/tests/ -m 'not ci'

lint:
	uv run ruff check .
	uv run black --check .

format:
	uv run black .
	uv run ruff check . --fix

typecheck:
	uv run ty check

dev:
	uv run uvicorn backend.app.main:app --reload

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down
