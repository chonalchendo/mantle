---
title: Inbox — ultra-low-friction idea capture for project feature ideas
status: planned
slice:
- core
- cli
- claude-code
- tests
story_count: 0
verification: null
blocked_by: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

There is no lightweight way to park feature ideas for later. `/mantle:idea` is the project origin story (singular, heavyweight). `/mantle:add-issue` requires acceptance criteria and structure. Users need a parking lot between "thought I had" and "planned issue" — optimised for capture speed, not structure.

Ideas come from two sources: the user (fleeting thoughts during any session) and the AI (patterns spotted during implementation or review). Both need a low-friction path to capture without interrupting the current workflow.

## What to build

### 1. Core inbox module

New `core/inbox.py` with an InboxNote pydantic model (title, description, source, status, date, author). CRUD functions: save, load, list, update status. Follows the pattern of `core/challenge.py` and `core/learning.py`.

Add `inbox` to SUBDIRS in `core/project.py` so `mantle init` creates `.mantle/inbox/`.

### 2. CLI save-inbox-item command

Thin CLI wrapper in `cli/inbox.py`. Command: `mantle save-inbox-item --title "..." [--description "..."] [--source user|ai]`.

### 3. /mantle:inbox prompt

Interactive prompt for user-initiated capture. Asks for title and optional one-liner description. Saves via CLI. Ultra-lightweight — no multi-field structured interview.

### 4. AI suggest-then-save in interactive sessions

During any interactive session, the AI can suggest inbox items: "I noticed X could be useful — want me to add it to the inbox?" On confirmation, saves via CLI with source=ai.

### 5. AI silent capture in automated pipelines

During build/implement pipelines, the AI captures ideas silently (no interruption) and reports them in the pipeline summary (e.g. build.md Step 9).

### 6. Plan-issues integration

`/mantle:plan-issues` surfaces open inbox items as candidates when starting a planning session, similar to how bugs are surfaced today.

### Flow

1. User runs `/mantle:inbox` or AI suggests an idea during a session
2. Title + optional description captured
3. Saved to `.mantle/inbox/` as a dated markdown file with YAML frontmatter
4. Item has status: open (default), promoted (moved to issue), dismissed
5. During `/mantle:plan-issues`, open inbox items are shown as candidates
6. User decides: promote to brainstorm/issue, keep for later, or dismiss

## Acceptance criteria

- [ ] `mantle save-inbox-item` CLI persists a titled note to `.mantle/inbox/`
- [ ] `/mantle:inbox` prompt captures title + optional description and saves via CLI
- [ ] `.mantle/inbox/` directory created by `mantle init` (added to SUBDIRS)
- [ ] `/mantle:plan-issues` surfaces inbox items as candidates (like bugs do today)
- [ ] Build pipeline reports AI-suggested ideas in the Step 9 summary
- [ ] Inbox items have status (open/promoted/dismissed) to track triage decisions

## Blocked by

None

## User stories addressed

- As a developer, I want to quickly capture a feature idea without full issue structure so that fleeting thoughts are preserved for later triage
- As a developer, I want the AI to suggest ideas it spots during sessions so that the project benefits from patterns the AI notices
- As a developer, I want inbox items surfaced during planning so that good ideas don't get forgotten in a backlog file