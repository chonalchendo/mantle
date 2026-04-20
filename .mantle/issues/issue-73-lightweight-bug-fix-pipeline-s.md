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
acceptance_criteria:
- id: ac-01
  text: Lightweight bug fix command runs without shape/plan-stories steps.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: On success, bug is auto-marked resolved with commit linked.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: On non-trivial mid-pipeline detection, command exits with a "promote to issue"
    hint.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Doc clearly distinguishes bug-fix path from issue path.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Tests cover the success and "promote" branches.
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

Bug fixes today go through the full issue pipeline (shape → plan-stories → implement → verify → review), which is overkill for small fixes. The existing `.mantle/bugs/` folder and `/mantle:bug` command capture bugs but don't have a corresponding lightweight fix path (inbox 2026-04-09).

## What to build

A fix pipeline scoped to bugs:
- `/mantle:fix-bug NN` (or rename existing `/mantle:fix`) reads the bug report and attempts a focused fix without shaping or story decomposition.
- Single agent pass: read bug → write fix + test → verify.
- Auto-marks the bug as resolved on success.
- Falls back to "promote to issue" when the fix proves non-trivial mid-pipeline.

## Acceptance criteria

- [ ] ac-01: Lightweight bug fix command runs without shape/plan-stories steps.
- [ ] ac-02: On success, bug is auto-marked resolved with commit linked.
- [ ] ac-03: On non-trivial mid-pipeline detection, command exits with a "promote to issue" hint.
- [ ] ac-04: Doc clearly distinguishes bug-fix path from issue path.
- [ ] ac-05: Tests cover the success and "promote" branches.
- [ ] ac-06: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user with a 1-line bug to fix, I want a path that takes seconds, not the full issue pipeline that takes minutes.