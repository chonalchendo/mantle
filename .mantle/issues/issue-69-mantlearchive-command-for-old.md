---
title: /mantle:archive command for old .mantle/ files
status: planned
slice:
- cli
- core
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

`.mantle/` accumulates stale files over time (old learnings, sessions, brainstorms, scouts). There's no first-class way to archive cold artifacts in bulk for both local and global storage modes (inbox 2026-04-13).

## What to build

`mantle archive` CLI + optional `/mantle:archive` Claude command that:
- Identifies cold artifacts by age + status (e.g. learnings older than N days, sessions older than M days).
- Moves them to `.mantle/archive/` preserving subfolder structure.
- Supports both local and global storage modes.
- Dry-run mode by default; `--apply` to commit.

Shape: define which folders + thresholds qualify (likely sessions > 90 days, brainstorms > 180 days, etc.).

## Acceptance criteria

- [ ] `mantle archive --dry-run` lists candidate files without moving them.
- [ ] `mantle archive --apply` moves to `.mantle/archive/<subfolder>/`.
- [ ] Works in both local and global storage modes.
- [ ] Configurable thresholds in `.mantle/config.md`.
- [ ] Tests cover dry-run, apply, and both storage modes.
- [ ] `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user with months of accumulated `.mantle/` artifacts, I want a single command to archive cold material so my active workspace stays manageable and `compile` stays cheap.