---
title: Verification (/mantle:verify)
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
  text: '`/mantle:verify` is available in Claude Code'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: On first use (no strategy in config.md), prompts user to define verification
    strategy and persists it
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: On subsequent uses, loads strategy from `.mantle/config.md`
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Per-issue verification overrides in issue frontmatter take precedence over
    project default
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Verification produces a report with pass/fail status per acceptance criterion
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Issue status transitions to "verified" on success
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: Tests verify strategy loading, per-issue override precedence, and report generation
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:verify` command that runs project-specific verification. On first invocation, it prompts the user to define their verification strategy (e.g., "run against example project", "test on localhost", "run integration tests"). The strategy is stored in `.mantle/config.md` as the project default, with per-issue overrides available in issue acceptance criteria.

This includes:
- `src/mantle/core/verify.py` — load verification strategy from config.md, check for per-issue overrides in issue frontmatter, execute verification steps, build verification report with pass/fail per criterion
- `claude/commands/mantle/verify.md` — static command that triggers verification: reads strategy, runs checks, reports results
- First-use flow: detect missing verification strategy in config.md, prompt user to define one, persist to config.md
- Per-issue override: if issue frontmatter has `verification:` field, use that instead of project default

## Acceptance criteria

- [ ] ac-01: `/mantle:verify` is available in Claude Code
- [ ] ac-02: On first use (no strategy in config.md), prompts user to define verification strategy and persists it
- [ ] ac-03: On subsequent uses, loads strategy from `.mantle/config.md`
- [ ] ac-04: Per-issue verification overrides in issue frontmatter take precedence over project default
- [ ] ac-05: Verification produces a report with pass/fail status per acceptance criterion
- [ ] ac-06: Issue status transitions to "verified" on success
- [ ] ac-07: Tests verify strategy loading, per-issue override precedence, and report generation

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and config.md)

## User stories addressed

- User story 29: Prompt for verification strategy on first use
- User story 30: Project-level default strategy stored in config.md
- User story 31: Per-issue verification overrides in acceptance criteria
