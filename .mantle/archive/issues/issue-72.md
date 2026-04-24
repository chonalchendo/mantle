---
title: End-of-workflow recommendations include fresh-context handoff prompt
status: dropped
slice:
- claude-code
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/dropped
acceptance_criteria:
- id: ac-01
  text: At least two `/mantle:*` commands emit a fresh-context handoff block when
    recommended.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: The pasted prompt runs successfully in a new session without further editing.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: The recommendation rule (when to suggest fresh context) is documented.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Status: Merged into issue 71

Closed on 2026-04-24 per brainstorm `2026-04-22-gsd-scout-backlog-reshape.md` (decision 2). Issue 72's body explicitly noted "may share scope with the dynamic end-of-command recommendations issue" — confirmed at brainstorm time. The fresh-context flag is a property of each recommended next step, not a separate feature, so it lives naturally as ACs 05-07 of issue 71. Original ACs preserved below for reference.

## Why

Some next steps are best run in a fresh context to avoid carrying stale assumptions (e.g. moving from `/mantle:plan-stories` to `/mantle:implement` benefits from a clean slate). Today's recommendations don't flag this or provide a copy-paste-ready prompt for the new session (inbox 2026-04-12).

## What to build

Extend end-of-workflow recommendations so each suggested next step includes:
- A flag for whether a fresh context is recommended.
- When true, a copy-paste-ready prompt block optimized for the new session (issue/story IDs pre-filled, relevant context summarized).

Likely overlaps with the dynamic-recommendations issue; these may need to ship together or in sequence.

## Acceptance criteria

- [ ] ac-01: At least two `/mantle:*` commands emit a fresh-context handoff block when recommended.
- [ ] ac-02: The pasted prompt runs successfully in a new session without further editing.
- [ ] ac-03: The recommendation rule (when to suggest fresh context) is documented.
- [ ] ac-04: `just check` passes.

## Blocked by

May share scope with the dynamic end-of-command recommendations issue.

## User stories addressed

- As a Mantle user moving between workflow stages, I want a ready-to-paste prompt for the new session so I don't have to reconstruct context by hand.