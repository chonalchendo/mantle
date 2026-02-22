---
title: Project initialization (mantle init + personal vault setup)
status: planned
slice: [cli, core, vault, tests]
story_count: 4
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `mantle init` command that creates `.mantle/` in a project repo with all required structure, and `mantle init-vault` for optional personal vault setup. This slice builds the foundational vault read/write (`core/vault.py`) and state management (`core/state.py`) that every subsequent command depends on.

This includes:
- `src/mantle/core/vault.py` — read/write notes with YAML frontmatter (yaml.safe_load + Pydantic validation), filesystem only (Obsidian CLI deferred)
- `src/mantle/core/state.py` — load, create, update, and transition project state; state machine validation; git identity resolution via `git config user.email`
- `src/mantle/core/project.py` — project initialization constants, `init_project()`, vault init, config read/write internals
- `src/mantle/cli/init.py` — `mantle init` creates `.mantle/` directory with state.md, config.md, tags.md, .gitignore; prints interactive onboarding message
- `src/mantle/cli/init_vault.py` — `mantle init-vault ~/vault` creates personal vault structure and auto-sets config
- Git identity tagging on all created notes (cross-cutting concern, built in from the start)

## Acceptance criteria

- [ ] `mantle init` in a git repo creates `.mantle/` with state.md, config.md, tags.md, and .gitignore
- [ ] state.md is created with valid YAML frontmatter including project name (derived from directory), status "idea", git identity, timestamps
- [ ] .gitignore excludes compiled/temp files
- [ ] Interactive onboarding message prints with next steps ("Run /mantle:idea to get started")
- [ ] Onboarding message mentions personal vault setup (non-blocking)
- [ ] `mantle init-vault ~/vault` creates skills/, knowledge/, inbox/ directories
- [ ] `mantle init-vault ~/vault` automatically sets personal_vault in `.mantle/config.md` frontmatter
- [ ] `core/vault.py` reads and writes markdown files with YAML frontmatter using yaml.safe_load + Pydantic
- [ ] `core/vault.py` is filesystem only (Obsidian CLI integration deferred)
- [ ] `core/state.py` validates state transitions (e.g., idea → challenge is valid, idea → implementing is not)
- [ ] All created notes are stamped with `git config user.email`
- [ ] Running `mantle init` in an already-initialized project warns and does not overwrite
- [ ] Tests cover vault read/write, state transitions, init idempotency, and vault init with auto-config

## Blocked by

- Blocked by issue-01 (needs CLI entry point and package structure)

## User stories addressed

- User story 3: `mantle init` creates `.mantle/` with interactive onboarding
- User story 4: `mantle init` prompts about personal vault
- User story 5: Clone repo and immediately access `.mantle/` context
- User story 43: Personal vault syncs via iCloud (vault lives in user-chosen directory)
