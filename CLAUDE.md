# Mantle

AI workflow engine with persistent context, integrated with Claude Code and Obsidian.

## Architecture

- `core/` never imports from `cli/` or `api/`
  - Enforced by `import-linter` — see `[tool.importlinter]` in `pyproject.toml`. The check runs as part of `just check` and CI.
  - To add another architectural invariant (e.g., `cli/` may not import `tests.fixtures`), append a new contract under `[[tool.importlinter.contracts]]`. No new tooling required.
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

## Baseline Skills

Some vault skills are auto-loaded based on project-level constraints,
independent of issue body matching. For example, any project with
`requires-python >= 3.14` in `pyproject.toml` gets the `python-314`
vault skill (when present) added to `skills_required` by
`mantle update-skills` and compiled by `mantle compile`. This ensures
agents working on 3.14+ code never misdiagnose valid PEP 758 syntax.
Baseline resolution lives in `core/baseline.py` — the mapping is a
flat function, not a plug-in registry.

## Test Conventions

- Framework: pytest
- Test directory mirrors `src/mantle/` structure (e.g. `tests/core/test_manifest.py` for `src/mantle/core/manifest.py`)
- Top-level `tests/test_package.py` and `tests/test_workflows.py` for project-wide and infrastructure tests
- Use `tmp_path` for isolated file operations — never touch real `~/.claude/` or real vaults
- No LLM calls in tests
- Test external behaviour, not internal implementation details
- Mock boundaries (filesystem, network), not internal functions
- Use `inline_snapshot` (`from inline_snapshot import snapshot`) for tests asserting exact-string CLI output, rendered markdown, or generated artefacts. `assert rendered == snapshot()` starts empty and is auto-filled by `uv run pytest --inline-snapshot=create`; review the diff before committing. Never hand-edit a snapshot literal.
- Use `dirty-equals` (`IsPartialDict`, `IsList(..., check_order=False)`, `IsDatetime`, `IsNow`, `IsStr(regex=...)`) for partial or unordered comparisons — replaces hand-written attribute-by-attribute asserts and sort-then-compare helpers. Pair with `inline_snapshot` for captures that need to tolerate unstable fields.
- Scenario fixtures in `tests/conftest.py` follow the naming convention `vault_with_<state>` or `<noun>_after_<event>`; the docstring describes the scenario. One fixture = one named scenario.
- Don't mix the two tools in a single assertion without intent: `inline_snapshot` captures values, `dirty-equals` captures shape.

## Commit Messages

Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`

## Releasing

1. `uv version --bump patch` (or `minor` / `major`)
2. Update `src/mantle/__init__.py` to match the new version
3. Update the `## Status` section in `README.md` with the new version and a one-line summary of what's included (match the milestone description from the product design)
4. Add a new entry to `CHANGELOG.md` under the new version header with the date and grouped Added/Changed/Fixed notes; add the matching comparison link at the bottom of the file
5. `git add pyproject.toml uv.lock src/mantle/__init__.py README.md CHANGELOG.md`
6. `git commit -m "release: v$(uv version)"`
7. `git tag "v$(uv version)"`
8. `git push && git push --tags`

The `publish.yml` workflow handles build, smoke test, and PyPI upload via trusted publishers.
