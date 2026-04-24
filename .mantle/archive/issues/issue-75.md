---
title: Model tiering config and A/B harness for build pipeline stages
status: dropped
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
- status/dropped
acceptance_criteria:
- id: ac-01
  text: Per-stage model config in `.mantle/config.md` is read by build.md and respected
    by spawned agents.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: At least one tier preset (e.g. `budget`, `balanced`, `quality`) is documented.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: A/B harness produces a side-by-side cost + quality summary for two runs of
    the same issue.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Tests cover config parsing, default fallback, and at least one preset.
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

## Status: Superseded

Closed on 2026-04-24 per brainstorm `2026-04-22-gsd-scout-backlog-reshape.md` (decision 1). Issue 84 carved 75 down and shipped the dominant lever — per-stage model tier config in `core/project.py`, presets in `cost-policy.md`, escape-hatch overrides, full tests. That covers ACs 01, 02, 04, and 05 of this issue. The remaining live work is AC-03 (the A/B harness), which has been re-opened as **issue 89 — A/B harness for build pipeline (replaces 75-remainder)** with the 84-retrospective lessons baked in (no `/mantle:build` nesting, sentinel-rejection in the verifier).

Original ACs and content preserved below for reference.

## Why

`/mantle:build` currently uses `opus-high` for story-implementer regardless of issue complexity. Two inbox items (2026-04-09 `ab-test-modeleffort-strategy`, 2026-04-16 `model-tiering-strategy`) ask to (a) make the per-stage model configurable and (b) provide a way to A/B test alternate model strategies for cost/quality.

## What to build

Two related capabilities:
1. **Model tiering config.** `.mantle/config.md` knobs for which model each pipeline stage uses (shape/plan/implement/simplify/verify). Defaults preserve today's behavior.
2. **A/B harness.** A way to run the same issue under two configurations and compare output quality + token cost. Could be as simple as a `mantle build --strategy A` flag plus a structured comparison report.

Shaping should split into separate issues if scope is too large for one.

## Acceptance criteria

- [ ] ac-01: Per-stage model config in `.mantle/config.md` is read by build.md and respected by spawned agents.
- [ ] ac-02: At least one tier preset (e.g. `budget`, `balanced`, `quality`) is documented.
- [ ] ac-03: A/B harness produces a side-by-side cost + quality summary for two runs of the same issue.
- [ ] ac-04: Tests cover config parsing, default fallback, and at least one preset.
- [ ] ac-05: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user paying for opus on mechanical issues, I want a budget tier I can set per-stage so I don't burn opus tokens on simple work.
- As a Mantle maintainer, I want to compare model strategies on the same issue so my recommended defaults are evidence-based.