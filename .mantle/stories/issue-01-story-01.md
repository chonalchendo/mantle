---
issue: 1
title: Package skeleton, project standards, and CLAUDE.md
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Create the foundational package structure that makes `mantle` installable and runnable.

### pyproject.toml

Hatchling build backend with src-layout:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mantle-ai"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "cyclopts>=3.0",
    "rich>=13.0",
    "omegaconf>=2.3",
    "pydantic>=2.0",
    "jinja2>=3.1",
]

[project.scripts]
mantle = "mantle.cli.main:app"

[tool.hatch.build.targets.wheel]
packages = ["src/mantle"]

[tool.hatch.build.targets.wheel.force-include]
"claude" = "mantle/claude"
"vault-templates" = "mantle/vault-templates"
```

Dependency groups for dev tooling:

```toml
[dependency-groups]
dev = ["pytest>=8.0", "pytest-cov>=5.0"]
lint = ["ruff>=0.11"]
type = ["ty>=0.0"]
hooks = ["prek>=0.3"]
check = [{include-group = "dev"}, {include-group = "lint"}, {include-group = "type"}]
```

### Directory structure

```
src/mantle/__init__.py          # __version__ = "0.1.0"
src/mantle/core/__init__.py     # Empty
src/mantle/cli/__init__.py      # Empty
src/mantle/cli/main.py          # Cyclopts app with install placeholder
src/mantle/py.typed             # PEP 561 marker
claude/commands/mantle/         # Empty dir (populated in later stories)
vault-templates/                # Empty dir (populated in later stories)
tests/__init__.py               # Empty
tests/test_package.py           # Package-level tests
```

### src/mantle/cli/main.py

Bare Cyclopts app:

```python
from cyclopts import App

app = App(name="mantle", help="AI workflow engine with persistent context.")

@app.command
def install() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    raise NotImplementedError("Install command not yet implemented.")

if __name__ == "__main__":
    app()
```

### CLAUDE.md

Project-level CLAUDE.md at repo root with:

- Project overview (what Mantle is, single sentence)
- Architecture rule: `core/` never imports from `cli/` or `api/`
- Python version: 3.14+
- How to install for development: `uv sync --group check`
- How to run tests: `uv run pytest`
- How to run all checks: `just check`
- Coding standards: Follow Google Python Style Guide (reference the skill)
  - Type hints on all public functions
  - Google-style docstrings on all public modules, classes, functions
  - 80 char line length
  - Absolute imports only
  - Never bare `except:`
  - Never mutable default arguments
- Test conventions: pytest, tmp directories for vault mocking, no LLM calls, test external behaviour not internals
- Commit message format: conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`)

### .gitignore

Python defaults, `.claude/worktrees/`, `dist/`, `*.egg-info`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, `.ty_cache`.

## Tests

- `mantle` package is importable
- `mantle.__version__` returns a string matching semver pattern
- `mantle install --help` outputs help text (subprocess call to `uv run mantle install --help`)
- `mantle --help` lists `install` as a subcommand
- CLAUDE.md exists at repo root
- .gitignore exists at repo root
