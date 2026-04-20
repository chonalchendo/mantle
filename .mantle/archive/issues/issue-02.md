---
title: Project initialization (mantle init + personal vault setup)
status: completed
slice:
- cli
- core
- vault
- tests
story_count: 4
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/completed
acceptance_criteria:
- id: ac-01
  text: '`mantle init` in a git repo creates `.mantle/` with state.md, config.md,
    tags.md, and .gitignore'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-02
  text: state.md is created with valid YAML frontmatter including project name (derived
    from directory), status "idea", git identity, timestamps
  passes: true
  waived: false
  waiver_reason: null
- id: ac-03
  text: .gitignore excludes compiled/temp files
  passes: true
  waived: false
  waiver_reason: null
- id: ac-04
  text: Interactive onboarding message prints with next steps ("Run /mantle:idea to
    get started")
  passes: true
  waived: false
  waiver_reason: null
- id: ac-05
  text: Onboarding message mentions personal vault setup (non-blocking)
  passes: true
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`mantle init-vault ~/vault` creates skills/, knowledge/, inbox/ directories'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-07
  text: '`mantle init-vault ~/vault` automatically sets personal_vault in `.mantle/config.md`
    frontmatter'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-08
  text: '`core/vault.py` reads and writes markdown files with YAML frontmatter using
    yaml.safe_load + Pydantic'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-09
  text: '`core/vault.py` is filesystem only (Obsidian CLI integration deferred)'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-10
  text: '`core/state.py` validates state transitions (e.g., idea → challenge is valid,
    idea → implementing is not)'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-11
  text: All created notes are stamped with `git config user.email`
  passes: true
  waived: false
  waiver_reason: null
- id: ac-12
  text: Running `mantle init` in an already-initialized project warns and does not
    overwrite
  passes: true
  waived: false
  waiver_reason: null
- id: ac-13
  text: Tests cover vault read/write, state transitions, init idempotency, and vault
    init with auto-config
  passes: true
  waived: false
  waiver_reason: null
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

- [x] ac-01: `mantle init` in a git repo creates `.mantle/` with state.md, config.md, tags.md, and .gitignore
- [x] ac-02: state.md is created with valid YAML frontmatter including project name (derived from directory), status "idea", git identity, timestamps
- [x] ac-03: .gitignore excludes compiled/temp files
- [x] ac-04: Interactive onboarding message prints with next steps ("Run /mantle:idea to get started")
- [x] ac-05: Onboarding message mentions personal vault setup (non-blocking)
- [x] ac-06: `mantle init-vault ~/vault` creates skills/, knowledge/, inbox/ directories
- [x] ac-07: `mantle init-vault ~/vault` automatically sets personal_vault in `.mantle/config.md` frontmatter
- [x] ac-08: `core/vault.py` reads and writes markdown files with YAML frontmatter using yaml.safe_load + Pydantic
- [x] ac-09: `core/vault.py` is filesystem only (Obsidian CLI integration deferred)
- [x] ac-10: `core/state.py` validates state transitions (e.g., idea → challenge is valid, idea → implementing is not)
- [x] ac-11: All created notes are stamped with `git config user.email`
- [x] ac-12: Running `mantle init` in an already-initialized project warns and does not overwrite
- [x] ac-13: Tests cover vault read/write, state transitions, init idempotency, and vault init with auto-config

## Blocked by

- Blocked by issue-01 (needs CLI entry point and package structure)

## User stories addressed

- User story 3: `mantle init` creates `.mantle/` with interactive onboarding
- User story 4: `mantle init` prompts about personal vault
- User story 5: Clone repo and immediately access `.mantle/` context
- User story 43: Personal vault syncs via iCloud (vault lives in user-chosen directory)
