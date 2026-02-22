# Mantle

AI workflow engine with persistent context, integrated with Claude Code and Obsidian.

## Architecture

- `core/` never imports from `cli/` or `api/`
- `cli/` depends on `core/`, never the reverse
- All state lives in `.mantle/` (local) or the Obsidian vault

## Development

- Python 3.14+
- Install for development: `uv sync --group check`
- Run tests: `uv run pytest`
- Run all checks: `just check`
- Auto-fix lint/format: `just fix`

## Coding Standards

Follow the Google Python Style Guide (see `google-python-style` skill).

- Type hints on all public functions
- Google-style docstrings on all public modules, classes, and functions
- 80 character line length
- Absolute imports only
- Never bare `except:`
- Never mutable default arguments

## Test Conventions

- Framework: pytest
- Use `tmp_path` for isolated file operations — never touch real `~/.claude/` or real vaults
- No LLM calls in tests
- Test external behaviour, not internal implementation details
- Mock boundaries (filesystem, network), not internal functions

## Commit Messages

Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`
