.PHONY: install test lint typecheck verify demo-draft

install:
	uv sync --extra dev

test:
	uv run pytest -q

lint:
	uv run ruff check src tests scripts
	uv run ruff format --check src tests scripts

typecheck:
	uv run mypy src

demo-draft:
	uv run python scripts/gen_demo_draft.py

verify: lint typecheck test
