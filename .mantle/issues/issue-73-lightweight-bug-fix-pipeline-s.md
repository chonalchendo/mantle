---
title: Lightweight bug fix pipeline separate from issue flow
status: planned
slice:
- cli
- claude-code
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

Bug fixes today go through the full issue pipeline (shape → plan-stories → implement → verify → review), which is overkill for small fixes. The existing `.mantle/bugs/` folder and `/mantle:bug` command capture bugs but don't have a corresponding lightweight fix path (inbox 2026-04-09).

## What to build

A fix pipeline scoped to bugs:
- `/mantle:fix-bug NN` (or rename existing `/mantle:fix`) reads the bug report and attempts a focused fix without shaping or story decomposition.
- Single agent pass: read bug → write fix + test → verify.
- Auto-marks the bug as resolved on success.
- Falls back to "promote to issue" when the fix proves non-trivial mid-pipeline.

## Acceptance criteria

- [ ] Lightweight bug fix command runs without shape/plan-stories steps.
- [ ] On success, bug is auto-marked resolved with commit linked.
- [ ] On non-trivial mid-pipeline detection, command exits with a "promote to issue" hint.
- [ ] Doc clearly distinguishes bug-fix path from issue path.
- [ ] Tests cover the success and "promote" branches.
- [ ] `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user with a 1-line bug to fix, I want a path that takes seconds, not the full issue pipeline that takes minutes.