---
issue: 47
title: Remove global-mode .mantle/config.md stub — detect by global dir existence
approaches:
- dir-existence-as-signal
- keep-sentinel-marker-file
- env-var-or-global-index
chosen_approach: dir-existence-as-signal
appetite: small batch
open_questions:
- run_storage (the CLI command that writes storage_mode to config.md) becomes a no-op
  under the new resolver. Should it be deprecated or repurposed as an alias for migrate-storage?
  Out of scope here.
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-09'
updated: '2026-04-09'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Problem

Global-storage mode promises zero `.mantle/` footprint in work repos. Current code violates that contract: `core/migration.py::migrate_to_global` rebuilds a stub `.mantle/config.md` with `storage_mode: global` because `core/project.py::resolve_mantle_dir` reads that stub to detect global mode. The stub is load-bearing for the resolver but directly breaks the user-facing guarantee.

Practical trigger: user wants to run claude-code sessions from git worktrees and rely on global mantle context. Worktrees share the same git origin → same `project_identity()` → same `~/.mantle/projects/<identity>/`. This only works if the resolver stops requiring the in-repo stub.

## Approaches considered

### A — Dir-existence as signal (CHOSEN)

Move detection entirely out of the project directory. The existence of `~/.mantle/projects/<project_identity()>/` is the signal; no in-repo marker required.

- **Appetite:** small batch
- **Tradeoffs:** simplest possible solution, zero project-dir footprint, worktrees work for free via shared identity. Loses the ability to explicitly mark a project as 'locally global-mode intended' before actual migration — but there was no legitimate use for that state.
- **Rabbit holes:** test rewrites are mechanical but touch 4 files. `run_storage` CLI becomes a no-op (write-only field nobody reads) — flagged as open question, not fixed here.
- **No-gos:** no changes to `project_identity()`, no migration of existing project state, no new CLI commands.

### B — Keep a sentinel marker file (`.mantle/.storage-mode-global`)

Rejected. Still violates the 'no footprint' contract (any file under `.mantle/` is footprint).

### C — Environment variable or global index file (`~/.mantle/index.md`)

Rejected. Env vars fail the worktree AC (would require per-shell setup). A global index file is redundant — the filesystem itself is already an index when you check for directory existence.

## Code design

### Strategy

Two small production edits plus test migration.

1. **`core/project.py::resolve_mantle_dir`** — replace config-read with directory-existence check:
   ```python
   def resolve_mantle_dir(project_dir: Path) -> Path:
       identity = project_identity(project_dir)
       global_dir = pathlib.Path.home() / GLOBAL_MANTLE_ROOT / identity
       if global_dir.exists():
           return global_dir
       return project_dir / MANTLE_DIR
   ```
   Drop the `_read_frontmatter_and_body(config_path)` call and the `FileNotFoundError` guard from this path. `_read_frontmatter_and_body` stays — still used by `read_config`/`update_config`.

2. **`core/migration.py::migrate_to_global`** — drop the stub rebuild block (lines 48–57). Replace with a plain `shutil.rmtree(source)` under `if remove_local:`. Also drop the `_update_config_at(target, storage_mode='global')` call that follows the copy — the `storage_mode` field is no longer meaningful (dead write). The copy is the migration; the directory's *existence* at the expected path is the signal.

3. **`core/migration.py::migrate_to_local`** — drop the symmetric `_update_config_at(local, storage_mode='local')` call. Again: field is ignored by the resolver, no reason to keep writing it.

### Test migration

- `tests/core/test_project.py::TestResolveMantleDir::test_global` — rewrite: create the global dir under a monkeypatched `Path.home()` and assert the resolver returns it. Remove the 'write config.md stub' setup.
- `tests/core/test_migration.py::TestMigrateToGlobal` — delete `test_leaves_stub` and rewrite `test_removes_local_contents` to assert `.mantle/` is fully gone after migration.
- `tests/cli/test_storage.py::TestMigrateStorage::test_migrate_storage_error` — rewrite: after first successful migration, calling `run_migrate_storage --direction global` again should fail because the global target already exists (no stub-rebuild trick needed).
- `tests/cli/test_storage.py::TestWhere::test_where_global_mode` — rewrite: call `migrate_to_global` in setup (or pre-create the global dir) instead of writing a config stub.
- `tests/test_global_mode_workflow.py::test_global_project_local_mantle_is_stub_only` — rename to `test_global_project_local_mantle_is_absent` and assert `(project_dir / '.mantle').exists()` is False.
- **New test** (AC #4 — worktree scenario): two directories monkeypatched to share the same `project_identity()` both resolve to the same global dir under a fake home.

### Fits architecture by

- Stays entirely within `core/` — no cli↔core coupling introduced.
- Honours the core-never-imports-cli boundary from `designing-architecture`.
- Reuses `project_identity()` as the sole cross-directory identity primitive — no new abstraction.
- Aligns the implementation with the stated user contract in `product-design.md` and issues 43/44.

### Does not

- **Does not remove or repurpose `run_storage`.** The `mantle storage --mode global` CLI still writes `storage_mode` to `config.md`. Under the new resolver that field is ignored — effectively dead write. Out of scope; see open questions.
- **Does not auto-migrate existing users.** Users who previously ran `migrate_to_global` and still have a local stub `.mantle/config.md` plus a populated global dir will just silently resolve to global under the new rules (dir exists → wins). The stub becomes harmless residue; they can `rm -rf .mantle/` manually.
- **Does not handle the edge case where both `project_dir/.mantle/` has real content AND `~/.mantle/projects/<identity>/` exists.** Global wins silently; no user warning. Migration-anomaly only; out of scope.
- **Does not change `project_identity()`** — identity comes from git remote via the existing unchanged function.
- **Does not touch user-facing help text or docs** for `mantle storage` / `mantle migrate-storage`.
- **Does not gitignore `.mantle/`** in any generated output — the user controls their own .gitignore.