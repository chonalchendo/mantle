---
title: Audit /mantle:* commands for token-cost conciseness
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

`/mantle:*` commands accumulated prose over many iterations. Some steps may be redundant or overly verbose, costing tokens on every invocation (inbox 2026-04-15). This is investigation-shaped: measure first, decide what to cut.

## What to build

An investigation pass with concrete deliverables:
- Token-count each `claude/commands/mantle/*.md` file.
- Identify the top 3-5 commands by token cost.
- For each, propose specific cuts (redundant prose, duplicate step instructions, pruneable examples) with measured savings.
- Land cuts that preserve behavior; defer or split out anything ambiguous.

## Acceptance criteria

- [ ] Audit report lists every command's token count and ranks by cost.
- [ ] Concrete cuts applied to at least the top 3 commands.
- [ ] Total token savings measured and reported.
- [ ] No behavioral regression — existing `/mantle:build` runs end-to-end.
- [ ] `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user paying for tokens on every `/mantle:*` invocation, I want command prose pruned of redundancy so my recurring cost shrinks without losing the workflow guarantees.