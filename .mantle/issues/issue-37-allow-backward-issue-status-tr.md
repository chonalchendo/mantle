---
title: Allow backward issue status transitions for review workflow
status: approved
slice:
- core
- tests
story_count: 1
verification: null
blocked_by: []
tags:
- type/issue
- status/approved
---

## Parent PRD

product-design.md, system-design.md

## Why

When /mantle:review flags issues and the user needs to move an issue back to implementing, \`mantle transition-issue-implementing --issue N\` fails with "Cannot transition to 'implementing' from 'implemented' status." The user has to manually edit the issue frontmatter. This breaks the review → fix → re-verify loop that the build pipeline needs.

## What to build

Allow backward transitions in the issue status machine, specifically \`implemented → implementing\`. This supports the review feedback workflow where issues need rework after review.

### Flow

1. User runs /mantle:review and flags issues
2. User (or pipeline) runs \`mantle transition-issue-implementing --issue N\`
3. Transition succeeds, issue is back in implementing status
4. User fixes issues, re-verifies, re-reviews

## Acceptance criteria

- [ ] \`implemented → implementing\` transition is allowed in the issue status machine
- [ ] CLI command \`mantle transition-issue-implementing\` succeeds when issue is in \`implemented\` status
- [ ] Other invalid transitions still fail (status machine isn't fully opened up)
- [ ] Covered by tests

## Blocked by

None

## User stories addressed

- As a developer whose code was flagged in review, I want to transition an issue back to implementing without editing frontmatter manually