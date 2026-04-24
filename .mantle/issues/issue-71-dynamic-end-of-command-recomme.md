---
title: Dynamic end-of-command recommendations with fresh-context handoff
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
  text: The dynamic block stays under ~5 lines of output (excluding optional fresh-context
    handoff block) to avoid bloat.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Token cost of the recommendation step is measured and documented.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Each suggested next step carries a `fresh_context` flag; when true, the recommendation
    emits a copy-paste-ready prompt block (issue/story IDs pre-filled, relevant context
    summarised).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: The pasted handoff prompt runs successfully in a new session without further
    editing for at least one tested transition (e.g. plan-stories → implement).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: The rule for when to suggest fresh context is documented (in the shared template
    or the command markdown).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Most `/mantle:*` commands end with hard-coded next-step hints (e.g. "next: /mantle:plan-stories"). These hints are curated, often stale, and miss commands the author didn't think to mention (inbox 2026-04-16).

Some next steps are also best run in a fresh context to avoid carrying stale assumptions (e.g. moving from `/mantle:plan-stories` to `/mantle:implement` benefits from a clean slate). Today's recommendations don't flag this or provide a copy-paste-ready prompt for the new session (inbox 2026-04-12). This issue absorbs the merged scope of issue 72 (closed) — the fresh-context flag is part of the same recommendation primitive, not a separate feature.

## What to build

Replace the hard-coded next-step blocks with a dynamic recommendation step that:
- Queries the full set of `/mantle:*` commands (their descriptions are already available via the skill list / `mantle:help`).
- Reads current project state (issue/story status, last command run).
- Asks the LLM to recommend the next 1-3 commands with one-line rationale.
- Tags each recommended command with `fresh_context: true | false` based on a documented rule (e.g. workflow-stage transitions where prior session context becomes a liability).
- When `fresh_context: true`, emits a copy-paste-ready prompt block optimised for the new session — issue/story IDs pre-filled, relevant context summarised, ready to paste into a fresh `claude` invocation.

Implementation likely lives in a shared template or a `mantle recommend-next` CLI step that each command calls at the end. The fresh-context handoff block is conditional output, not a separate command.

## Acceptance criteria

- [ ] ac-01: At least three `/mantle:*` commands swap their hard-coded next-step block for the dynamic recommendation.
- [ ] ac-02: Recommendations are derived from the full command catalogue, not a static subset.
- [ ] ac-03: The dynamic block stays under ~5 lines of output (excluding optional fresh-context handoff block) to avoid bloat.
- [ ] ac-04: Token cost of the recommendation step is measured and documented.
- [ ] ac-05: Each suggested next step carries a `fresh_context` flag; when true, the recommendation emits a copy-paste-ready prompt block (issue/story IDs pre-filled, relevant context summarised).
- [ ] ac-06: The pasted handoff prompt runs successfully in a new session without further editing for at least one tested transition (e.g. plan-stories → implement).
- [ ] ac-07: The rule for when to suggest fresh context is documented (in the shared template or the command markdown).
- [ ] ac-08: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user finishing a command, I want next-step suggestions that reflect the full toolkit and my actual project state, not a curated subset that drifts as new commands ship.
- As a Mantle user moving between workflow stages, I want a ready-to-paste prompt for the new session so I don't have to reconstruct context by hand.

## Notes

- Absorbs issue 72 (closed; merged here on 2026-04-24 per brainstorm `2026-04-22-gsd-scout-backlog-reshape.md`, decision 2).
- Source inbox items: `2026-04-16-end-of-command-dynamic-recommendations`, `2026-04-12-fresh-context-handoff-block`.
