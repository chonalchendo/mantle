---
title: Dynamic end-of-command recommendations from full command catalogue
status: planned
slice:
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
  text: At least three `/mantle:*` commands swap their hard-coded next-step block
    for the dynamic recommendation.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Recommendations are derived from the full command catalogue, not a static
    subset.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: The dynamic block stays under ~5 lines of output to avoid bloat.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Token cost of the recommendation step is measured and documented.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Most `/mantle:*` commands end with hard-coded next-step hints (e.g. "next: /mantle:plan-stories"). These hints are curated, often stale, and miss commands the author didn't think to mention (inbox 2026-04-16).

## What to build

Replace the hard-coded next-step blocks with a dynamic recommendation step that:
- Queries the full set of `/mantle:*` commands (their descriptions are already available via the skill list / `mantle:help`).
- Reads current project state (issue/story status, last command run).
- Asks the LLM to recommend the next 1-3 commands with one-line rationale.

Implementation likely lives in a shared template or a `mantle recommend-next` CLI step that each command calls at the end.

## Acceptance criteria

- [ ] ac-01: At least three `/mantle:*` commands swap their hard-coded next-step block for the dynamic recommendation.
- [ ] ac-02: Recommendations are derived from the full command catalogue, not a static subset.
- [ ] ac-03: The dynamic block stays under ~5 lines of output to avoid bloat.
- [ ] ac-04: Token cost of the recommendation step is measured and documented.
- [ ] ac-05: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user finishing a command, I want next-step suggestions that reflect the full toolkit and my actual project state, not a curated subset that drifts as new commands ship.