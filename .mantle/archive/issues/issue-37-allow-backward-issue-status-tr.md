---
title: Allow backward issue status transitions for review workflow
status: approved
slice:
- core
- tests
story_count: 1
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: \`implemented → implementing\` transition is allowed in the issue status machine
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: CLI command \`mantle transition-issue-implementing\` succeeds when issue is
    in \`implemented\` status
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Other invalid transitions still fail (status machine isn't fully opened up)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Covered by tests
  passes: false
  waived: false
  waiver_reason: null
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

- [ ] ac-01: \`implemented → implementing\` transition is allowed in the issue status machine
- [ ] ac-02: CLI command \`mantle transition-issue-implementing\` succeeds when issue is in \`implemented\` status
- [ ] ac-03: Other invalid transitions still fail (status machine isn't fully opened up)
- [ ] ac-04: Covered by tests

## Blocked by

None

## User stories addressed

- As a developer whose code was flagged in review, I want to transition an issue back to implementing without editing frontmatter manually