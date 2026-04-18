---
title: End-of-build triage prompt for surfaced side issues
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

`/mantle:build` and the `/mantle:implement` step often surface side issues during a run (e.g. flaky test, code smell, missing docs). Today these dissolve into the session log. They should be triaged on the spot: fix-now, file-as-issue, or ignore (inbox 2026-04-16).

## What to build

A triage step at the end of `/mantle:build` (and `/mantle:implement` when used standalone) that:
- Lists issues surfaced during the run (parsed from session log + agent output).
- For each, asks the user to classify: **fix now** | **needs new issue** | **doesn't need fixing**.
- For "needs new issue", auto-drafts an inbox item (or full issue body) and saves via existing `save-inbox-item` / `save-issue` commands.
- For "fix now", spawns a focused fix in the current session.

## Acceptance criteria

- [ ] Triage step appears at the end of `/mantle:build` and `/mantle:implement`.
- [ ] User can dismiss without classifying (skip).
- [ ] "needs new issue" choice writes an inbox item with title and body pre-filled.
- [ ] No regression in existing build/implement flow when triage is empty.
- [ ] Documented in build.md prose.

## Blocked by

None.

## User stories addressed

- As a Mantle user finishing a build, I want surfaced side issues triaged before I move on so I don't lose them or pollute the next issue's scope.