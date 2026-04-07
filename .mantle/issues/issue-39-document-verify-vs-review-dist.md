---
title: Document verify vs review distinction and add convention checking to verify
status: verified
slice:
- claude-code
- tests
story_count: 1
verification: null
blocked_by: []
tags:
- type/issue
- status/verified
---

## Parent PRD

product-design.md, system-design.md

## Why

The build pipeline treats verification (Step 8) as the quality gate, but it only checks "does the code satisfy the acceptance criteria." It doesn't check architectural consistency, convention adherence, or whether the implementation follows project patterns. During issue 35, human review caught 3 issues (hardcoded data, CLI ergonomics, connector pattern) that verification passed cleanly.

The distinction between /mantle:verify (functional correctness) and /mantle:review (architectural quality) is not documented, leading to false confidence after verification passes.

## What to build

### 1. Documentation

Document the distinction clearly in the verify and review command prompts:
- /mantle:verify checks functional correctness against acceptance criteria
- /mantle:review checks architectural quality, conventions, and design consistency

### 2. Convention check in verify (optional enhancement)

Add a "convention check" sub-step to the verify command that reads CLAUDE.md and system-design.md and flags deviations in the implemented code. This bridges the gap between pure AC checking and full architectural review.

### Flow

1. /mantle:verify runs acceptance criteria checks (existing)
2. /mantle:verify runs convention check: reads CLAUDE.md + system-design.md, scans changed files for deviations
3. Convention violations are reported as warnings (not failures) in the verification report
4. /mantle:review remains the authoritative architectural quality gate

## Acceptance criteria

- [ ] verify.md prompt documents that it checks functional correctness, not architectural quality
- [ ] review.md prompt documents that it checks architectural quality and conventions
- [ ] Verify step includes a convention check that reads CLAUDE.md and flags deviations in changed files
- [ ] Convention check results appear as warnings in the verification report (not pass/fail blockers)

## Blocked by

None

## User stories addressed

- As a developer reading verification results, I want to understand what verify checks and what it doesn't so I don't skip the review step
- As the build pipeline, I want convention deviations surfaced early so fewer issues reach human review