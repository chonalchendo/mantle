---
issue: 43
title: Core resolver — resolve_mantle_dir and project_identity
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer in a workplace with strict git policies, I want Mantle to resolve the .mantle/ directory through a central function so that storage location can be configured without changing every module.

## Depends On

None — independent (foundation story).

## Approach

Add two pure functions to `core/project.py`: `project_identity()` derives a stable project ID from git remote URL (fallback: repo root path), and `resolve_mantle_dir()` reads config to decide between local and global storage paths. Follows the existing pattern of project.py as the home for structure constants and path logic. Adds `storage_mode` field to config frontmatter.

## Implementation

### src/mantle/core/project.py (modify)

Add two public functions after the existing `init_project()`:

1. **`project_identity(project_dir: Path) -> str`**
   - Run `git -C <project_dir> remote get-url origin` via subprocess
   - If remote exists, hash it with `hashlib.sha256` and take first 12 hex chars
   - Prefix with a slugified repo name: `<repo-name>-<hash12>`
   - If no remote (exit code != 0), hash the resolved absolute path instead
   - Return the identity string

2. **`resolve_mantle_dir(project_dir: Path) -> Path`**
   - Try to read `.mantle/config.md` frontmatter for `storage_mode` key
   - If `storage_mode == "global"`, compute identity via `project_identity()` and return `Path.home() / ".mantle" / "projects" / identity`
   - Otherwise (missing config, missing key, or `storage_mode == "local"`), return `project_dir / MANTLE_DIR`
   - This function must NOT create directories — just resolve the path

3. Add constant: `GLOBAL_MANTLE_ROOT = ".mantle/projects"` (relative to home)

4. Update `_ConfigFrontmatter` to include `storage_mode: str | None = None`

#### Design decisions

- **Hash-based identity**: Using SHA256 of git remote URL gives a stable identity that survives repo moves on disk. The 12-char prefix is sufficient for uniqueness while keeping paths readable.
- **Slug prefix**: `myrepo-a1b2c3d4e5f6` is more readable than a bare hash in `~/.mantle/projects/`.
- **No directory creation**: The resolver only computes paths. `init_project()` and `migrate_to_global()` handle creation. This keeps the resolver side-effect-free.
- **Graceful fallback**: If config doesn't exist or storage_mode isn't set, default to local. This preserves backward compatibility.

## Tests

### tests/core/test_project.py (modify)

- **test_project_identity_with_remote**: Mock `subprocess.run` to return a remote URL, verify identity format is `<name>-<hash12>`.
- **test_project_identity_without_remote**: Mock `subprocess.run` to fail (no remote), verify identity is derived from path hash.
- **test_project_identity_stable**: Same input produces same output across calls.
- **test_resolve_mantle_dir_default_local**: No config → returns `project_dir / ".mantle"`.
- **test_resolve_mantle_dir_explicit_local**: Config has `storage_mode: local` → returns `project_dir / ".mantle"`.
- **test_resolve_mantle_dir_global**: Config has `storage_mode: global` → returns `~/.mantle/projects/<identity>`.
- **test_resolve_mantle_dir_missing_config**: No `.mantle/config.md` → returns local path (no crash).