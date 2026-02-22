# Mantle development tasks
# Run 'just' to list all available recipes

default:
    @just --list

# Install project with all dev dependencies
install:
    uv sync --group check

# Run linter
lint *args:
    uv run ruff check src/ tests/ {{args}}

# Run formatter
format *args:
    uv run ruff format src/ tests/ {{args}}

# Run type checker
type:
    uv run ty check src/

# Run tests
test *args:
    uv run pytest {{args}}

# Run all checks (lint, format check, type, test)
check: lint type test
    uv run ruff format src/ tests/ --check
    @echo "All checks passed."

# CI mode (non-destructive, used in GitHub Actions)
ci:
    uv run ruff check src/ tests/
    uv run ruff format src/ tests/ --check
    uv run ty check src/
    uv run pytest

# Auto-fix lint and format issues
fix:
    uv run ruff check src/ tests/ --fix
    uv run ruff format src/ tests/
