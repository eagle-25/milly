# Makefile for Docker Compose management

.PHONY: up down mypy lint format check test

# Start services
up:
	docker-compose up --build -d

# Stop services
down:
	docker-compose down

mypy:
	uv run mypy .

lint:
	uv run ruff check . --fix
	uv run ruff format 

check: format lint mypy

install:
	uv sync

test:
	uv run python -m pytest -s
