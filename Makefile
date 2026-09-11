.PHONY: install test lint typecheck verify

install:
	uv sync --extra dev

test:
	uv run pytest -q

lint:
	uv run ruff check src tests
	uv run ruff format --check src tests

typecheck:
	uv run mypy src

verify: lint typecheck test
