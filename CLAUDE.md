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
- Set up git hooks: `prek install`

## Coding Standards

Follow the Google Python Style Guide (see `google-python-style` skill).

- Type hints on all public functions
- Google-style docstrings on all public modules, classes, and functions
- 80 character line length
- Absolute imports only
- Import modules, not individual names: `from mantle.core import vault` then `vault.read_note(...)`, not `from mantle.core.vault import read_note`
- Never bare `except:`
- Never mutable default arguments

## Test Conventions

- Framework: pytest
- Test directory mirrors `src/mantle/` structure (e.g. `tests/core/test_manifest.py` for `src/mantle/core/manifest.py`)
- Top-level `tests/test_package.py` and `tests/test_workflows.py` for project-wide and infrastructure tests
- Use `tmp_path` for isolated file operations — never touch real `~/.claude/` or real vaults
- No LLM calls in tests
- Test external behaviour, not internal implementation details
- Mock boundaries (filesystem, network), not internal functions

## Commit Messages

Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`

## Releasing

1. `uv version --bump patch` (or `minor` / `major`)
2. Update `src/mantle/__init__.py` to match the new version
3. `git add pyproject.toml uv.lock src/mantle/__init__.py`
4. `git commit -m "release: v$(uv version)"`
5. `git tag "v$(uv version)"`
6. `git push && git push --tags`

The `publish.yml` workflow handles build, smoke test, and PyPI upload via trusted publishers.
