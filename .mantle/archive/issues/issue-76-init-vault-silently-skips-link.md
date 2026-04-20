---
title: init-vault silently skips linking when vault directory already exists
status: approved
slice:
- core
- cli
- tests
story_count: 2
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Python 3.14
- Python package structure
- cyclopts
- omegaconf
- pydantic-project-conventions
- python-314
- streamlit-aggrid
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: 'Running `mantle init-vault PATH` when `PATH` already contains all four subdirs
    records `personal_vault: PATH` in the current project''s `.mantle/config.md` without
    raising.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: CLI prints a message indicating the existing vault was linked (e.g., *Linked
    existing vault at PATH*), not *Nothing to do*.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Creating a brand-new vault (fresh path) still creates the four subdirs and
    links the project — no regression.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: 'Regression test covers the multi-project share flow: Project A creates +
    links, Project B re-links to the same path, and Project B''s `config.md` ends
    up populated.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

`mantle init-vault PATH` is supposed to do two things: (1) create the vault directory structure and (2) record `personal_vault: PATH` in the current project's `.mantle/config.md`.

When the target path already contains all four vault subdirectories (`skills/`, `knowledge/`, `inbox/`, `projects/`), `project.init_vault()` raises `FileExistsError` before calling `update_config`. The CLI catches it, prints *Personal vault already exists. Nothing to do.*, and returns.

Result: the current project is **not** linked to the existing vault. Users who want multiple projects to share one personal vault have to hand-edit `.mantle/config.md`.

### Repro

```bash
# Project A — creates the vault and links to it (works fine)
cd ~/project-a && mantle init && mantle init-vault ~/shared-vault

# Project B — wants to share the same vault
cd ~/project-b && mantle init && mantle init-vault ~/shared-vault
# => 'Personal vault already exists. Nothing to do.'
# => cat ~/project-b/.mantle/config.md  -> no personal_vault entry
```

## What to build

Make linking idempotent. If the vault directories already exist, skip the mkdirs but still call `update_config` so the current project points at the vault. Emit a confirmation message that reflects what actually happened (e.g., *Linked existing vault at PATH*), not *Nothing to do*.

### Flow

1. User runs `mantle init-vault PATH` in Project B.
2. `init_vault` sees that all four subdirs exist at `PATH`.
3. It skips the `mkdir` calls but still runs `update_config(project_root, personal_vault=...)`.
4. CLI prints *Linked existing vault at PATH* (distinct from the fresh-vault creation message).
5. `.mantle/config.md` in Project B now contains `personal_vault: PATH`.

### Proposed fix

In `src/mantle/core/project.py::init_vault` (line ~336), don't raise when all four subdirs exist — just skip the `mkdir` loop and continue to `update_config`. Alternatively, the CLI wrapper can swallow `FileExistsError` and still call `update_config` itself. Core-level fix is cleaner because it keeps `init_vault` semantically idempotent.

### Affected files

- `src/mantle/core/project.py:314-343` — the `init_vault` function and its `FileExistsError` raise at line ~336
- `src/mantle/cli/init_vault.py:15-49` — the `FileExistsError` handler and success messaging
- `tests/core/test_project.py` (and/or `tests/cli/test_init_vault.py`) — regression coverage

## Acceptance criteria

- [ ] ac-01: Running `mantle init-vault PATH` when `PATH` already contains all four subdirs records `personal_vault: PATH` in the current project's `.mantle/config.md` without raising.
- [ ] ac-02: CLI prints a message indicating the existing vault was linked (e.g., *Linked existing vault at PATH*), not *Nothing to do*.
- [ ] ac-03: Creating a brand-new vault (fresh path) still creates the four subdirs and links the project — no regression.
- [ ] ac-04: Regression test covers the multi-project share flow: Project A creates + links, Project B re-links to the same path, and Project B's `config.md` ends up populated.

## Blocked by

None

## User stories addressed

- As a developer with multiple projects on one machine, I want `mantle init-vault` to link the current project to an existing personal vault so that I can share skills and knowledge across projects without hand-editing `config.md`.
