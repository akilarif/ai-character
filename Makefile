PYTHON ?= python

.PHONY: run lint format-check typecheck test validate

run:
	uv run $(PYTHON) backend/main.py

lint:
	uv run ruff check .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy

test:
	uv run pytest

validate: lint format-check typecheck test
