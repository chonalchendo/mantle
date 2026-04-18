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

- [ ] `/mantle:upgrade` reports current vs latest version.
- [ ] User confirms before any package install (no surprise upgrades).
- [ ] After upgrade, slash commands and agents in `~/.claude/` are refreshed.
- [ ] Release notes for the version delta are shown.
- [ ] Test covers the version-detection and refresh logic (mock PyPI + filesystem).
- [ ] `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user who installed mantle weeks ago, I want one command that upgrades the package, refreshes the tooling, and tells me what's new — so I don't have to remember the three-step ritual.