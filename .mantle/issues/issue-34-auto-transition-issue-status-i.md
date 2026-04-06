---
title: Auto-transition issue status in build pipeline
status: verified
slice:
- claude-code
story_count: 2
verification: null
blocked_by: []
tags:
- type/issue
- status/verified
---

## Parent PRD

product-design.md, system-design.md

## Why

Issue status transitions are manually managed, leading to stale statuses (e.g. issues 24 and 30 were built and released but stuck at 'planned' and 'approved'). This friction was flagged in retrospectives for issues 27 and 28 as a recurring problem.

The build pipeline (build.md) and individual commands (implement.md, verify.md) should auto-transition issue status as phases complete, eliminating manual ceremony.

## What to build

Update prompts to auto-transition issue status at the right points:

- build.md Step 6 (implement): transition issue to 'implementing' when implementation starts
- build.md Step 8 (verify): transition issue to 'verified' on pass (already done by verify.md)
- build.md Step 9 or review: transition to 'approved'/'completed' on review pass

May need new CLI commands or relaxed state machine transitions to support skipping intermediate states when the build pipeline handles the full lifecycle.

## Acceptance criteria

- [ ] Build pipeline auto-transitions issue to 'implementing' at Step 6
- [ ] Issue status reflects actual state after a full build pipeline run
- [ ] No manual transition commands needed during normal build pipeline flow

## Blocked by

None

## User stories addressed

- As a developer, I want issue statuses to stay accurate without manual CLI calls so that project state reflects reality