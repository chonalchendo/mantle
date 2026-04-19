---
issue: 76
title: Core init_vault — idempotent linking with outcome signal
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer with multiple projects on one machine, I want `init_vault` to link the current project to an existing vault instead of raising, so my second project's `config.md` is populated without hand-editing.

## Depends On

None — independent (foundational core change).

## Approach

Modify `core.project.init_vault` so it no longer raises `FileExistsError` when all four subdirs exist at the resolved vault path. Instead, it skips the `mkdir` loop, still calls `update_config(project_root, personal_vault=...)`, and returns a bool — `True` when a fresh vault was created, `False` when linking to a pre-existing one. This keeps core's semantics honest (idempotent) and gives the CLI (next story) enough signal to print distinct messages.

## Implementation

### `src/mantle/core/project.py` (modify)

Function: `init_vault(vault_path: Path, project_root: Path) -> bool` (was `-> None`).

1. Keep the `FileNotFoundError` guard for missing `.mantle/` (unchanged).
2. Compute `resolved = vault_path.expanduser().resolve()` and `subdirs = ("skills", "knowledge", "inbox", "projects")` (unchanged).
3. Replace the current `if all(... ): raise FileExistsError` block at line ~336-338 with:
   - `already_linked = all((resolved / d).is_dir() for d in subdirs)`
   - If not `already_linked`: run the existing `for d in subdirs: (resolved / d).mkdir(parents=True, exist_ok=True)` loop.
4. Always call `update_config(project_root, personal_vault=str(resolved))` unconditionally after the subdir handling.
5. Return `not already_linked` (i.e., `True` when the vault was freshly created, `False` when it was pre-existing and we just linked).
6. Update the docstring:
   - Summary: "Create or link a personal vault, then record it in this project's config."
   - Returns: "True if the vault was newly created, False if linked to an existing one."
   - Raises: drop `FileExistsError`; keep `FileNotFoundError`.

### Design decisions

- **Decision**: Return `bool` rather than an enum. Rationale: there are only two outcomes (fresh vs. linked), the CLI is the only caller, and a bool keeps the surface minimal. An enum would be overkill for a two-state signal.
- **Decision**: Always call `update_config` regardless of whether subdirs existed. Rationale: that is the fix — AC1 requires `personal_vault` to be recorded in both branches.
- **Decision**: Partial-state paths (some but not all subdirs exist) still run the `mkdir` loop — `exist_ok=True` handles existing dirs gracefully, so this matches today's `test_partial_init_completes` behaviour. No new branch needed.

## Tests

### `tests/core/test_project.py` (modify)

Delete the existing `test_raises_if_all_exist` (line 275-282) — its behaviour is being removed. Replace it with three new tests and update one, all inside `TestInitVault`:

- **test_returns_true_on_fresh_vault**: fresh `vault` path under `tmp_path`; `assert init_vault(vault, tmp_path) is True`.
- **test_returns_false_when_linking_existing_vault**: pre-create all four subdirs at `vault`; `assert init_vault(vault, tmp_path) is False` (no exception).
- **test_links_existing_vault_writes_config**: pre-create all four subdirs; call `init_vault`; `assert read_config(tmp_path)["personal_vault"] == str(vault.resolve())`. This covers AC1.
- **test_multi_project_share**: two project roots (`tmp_path / "proj_a"`, `tmp_path / "proj_b"`), each with its own `.mantle/config.md` (use `_create_config` helper); one shared `vault` path; call `init_vault(vault, proj_a)` then `init_vault(vault, proj_b)`. Assert both `config.md` files contain `personal_vault: <resolved vault path>`. This covers AC4.

Keep `test_creates_subdirectories`, `test_tilde_expansion`, `test_auto_sets_config`, `test_preserves_config_body`, `test_partial_init_completes`, `test_raises_if_mantle_missing` — they still hold.

### Test fixtures

All tests use the existing `_create_config(tmp_path)` helper and `tmp_path` (no real-vault access). No new fixtures required.