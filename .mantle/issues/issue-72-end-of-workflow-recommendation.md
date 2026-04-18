---
title: End-of-workflow recommendations include fresh-context handoff prompt
status: planned
slice:
- claude-code
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

Some next steps are best run in a fresh context to avoid carrying stale assumptions (e.g. moving from `/mantle:plan-stories` to `/mantle:implement` benefits from a clean slate). Today's recommendations don't flag this or provide a copy-paste-ready prompt for the new session (inbox 2026-04-12).

## What to build

Extend end-of-workflow recommendations so each suggested next step includes:
- A flag for whether a fresh context is recommended.
- When true, a copy-paste-ready prompt block optimized for the new session (issue/story IDs pre-filled, relevant context summarized).

Likely overlaps with the dynamic-recommendations issue; these may need to ship together or in sequence.

## Acceptance criteria

- [ ] At least two `/mantle:*` commands emit a fresh-context handoff block when recommended.
- [ ] The pasted prompt runs successfully in a new session without further editing.
- [ ] The recommendation rule (when to suggest fresh context) is documented.
- [ ] `just check` passes.

## Blocked by

May share scope with the dynamic end-of-command recommendations issue.

## User stories addressed

- As a Mantle user moving between workflow stages, I want a ready-to-paste prompt for the new session so I don't have to reconstruct context by hand.