---
title: Fix archive_issue shaped-doc glob to match slug-less filenames
status: approved
slice:
- core
- tests
story_count: 1
verification: null
blocked_by: []
skills_required:
- python-314
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: '`archive_issue` matches `issue-NN-shaped.md` (no slug) in addition to `issue-NN-<slug>-shaped.md`.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Unit test covers both filename forms; regression test for the slug-less form
    passes.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

`core/archive.py:46` globs `issue-{NN:02d}-*-shaped.md`, which requires at least one character between the issue number and `-shaped.md`. Files like `issue-24-shaped.md` (no slug) are silently missed during archive. Surfaced during batch archive of issues 01-40 (inbox 2026-04-09).

## What to build

Update the shaped-doc glob in `core/archive.py:46` so it also matches the slug-less form `issue-NN-shaped.md`. Either widen the pattern to `issue-{NN:02d}*-shaped.md` or add a second glob for the no-slug case.

## Acceptance criteria

- [ ] ac-01: `archive_issue` matches `issue-NN-shaped.md` (no slug) in addition to `issue-NN-<slug>-shaped.md`.
- [ ] ac-02: Unit test covers both filename forms; regression test for the slug-less form passes.
- [ ] ac-03: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user archiving older issues whose shaped docs lack a slug, I want them archived alongside the issue file so the project state is consistent.