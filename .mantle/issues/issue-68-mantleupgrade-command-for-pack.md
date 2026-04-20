---
title: /mantle:upgrade command for package and tooling refresh
status: planned
slice:
- claude-code
- cli
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria:
- id: ac-01
  text: '`/mantle:upgrade` reports current vs latest version.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: User confirms before any package install (no surprise upgrades).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: After upgrade, slash commands and agents in `~/.claude/` are refreshed.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Release notes for the version delta are shown.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Test covers the version-detection and refresh logic (mock PyPI + filesystem).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Today, upgrading the mantle package, refreshing slash commands, and discovering what changed are three separate manual steps. A single command would let users stay current without remembering to re-run `mantle install` after upgrading the package (inbox 2026-04-09).

## What to build

`/mantle:upgrade` Claude command that:
- Detects current installed version vs latest published version (PyPI).
- Runs the upgrade (`uv add` / `pip install -U`) in the active project's environment.
- Re-runs `mantle install` to refresh `~/.claude/` slash commands and agents.
- Surfaces release notes for the version delta (read from CHANGELOG.md or PyPI metadata).

## Acceptance criteria

- [ ] ac-01: `/mantle:upgrade` reports current vs latest version.
- [ ] ac-02: User confirms before any package install (no surprise upgrades).
- [ ] ac-03: After upgrade, slash commands and agents in `~/.claude/` are refreshed.
- [ ] ac-04: Release notes for the version delta are shown.
- [ ] ac-05: Test covers the version-detection and refresh logic (mock PyPI + filesystem).
- [ ] ac-06: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user who installed mantle weeks ago, I want one command that upgrades the package, refreshes the tooling, and tells me what's new — so I don't have to remember the three-step ritual.