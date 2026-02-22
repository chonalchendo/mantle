---
issue: 1
title: Development tooling (justfile, ruff, ty, prek, pytest)
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Set up all development tooling so `just check` validates the codebase from day one.

### justfile

At repo root:

```just
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
```

### Ruff config in pyproject.toml

```toml
[tool.ruff]
line-length = 80
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "RUF", "B", "SIM", "TCH"]
ignore = ["E501"]  # Line length handled by formatter

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### ty config in pyproject.toml

```toml
[tool.ty]
python-version = "3.14"
```

### pytest config in pyproject.toml

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --strict-markers --tb=short"
```

### .pre-commit-config.yaml (prek-compatible)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### Install prek hooks

Add note to CLAUDE.md about running `prek install` to set up git hooks.

## Tests

- `just --list` shows all recipes (install, lint, format, type, test, check, ci, fix)
- `just check` passes on the skeleton codebase without errors
- `ruff check src/ tests/` passes
- `ruff format src/ tests/ --check` passes (code is already formatted)
- `ty check src/` runs without errors on the minimal codebase
- `uv run pytest` discovers and runs the tests from story 1
