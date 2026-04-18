---
title: Model tiering config and A/B harness for build pipeline stages
status: planned
slice:
- cli
- core
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

`/mantle:build` currently uses `opus-high` for story-implementer regardless of issue complexity. Two inbox items (2026-04-09 `ab-test-modeleffort-strategy`, 2026-04-16 `model-tiering-strategy`) ask to (a) make the per-stage model configurable and (b) provide a way to A/B test alternate model strategies for cost/quality.

## What to build

Two related capabilities:
1. **Model tiering config.** `.mantle/config.md` knobs for which model each pipeline stage uses (shape/plan/implement/simplify/verify). Defaults preserve today's behavior.
2. **A/B harness.** A way to run the same issue under two configurations and compare output quality + token cost. Could be as simple as a `mantle build --strategy A` flag plus a structured comparison report.

Shaping should split into separate issues if scope is too large for one.

## Acceptance criteria

- [ ] Per-stage model config in `.mantle/config.md` is read by build.md and respected by spawned agents.
- [ ] At least one tier preset (e.g. `budget`, `balanced`, `quality`) is documented.
- [ ] A/B harness produces a side-by-side cost + quality summary for two runs of the same issue.
- [ ] Tests cover config parsing, default fallback, and at least one preset.
- [ ] `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user paying for opus on mechanical issues, I want a budget tier I can set per-stage so I don't burn opus tokens on simple work.
- As a Mantle maintainer, I want to compare model strategies on the same issue so my recommended defaults are evidence-based.