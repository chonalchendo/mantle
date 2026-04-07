---
title: Review feedback loop — automated fix and re-verify after review
status: planned
slice:
- claude-code
- core
- tests
story_count: 0
verification: null
blocked_by: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

After /mantle:review flags changes, there's no automated path back through the build pipeline. The user has to manually fix issues, re-verify, and re-review. The build pipeline assumes a single pass — shape, plan, implement, simplify, verify, done. But review is iterative: review finds problems, fixes are made, re-verification is needed.

## What to build

A way to resume the build pipeline after review flags issues. Two possible approaches (to be shaped):

1. **\`/mantle:fix\` command** — takes review feedback, spawns an implementation agent to fix flagged issues, then re-runs verification automatically.
2. **\`/mantle:build --resume\` flag** — allows the build pipeline to pick up from where review flagged issues, apply fixes, and re-verify.

### Flow

1. User runs /mantle:review, which flags issues
2. User runs /mantle:fix (or /mantle:build --resume)
3. Command reads review feedback from the review output
4. Spawns implementation agent(s) to fix flagged issues
5. Re-runs verification to confirm fixes
6. Reports results

## Acceptance criteria

- [ ] Review feedback can be consumed programmatically (structured output from review step)
- [ ] Fix command spawns implementation agents with review feedback as context
- [ ] Verification re-runs automatically after fixes are applied
- [ ] Issue status transitions correctly through the fix cycle (implementing → implemented)
- [ ] Covered by tests where applicable (CLI/core logic, not prompt behaviour)

## Blocked by

- Blocked by issue-37 (needs backward transitions for implemented → implementing)

## User stories addressed

- As a developer who received review feedback, I want an automated path to fix issues and re-verify without manually orchestrating each step