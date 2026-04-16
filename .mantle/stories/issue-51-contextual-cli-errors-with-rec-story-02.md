---
issue: 51
title: Migrate all CLI error paths to errors.exit_with_error
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a mantle user, I want every CLI error to end with a specific recovery hint so that when a command fails I know exactly what to do next without guessing.

## Depends On

Story 1 — imports `mantle.cli.errors`.

## Approach

Mechanical migration pass across every `src/mantle/cli/*.py` module. Every existing `console.print("[red]Error:[/red] ...")` followed by `raise SystemExit(...)` (or bare return) becomes a single `errors.exit_with_error("...", hint="...")` call. Each site needs an appropriate, specific hint derived from the error condition. Rich-style messages keep the same tone ("Run `mantle init` to create a project"). Tests are integration-style — run one representative command from each family under `capsys` / cyclopts' testing idiom and assert the stderr output matches the expected shape.

## Implementation

### src/mantle/cli/*.py (modify — migration pass)

For every file that currently prints a red-error line, replace the pair:

```python
console.print(f"[red]Error:[/red] <msg>")
raise SystemExit(1)
```

with:

```python
errors.exit_with_error("<msg>", hint="<recovery>")
```

Add `from mantle.cli import errors` at the top of each touched file.

Files to migrate (with hint direction — call sites already have the message):

- **cli/compile.py** — "no .mantle/ directory found" → hint: `Run 'mantle init' to create a project`.
- **cli/init_vault.py** — "project not initialized" → hint: `Run 'mantle init' first`.
- **cli/install.py** — "bundled claude/ not found" → hint: `Reinstall mantle with 'uv tool install mantle'`.
- **cli/skills.py** — "personal vault not configured" → hint: `Set vault_path in ~/.mantle/config.yaml or run 'mantle init-vault'`. Also the generic `except Exception as exc` → hint: `See the error above; file a bug at https://github.com/chonalchendo/mantle/issues if unexpected`.
- **cli/issues.py** — "cannot plan issues from <phase>" → hint: `Run 'mantle design-product' first`.
- **cli/stories.py** — "story N for issue M not found" → hint: `Check the story ID with 'mantle list-stories --issue M'`.
- **cli/review.py** — "issue N not found" → hint: `Check the issue number with 'mantle list-issues'`. "no review found for issue N" → hint: `Run 'mantle review-issue --issue N' first`. "Cannot transition to '<target>'" → hint: `Run 'mantle verify-issue --issue N' first`.
- **cli/verify.py** — "Cannot transition to 'verified'" → hint: `Run 'mantle verify-issue --issue N' first to record verification result`.
- **cli/storage.py** — "Invalid storage mode" → hint: `Use 'local', 'remote', or 'both'`. "Invalid direction" → hint: `Use 'push' or 'pull'`. Generic `except Exception as exc` → hint: `See the error above; file a bug at https://github.com/chonalchendo/mantle/issues if unexpected`.
- **cli/adopt.py** — "project at wrong phase" → hint: `Back up .mantle/ and re-run 'mantle init' if you want to restart`.
- **cli/inbox.py** — generic catches → hint: `See the error above; file a bug at https://github.com/chonalchendo/mantle/issues if unexpected`. "Inbox item not found" → hint: `List inbox items with 'mantle list-inbox'`.
- **cli/bugs.py** — "Bug not found" → hint: `List bugs with 'mantle list-bugs'`. Generic catches → the fallback bug-report hint.
- **cli/knowledge.py** — "--topic is required" → hint: `Pass a topic like: mantle query --topic pyproject`. Generic catches → fallback hint.
- **cli/learning.py** — generic catches → fallback hint.
- **cli/research.py** — "No issue file found for issue N" → hint: `Check the issue number with 'mantle list-issues'`. Generic catches → fallback hint.
- **cli/brainstorm.py** — generic catches → fallback hint.
- **cli/scout.py** — generic catches → fallback hint.

For sites that currently *don't* raise SystemExit (e.g., `console.print("[red]Error:[/red] ...")` with bare return) — convert them to `errors.exit_with_error(...)` so the CLI exits non-zero. The acceptance criterion says non-zero exit code is part of the error contract.

`main.py`'s informational `print(..., file=sys.stderr)` lines (e.g., "Updated skills_required in state.md.") are **status messages, not errors** — leave them alone. The migration is about error paths only.

#### Design decisions

- **Each call site carries its hint as a literal**: no central catalogue. Hints are context-specific and live closest to the message they pair with.
- **Generic `except Exception as exc` handlers get a fallback hint** pointing to the bug tracker — matches the cli-design-best-practices "unexpected errors should provide a bug-report path" guidance.
- **Do not change exit codes**: every existing site exits 1; keep that.
- **Do not touch `main.py` status prints**: they are not errors.
- **Do not migrate `core/` raises**: they bubble to the CLI layer where the migrated handlers already call `exit_with_error`.

### tests/cli/test_errors_integration.py (new file)

Verify the migration end-to-end via cyclopts' testing idiom. Import the `app` from `mantle.cli.main` and drive representative error paths:

- **test_compile_outside_project_exits_with_hint**: run `mantle compile` from a `tmp_path` cwd with no `.mantle/` directory; assert SystemExit(1); assert stderr contains `Error:` and `mantle init`.
- **test_skills_without_vault_exits_with_hint**: stub vault config to be unset; run `mantle list-skills`; assert stderr contains both the error prefix and the `vault_path` hint.
- **test_review_for_missing_issue_exits_with_hint**: with `.mantle/` initialised but no issue 999, run `mantle review-issue --issue 999`; assert stderr contains the `mantle list-issues` hint.
- **test_errors_go_to_stderr_not_stdout**: pick one representative command; assert stdout is empty for the error case and stderr contains the formatted message.

These tests use `monkeypatch` to set cwd to `tmp_path` and drive via `app("<args>", result_action="return_value")` per the cyclopts skill. No mocks on `mantle.cli.errors` itself — black-box the migration.

## Tests

See above — integration tests live in `tests/cli/test_errors_integration.py`. Unit tests for `errors.py` are story 1.

Additionally, **after the migration pass**, run `uv run pytest` end-to-end — all 1171 existing tests must still pass, plus the new tests. If any test previously asserted `[red]Error:[/red]` in stdout (unlikely but possible), update it to capture stderr.