---
issue: 76
title: CLI init-vault — distinct linked-vs-created message
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a developer running `mantle init-vault` on a path already used by another project, I want a clear confirmation that my current project was linked to the existing vault (not a misleading "Nothing to do"), so I can trust the command and verify the result without reading source.

## Depends On

Story 1 — requires `core.project.init_vault` returning `bool` and no longer raising `FileExistsError`.

## Approach

Thin CLI formatting change. The CLI calls the now-idempotent `core.project.init_vault`, captures the bool return, and routes to one of two message branches: the existing "Created personal vault" block when the vault was fresh (return `True`), or a new "Linked existing vault" block when it already existed (return `False`). The `FileExistsError` handler is removed because core no longer raises it. Follows `cli-design-best-practices`: distinct phrases so scripts can grep either outcome; success path always exits 0.

## Implementation

### `src/mantle/cli/init_vault.py` (modify)

Rewrite `run_init_vault(vault_path: Path) -> None` so it:

1. Resolves `project_root = Path.cwd()` (unchanged).
2. Calls `created = project.init_vault(vault_path, project_root)` inside a `try` that handles only `FileNotFoundError` (project not initialised) — same `errors.exit_with_error` branch as today. **Delete the `except FileExistsError` block entirely.**
3. Resolves `resolved = vault_path.expanduser().resolve()` (unchanged).
4. Branches on `created`:
   - `if created:` emit the existing block — blank line, `[green]Created personal vault at {resolved}[/green]`, then the three subdir lines (`skills/`, `knowledge/`, `inbox/`), blank line, `Vault path saved to .mantle/config.md`, and the iCloud tip.
   - `else:` emit a new block — blank line, `[green]Linked existing vault at {resolved}[/green]`, then a single line `Vault path saved to .mantle/config.md` (no subdir listing or iCloud tip, since nothing was created).

### Design decisions

- **Decision**: Two distinct message blocks (not one parameterised template). Rationale: the information density differs — the fresh-vault block teaches the user about structure and the iCloud sync tip, which is irrelevant when just linking. Duplicating 3 lines keeps intent obvious.
- **Decision**: "Linked existing vault at {path}" as the exact phrase (from the issue's proposed flow, AC2). Scripts that previously grepped "Nothing to do" will need to update, but that message was a bug signal, not a contract.
- **Decision**: Still print "Vault path saved to .mantle/config.md" in the linked branch — it truthfully describes what just happened and matches AC1's intent.
- **Decision**: `projects/` is still not listed in the created-vault output, matching current behaviour — out of scope to change here.

## Tests

### `tests/cli/test_init_vault.py` (modify)

Replace `test_prints_warning_on_existing` (line 52-70) with two tests inside `TestRunInitVault`:

- **test_prints_linked_message_for_existing_vault**: pre-create all four subdirs at `tmp_path / "vault"`, call `run_init_vault(vault)`, assert `"Linked existing vault"` is in `capsys.readouterr().out` and `"Nothing to do"` is NOT in the output.
- **test_populates_config_when_linking_existing_vault**: same setup; after calling `run_init_vault(vault)`, read `(tmp_path / MANTLE_DIR / "config.md")` via `mantle.core.project.read_config(tmp_path)` and assert `result["personal_vault"] == str(vault.resolve())`. This is the CLI-layer coverage of AC1 (end-to-end through the CLI entry point).

Keep `test_prints_success` (fresh-vault happy path) — still passes, proves no regression of AC3.
Keep `test_prints_error_when_not_initialized` — `FileNotFoundError` handling unchanged.
Keep `TestCLIWiring::test_init_vault_help` — CLI surface unchanged.

### Test fixtures

Uses the existing `_create_project(tmp_path)` helper in the same file (line 19-25) and `capsys` / `monkeypatch.chdir`. No new fixtures required. Import `read_config` from `mantle.core.project` (local import inside the test function to match the file's existing style of importing `run_init_vault` lazily).