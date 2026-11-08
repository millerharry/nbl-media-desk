.PHONY: install lint format typecheck test check eval

install:      ## Install dependencies and git hooks
	uv sync
	uv run pre-commit install

lint:         ## Lint and check formatting
	uv run ruff check .
	uv run ruff format --check .

format:       ## Auto-format
	uv run ruff check --fix .
	uv run ruff format .

typecheck:    ## Strict type check
	uv run mypy

test:         ## Unit tests with coverage
	uv run pytest --cov --cov-report=term-missing

check: lint typecheck test   ## Everything CI runs
	uv run python scripts/check_no_feed_data.py

eval:         ## Run eval suites (Phase 3e)
	@echo "Eval harness arrives in Phase 3e. See evals/README.md."
