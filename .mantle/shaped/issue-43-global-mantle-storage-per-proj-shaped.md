---
issue: 43
title: Global .mantle/ storage — per-project folders under ~/.mantle/
approaches:
- Thin Resolver — single resolve function, config flag, migration CLI
- Full Abstraction Layer — storage backend interface with local/global implementations
- Symlink Bridge — global storage with symlinks back to project root
chosen_approach: Thin Resolver — single resolve function, config flag, migration CLI
appetite: medium batch
open_questions:
- Should project identity use git remote URL hash or repo name? Remote URL is more
  stable but fails for repos without remotes.
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-07'
updated: '2026-04-07'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches

### Approach A: Thin Resolver (chosen)

Add a single function `resolve_mantle_dir(project_dir: Path) -> Path` to `core/project.py` that:
1. Checks `.mantle/config.md` for a `storage_mode: global` setting (defaults to `local`)
2. If local, returns `project_dir / ".mantle"` (current behaviour)
3. If global, computes project identity from git remote URL (fallback: repo root path hash) and returns `~/.mantle/projects/<identity>/`

All 22 core modules replace inline `project_dir / ".mantle"` with a call to this resolver. The CLI gains two new subcommands: `mantle storage --mode global` (configures) and `mantle migrate-storage` (moves files).

**Appetite**: Medium batch (3-5 days). The resolver itself is trivial; the bulk is mechanical replacement across 22 modules + testing + migration logic.

**Tradeoffs**: Minimal abstraction overhead. Single function, no new classes or interfaces. Every module still knows it's working with a Path — just gets the right one.

**Rabbit holes**: Ensuring the 79 inline `.mantle` references are all caught. Missing one means silent breakage in global mode.

**No-gos**: No support for multiple storage locations per project. No migration between two global locations.

### Approach B: Full Abstraction Layer

Create a `StorageBackend` protocol with `LocalStorage` and `GlobalStorage` implementations. All file operations go through the backend.

**Appetite**: Large batch (1-2 weeks). Over-engineered for the current need.

**Tradeoffs**: Maximum flexibility but adds an abstraction layer that leaks no information the current codebase needs.

**No-gos**: Not needed — the filesystem is already the abstraction.

### Approach C: Symlink Bridge

Store in `~/.mantle/projects/<id>/` always, create a `.mantle` symlink in the repo root pointing there.

**Appetite**: Small batch. Simple, but fragile — symlinks don't survive `git clone`, break on Windows, confuse some tools.

**Tradeoffs**: Zero code changes to path resolution, but shifts complexity to environment setup and breaks cross-platform.

**No-gos**: Not viable for workplace environments (the target use case) where symlink behavior varies.

## Chosen: Thin Resolver

Smallest approach that satisfies all ACs without introducing unnecessary abstraction.

## Code Design

### Strategy

1. **`core/project.py`** — Add `resolve_mantle_dir(project_dir: Path) -> Path` and `project_identity(project_dir: Path) -> str`. The resolver checks config for `storage_mode`, computes identity if global, and returns the correct base path. Add `GLOBAL_MANTLE_DIR = Path("~/.mantle/projects")`.

2. **All 22 core modules** — Replace `project_dir / ".mantle" / "subdir"` with `project.resolve_mantle_dir(project_dir) / "subdir"`. This is mechanical — same pattern everywhere.

3. **`core/migration.py`** (new) — `migrate_to_global(project_dir: Path) -> Path` and `migrate_to_local(project_dir: Path) -> Path`. Copies `.mantle/` contents to/from global location, updates config, verifies.

4. **`cli/storage.py`** (new) — Two subcommands: `mantle storage --mode global|local` (sets config), `mantle migrate-storage --direction global|local` (runs migration).

### Fits architecture by

- `resolve_mantle_dir()` lives in `core/project.py` alongside existing `MANTLE_DIR` constant and `init_project()` — natural home for path resolution
- Core-never-imports-CLI boundary preserved — migration logic in `core/`, CLI wiring in `cli/`
- Config stored in `.mantle/config.md` frontmatter using existing `read_config`/`update_config` pattern
- `project_identity()` uses `subprocess.run(["git", "remote", ...])` — same pattern as `state.py` git identity resolution

### Does not

- Does not add a StorageBackend abstraction (overkill, filesystem is the interface)
- Does not handle concurrent access to global storage (single-user tool)
- Does not migrate session logs or compiled commands (those are ephemeral)
- Does not change the personal vault path resolution (separate concern in `core/skills.py`)
- Does not support mixed mode (some files local, some global)
- Does not validate user input (CLI layer responsibility via cyclopts)