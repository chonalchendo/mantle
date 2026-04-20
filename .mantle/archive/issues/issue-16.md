---
title: Review (/mantle:review)
status: completed
slice:
- core
- claude-code
- tests
story_count: 2
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/completed
acceptance_criteria:
- id: ac-01
  text: '`/mantle:review` is available in Claude Code'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Presents acceptance criteria as a checklist with pass/fail status from verification
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Human can mark each criterion as approved or needs-changes
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Human can add comments to individual review items
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Issue status transitions to "approved" when all criteria are marked approved
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Issue status transitions back if any criterion is marked needs-changes
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: Tests verify checklist construction from acceptance criteria + verification
    results
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:review` command that presents a checklist of acceptance criteria with pass/fail status from verification. The human marks each criterion as approved or needs-changes with optional comments. This is the final quality gate before work is considered done.

This includes:
- `src/mantle/core/review.py` — build checklist from issue acceptance criteria + verification results, collect human feedback (approved/needs-changes + comments per criterion), update issue status
- `claude/commands/mantle/review.md` — static command that loads verification results and presents the review checklist
- Issue status transitions: verified → approved (all criteria pass) or back to implementing (needs changes)

## Acceptance criteria

- [ ] ac-01: `/mantle:review` is available in Claude Code
- [ ] ac-02: Presents acceptance criteria as a checklist with pass/fail status from verification
- [ ] ac-03: Human can mark each criterion as approved or needs-changes
- [ ] ac-04: Human can add comments to individual review items
- [ ] ac-05: Issue status transitions to "approved" when all criteria are marked approved
- [ ] ac-06: Issue status transitions back if any criterion is marked needs-changes
- [ ] ac-07: Tests verify checklist construction from acceptance criteria + verification results

## Blocked by

- Blocked by issue-15 (needs verification results to review against)

## User stories addressed

- User story 32: Checklist presentation with pass/fail from verification
- User story 33: Comments on individual review items
