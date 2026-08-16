.DEFAULT_GOAL := help
UV ?= uv

.PHONY: help setup test test-ci lint ingest eval up down audit

help:
	@printf '%s\n' \
		'make setup  - install the locked local development environment' \
		'make ingest - acquire and normalize a 500-email development subset' \
		'make test   - run the full offline test suite' \
		'make lint   - run Ruff' \
		'make eval   - run the offline dense/BM25/hybrid retrieval evaluation' \
		'make up     - build and start the Docker Compose app' \
		'make down   - stop the Docker Compose app'

setup:
	@test -f .env || cp .env.example .env
	$(UV) sync --frozen --extra dev

test:
	$(UV) run pytest -q

test-ci:
	$(UV) run pytest -q --disable-warnings --maxfail=1

lint:
	$(UV) run ruff check src tests

ingest:
	PYTHONPATH=src $(UV) run --extra dev python -m securemail.ingestion.cli \
		--limit 500 --output data/sample/enron_dev_500.jsonl

eval:
	PYTHONPATH=src $(UV) run --extra dev python -m securemail.retrieval.phase03_cli \
		--data data/sample/enron_dev_500.jsonl

up:
	docker compose up --build

down:
	docker compose down

audit:
	@echo "Follow tasks/rubric_audit.md with Codex; this target is a placeholder for a future automated audit."
