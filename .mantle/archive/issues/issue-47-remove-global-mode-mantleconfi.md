---
title: Remove global-mode .mantle/config.md stub — detect by global dir existence
status: approved
slice:
- core
- tests
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- Production Project Readiness
- Python package structure
- cyclopts
- omegaconf
- pydantic-discriminated-unions
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: After running the migrate-to-global command, the project directory contains
    no `.mantle/` folder whatsoever.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: '`mantle where` continues to print the correct global path for a migrated
    project.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: '`resolve_mantle_dir` returns the global path iff `~/.mantle/projects/<identity>/`
    exists, otherwise `project_dir/.mantle/`. No path depends on reading `.mantle/config.md`
    for `storage_mode`.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: A `git worktree add` from a migrated repo resolves to the same `~/.mantle/projects/<identity>/`
    as its parent with no in-repo setup and no additional commands run inside the
    worktree.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: '`migrate_to_local` still works end-to-end: creates a fresh local `.mantle/`,
    copies global contents, removes the global directory.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Local-mode projects that never migrated are unaffected.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: '`tests/core/test_project.py`, `tests/core/test_migration.py`, `tests/cli/test_storage.py`,
    and `tests/test_global_mode_workflow.py` are updated to the new detection semantics
    and pass.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: 'A new test covers the worktree scenario: two directories with the same `project_identity()`
    both resolve to the same global dir.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Global-storage mode (issues 43/44) was designed to let users keep mantle out of their project repo entirely — the stated user contract is that work repos must have no `.mantle/` artifact at all. But the current implementation contradicts that contract: `core/migration.py::migrate_to_global` (lines 48–57) intentionally rebuilds a stub `.mantle/config.md` with `storage_mode: global` after copying contents to `~/.mantle/projects/<identity>/`, because `core/project.py::resolve_mantle_dir` (lines 178–205) reads that stub to detect global mode. The stub is load-bearing for the resolver but directly breaks the user-facing guarantee.

Practical impact for the user right now: they have started using mantle at work and want zero `.mantle/` footprint in work repos. Their plan is to spin up claude-code sessions inside git worktrees and rely on global mantle context, because worktrees share the same `git origin` URL → same `project_identity()` → same `~/.mantle/projects/<identity>/` directory → same context. This plan works only if the resolver stops requiring the in-repo stub. Today it cannot.

Captured as inbox item `bug-global-storage-mode-still.md`.

## What to build

Move global-mode detection out of the project directory entirely. The existence of `~/.mantle/projects/<project_identity()>/` is itself the signal — no in-repo marker needed. The identity hash is already derived from the git remote URL, so worktrees inherit the correct global context for free.

Proposed changes (production delta ~15 lines):

1. `core/project.py::resolve_mantle_dir`:
   - Compute `identity = project_identity(project_dir)`
   - If `Path.home() / GLOBAL_MANTLE_ROOT / identity` exists, return it
   - Otherwise return `project_dir / MANTLE_DIR`
   - Drop the `.mantle/config.md` frontmatter read entirely from this path
2. `core/migration.py::migrate_to_global`:
   - Drop lines 48–57 that rebuild the stub `config.md`
   - `shutil.rmtree(source)` already runs above; the directory can simply stay gone
3. `core/migration.py::migrate_to_local`: no change — it already writes a fresh local `.mantle/` from scratch.
4. Test migration: `tests/core/test_project.py`, `tests/core/test_migration.py`, `tests/cli/test_storage.py`, and `tests/test_global_mode_workflow.py` currently scaffold global-mode projects by writing `config.md` with `storage_mode: global`. Update them to create the global dir under a monkeypatched `~/.mantle/projects/...` instead.

### Flow

1. User runs the global-mode migration command on a project.
2. Contents of `.mantle/` are copied to `~/.mantle/projects/<identity>/`.
3. The local `.mantle/` directory is removed entirely — the project directory contains no mantle artifacts.
4. Subsequent calls to `mantle where` (and every prompt that relies on it) compute `project_identity()` from the git remote, see that `~/.mantle/projects/<identity>/` exists, and resolve to it.
5. A `git worktree add` from the same repo produces a new working directory that resolves to the same global context with zero in-repo setup.

## Acceptance criteria

- [ ] ac-01: After running the migrate-to-global command, the project directory contains no `.mantle/` folder whatsoever.
- [ ] ac-02: `mantle where` continues to print the correct global path for a migrated project.
- [ ] ac-03: `resolve_mantle_dir` returns the global path iff `~/.mantle/projects/<identity>/` exists, otherwise `project_dir/.mantle/`. No path depends on reading `.mantle/config.md` for `storage_mode`.
- [ ] ac-04: A `git worktree add` from a migrated repo resolves to the same `~/.mantle/projects/<identity>/` as its parent with no in-repo setup and no additional commands run inside the worktree.
- [ ] ac-05: `migrate_to_local` still works end-to-end: creates a fresh local `.mantle/`, copies global contents, removes the global directory.
- [ ] ac-06: Local-mode projects that never migrated are unaffected.
- [ ] ac-07: `tests/core/test_project.py`, `tests/core/test_migration.py`, `tests/cli/test_storage.py`, and `tests/test_global_mode_workflow.py` are updated to the new detection semantics and pass.
- [ ] ac-08: A new test covers the worktree scenario: two directories with the same `project_identity()` both resolve to the same global dir.

## Blocked by

- Blocked by issue-46 (fix save-learning auto-archive) — the build pipeline for this issue will itself trigger the save-learning bug mid-flow unless issue-46 lands first, forcing manual file restoration during implementation.

## User stories addressed

- As a mantle user working across several repos at work, I want to gitignore or delete `.mantle/` entirely from my work repos so that mantle leaves no trace in repositories I do not own.
- As a mantle user running claude-code inside a git worktree, I want mantle context to resolve automatically from the shared global directory so that I do not have to configure each worktree.
- As a mantle maintainer, I want the global-mode contract (\"no in-repo artifact\") and the implementation to agree so that the user-facing promise is not a lie.