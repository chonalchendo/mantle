---
title: Project initialization (mantle init + personal vault setup)
status: planned
slice: [cli, core, vault, tests]
story_count: 0
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
- `src/mantle/cli/init.py` — `mantle init` creates `.mantle/` directory with state.md, config.md, tags.md, .gitignore; prints interactive onboarding message; prompts about personal vault
- `src/mantle/core/vault.py` — read/write notes with YAML frontmatter (OmegaConf parsing, Pydantic validation), Obsidian CLI integration with filesystem fallback, path resolution between `.mantle/` and personal vault
- `src/mantle/core/state.py` — load, create, update, and transition project state; state machine validation; git identity resolution via `git config user.email`
- `mantle init-vault ~/vault` — creates personal vault structure (skills/, knowledge/, inbox/)
- `mantle config set personal-vault ~/vault` — stores personal vault path in config
- Vault templates for state.md, config.md, tags.md
- Git identity tagging on all created notes (cross-cutting concern, built in from the start)

## Acceptance criteria

- [ ] `mantle init` in a git repo creates `.mantle/` with state.md, config.md, tags.md, and .gitignore
- [ ] state.md is created with valid YAML frontmatter including project name (derived from directory), status "idea", git identity, timestamps
- [ ] .gitignore excludes compiled/temp files
- [ ] Interactive onboarding message prints with next steps ("Run /mantle:idea to get started")
- [ ] User is prompted about personal vault setup (non-blocking)
- [ ] `mantle init-vault ~/vault` creates skills/, knowledge/, inbox/ directories
- [ ] `mantle config set personal-vault ~/vault` persists the path in `.mantle/config.md`
- [ ] `core/vault.py` reads and writes markdown files with YAML frontmatter using OmegaConf + Pydantic
- [ ] `core/vault.py` falls back to filesystem when Obsidian CLI is unavailable, logging a warning
- [ ] `core/state.py` validates state transitions (e.g., idea → challenge is valid, idea → implementing is not)
- [ ] All created notes are stamped with `git config user.email`
- [ ] Running `mantle init` in an already-initialized project warns and does not overwrite
- [ ] Tests cover vault read/write, state transitions, filesystem fallback, and init idempotency

## Blocked by

- Blocked by issue-01 (needs CLI entry point and package structure)

## User stories addressed

- User story 3: `mantle init` creates `.mantle/` with interactive onboarding
- User story 4: `mantle init` prompts about personal vault
- User story 5: Clone repo and immediately access `.mantle/` context
- User story 43: Personal vault syncs via iCloud (vault lives in user-chosen directory)
