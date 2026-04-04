---
title: Add-issue command — create single issues for existing projects
status: planned
slice:
- claude-code
- core
story_count: 1
verification: null
blocked_by:
- 27
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

`/mantle:plan-issues` is designed for batch decomposition of designs into issues during initial setup. After setup, there is no way to add a single new issue to the backlog. Users who complete a brainstorm session and get a "proceed" verdict have no command to create the issue — they'd have to manually write the markdown file or awkwardly re-run plan-issues.

This is the second half of the post-setup idea pipeline: brainstorm validates the idea, add-issue creates it.

## What to build

A `/mantle:add-issue` command that creates a single issue in an existing project's backlog. It assumes the idea has already been validated (via brainstorm or the user's own judgement).

### Flow

1. **Load context** — read existing issues (for numbering and deduplication), system-design.md
2. **Capture the issue** — conversational, gather:
   - Title and description (what to build and why)
   - Acceptance criteria
   - Architectural slices touched
   - Dependencies on existing issues
3. **Deduplication check** — flag if this overlaps with an existing issue
4. **System design impact** — flag if the issue introduces architecture not covered in system-design.md, suggest `/mantle:revise-system`
5. **Save** — write to `.mantle/issues/` using `mantle save-issue`
6. **Recommend next step** — typically `/mantle:shape-issue`

### Design principles

- Lightweight: 3-5 exchanges, not a lengthy session
- One issue at a time (use plan-issues for batch)
- Does not modify product-design.md (stubborn vision)
- Flags system design drift but doesn't block on it
- If a brainstorm file exists for this idea, reference it in the issue

## Acceptance criteria

- [ ] `/mantle:add-issue` command exists as a Claude Code slash command
- [ ] Reads existing issues to determine next number and check for duplicates
- [ ] Interactive session captures title, description, acceptance criteria, slices, and dependencies
- [ ] Flags overlap with existing issues
- [ ] Flags when system design may need updating
- [ ] Saves issue via `mantle save-issue` CLI
- [ ] References brainstorm file if one exists for this idea
- [ ] Recommends `/mantle:shape-issue` as next step

## Blocked by

Issue 27 (brainstorm command — the primary entry point that feeds into add-issue)

## User stories addressed

- As a developer mid-project, I want to add a single validated issue to my backlog without re-running the full plan-issues pipeline
- As a developer, I want new issues to flag when they introduce scope not covered by my system design, so I keep the design in sync