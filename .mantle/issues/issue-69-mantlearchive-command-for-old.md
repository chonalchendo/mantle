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
acceptance_criteria:
- id: ac-01
  text: '`mantle archive --dry-run` lists candidate files without moving them.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: '`mantle archive --apply` moves to `.mantle/archive/<subfolder>/`.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Works in both local and global storage modes.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Configurable thresholds in `.mantle/config.md`.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Tests cover dry-run, apply, and both storage modes.
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

`.mantle/` accumulates stale files over time (old learnings, sessions, brainstorms, scouts). There's no first-class way to archive cold artifacts in bulk for both local and global storage modes (inbox 2026-04-13).

## What to build

`mantle archive` CLI + optional `/mantle:archive` Claude command that:
- Identifies cold artifacts by age + status (e.g. learnings older than N days, sessions older than M days).
- Moves them to `.mantle/archive/` preserving subfolder structure.
- Supports both local and global storage modes.
- Dry-run mode by default; `--apply` to commit.

Shape: define which folders + thresholds qualify (likely sessions > 90 days, brainstorms > 180 days, etc.).

## Acceptance criteria

- [ ] ac-01: `mantle archive --dry-run` lists candidate files without moving them.
- [ ] ac-02: `mantle archive --apply` moves to `.mantle/archive/<subfolder>/`.
- [ ] ac-03: Works in both local and global storage modes.
- [ ] ac-04: Configurable thresholds in `.mantle/config.md`.
- [ ] ac-05: Tests cover dry-run, apply, and both storage modes.
- [ ] ac-06: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user with months of accumulated `.mantle/` artifacts, I want a single command to archive cold material so my active workspace stays manageable and `compile` stays cheap.