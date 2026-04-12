---
title: Query .mantle/ for recurring issues — surface patterns from learnings and retrospectives
status: implementing
slice:
- core
- cli
- claude-code
story_count: 2
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- DuckLake
- Lakehouse Architecture
- OpenRouter LLM Gateway
- Python package structure
- cyclopts
- omegaconf
tags:
- type/issue
- status/implementing
---

## Parent PRD

product-design.md, system-design.md

## Why

As a project accumulates learnings, retrospectives, and brainstorms, patterns emerge — recurring friction, repeated mistakes, or consistent surprises. Currently there's no way to surface these patterns automatically. Users have to manually re-read past learnings to spot trends.

## What to build

A /mantle:query enhancement (or new /mantle:patterns command) that analyzes accumulated vault knowledge — learnings, brainstorms, retrospectives, and shaped docs — for recurring themes. Should identify:

- Repeated friction points across issues
- Consistent over/under-estimation patterns from confidence deltas
- Common skills or slices that cause problems

## Acceptance criteria

- As a user, I can run a command that surfaces recurring patterns from past learnings
- The output groups findings by theme (e.g. "estimation", "testing", "scope")
- Confidence delta trends are summarized (e.g. "issues touching `core` average -1 confidence")
- Works with existing vault structure, no schema changes needed