---
title: Fix issue numbering to include archive — prevent reused numbers
status: planned
slice:
- core
- cli
- tests
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

`mantle save-issue` auto-assigns the next issue number via `core.issues.next_issue_number()`, which calls `list_issues()` at `core/issues.py:166`. `list_issues()` only globs `.mantle/issues/` — it never scans `.mantle/archive/issues/`.

The result: when an issue is archived (moved from `.mantle/issues/` to `.mantle/archive/issues/`), its number becomes available for reuse. Today, saving a new issue in this repo produced `issue-43` even though `.mantle/archive/issues/issue-43-global-mantle-storage-per-proj.md` already exists — it had to be manually renamed to `issue-44`.

This silently pollutes history every time you archive an issue and add a new one. Git log, session logs, learning notes, and session recaps will all reference two different "issue-N"s, and retrospectives that load by issue number may load the wrong file.

## What to build

Update `next_issue_number()` (or the underlying `list_issues()` helper) to scan both the active issues directory **and** the archive directory when computing the next number. The returned max should be the global max across all known issue numbers — active + archived.

### Flow

1. User completes issue 43 and archives it (it moves to `.mantle/archive/issues/issue-43-*.md`)
2. User runs `mantle save-issue` (or `/mantle:add-issue`) to file a new issue
3. `next_issue_number()` scans `.mantle/issues/` (finds max 42) **and** `.mantle/archive/issues/` (finds 43)
4. Returns 44 — the first globally-unique number
5. New issue is saved as `issue-44-*.md`

## Acceptance criteria

- [ ] `next_issue_number()` in `src/mantle/core/issues.py` scans both `.mantle/issues/` and `.mantle/archive/issues/` when computing the max number
- [ ] `mantle save-issue` in this repo returns 45 (the next number after the current active max of 44), not 43 or 44
- [ ] Unit test: given a repo with active issues [40, 41] and archived issue [43], `next_issue_number` returns 44
- [ ] Unit test: given a repo with only archived issues [1, 2, 3], `next_issue_number` returns 4
- [ ] Unit test: existing behaviour (no archive directory present) still returns `max(active) + 1`
- [ ] No regression in `tests/core/test_issues.py`

## Blocked by

None

## User stories addressed

- As a Mantle user who archives completed issues, I want new issue numbers to be globally unique across active and archived so that my history and git log stay unambiguous.
- As a developer reading session logs and retrospectives, I want "issue-N" to always refer to the same piece of work so that cross-referencing past learnings doesn't require context-guessing.