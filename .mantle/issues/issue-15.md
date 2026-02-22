---
title: Verification (/mantle:verify)
status: planned
slice: [core, claude-code, tests]
story_count: 0
verification: null
tags:
  - type/issue
  - status/planned
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

- [ ] `/mantle:verify` is available in Claude Code
- [ ] On first use (no strategy in config.md), prompts user to define verification strategy and persists it
- [ ] On subsequent uses, loads strategy from `.mantle/config.md`
- [ ] Per-issue verification overrides in issue frontmatter take precedence over project default
- [ ] Verification produces a report with pass/fail status per acceptance criterion
- [ ] Issue status transitions to "verified" on success
- [ ] Tests verify strategy loading, per-issue override precedence, and report generation

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and config.md)

## User stories addressed

- User story 29: Prompt for verification strategy on first use
- User story 30: Project-level default strategy stored in config.md
- User story 31: Per-issue verification overrides in acceptance criteria
