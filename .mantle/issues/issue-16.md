---
title: Review (/mantle:review)
status: planned
slice:
- core
- claude-code
- tests
story_count: 2
verification: null
blocked_by: []
tags:
- type/issue
- status/planned
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

- [ ] `/mantle:review` is available in Claude Code
- [ ] Presents acceptance criteria as a checklist with pass/fail status from verification
- [ ] Human can mark each criterion as approved or needs-changes
- [ ] Human can add comments to individual review items
- [ ] Issue status transitions to "approved" when all criteria are marked approved
- [ ] Issue status transitions back if any criterion is marked needs-changes
- [ ] Tests verify checklist construction from acceptance criteria + verification results

## Blocked by

- Blocked by issue-15 (needs verification results to review against)

## User stories addressed

- User story 32: Checklist presentation with pass/fail from verification
- User story 33: Comments on individual review items
