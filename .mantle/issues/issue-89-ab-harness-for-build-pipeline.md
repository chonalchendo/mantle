---
title: A/B harness for build pipeline (replaces 75-remainder)
status: planned
slice:
- cli
- core
- claude-code
- tests
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria: []
---

## Parent PRD

product-design.md, system-design.md

## Why

Issue 84 shipped per-stage model-tier config + presets + tests (4 of issue 75's 5 ACs). The remaining live AC from 75 is the A/B harness: a way to run the same issue under two model strategies and produce a side-by-side cost + quality report so default recommendations are evidence-based.

Issue 84's retrospective surfaced the load-bearing constraint here: the harness cannot satisfy itself inside a single `/mantle:build` session — `/mantle:build` cannot nest another `/mantle:build`. Any AC that says "produce real numbers" must either run as a standalone CLI (not through build) or be measured by a separate user-driven session and verified with placeholder-sentinel checks.

This issue replaces issue 75 (now closed). The 2026-04-22 GSD scout (gsd-build/get-shit-done) confirmed this carve — model-profile shape is solved by 84; only the comparison harness remains.

## What to build

A standalone `mantle ab-build` (name TBD at shape time) that:
- Takes an issue ID and two strategy names (preset slugs from `cost-policy.md`).
- Runs the build under each strategy in turn (or compares two pre-existing telemetry runs).
- Emits a single side-by-side report: per-stage tokens, wall-clock, dollar cost, story pass/retry/block counts.
- Lives outside `/mantle:build` so it doesn't suffer the self-referential measurement problem.

Shaping should evaluate at least: (a) live dual-run vs (b) post-hoc comparison of two prior telemetry files vs (c) a hybrid where the harness orchestrates one fresh run and diffs against a stored baseline.

## Acceptance criteria

- [ ] ac-01: A CLI entrypoint (e.g. `mantle ab-build`) accepts an issue ID and two strategy names and produces a single comparison report.
- [ ] ac-02: The report includes per-stage tokens, wall-clock seconds, and dollar cost for both strategies, plus a delta column.
- [ ] ac-03: Report cells contain real numerical content — verifier rejects `<fill>`, `TBD`, `pending`, `<x>`, `<y>` placeholder sentinels (84-retro lesson).
- [ ] ac-04: The harness runs from outside `/mantle:build` (no nested-build invocation).
- [ ] ac-05: Tests cover: argument parsing, report format, sentinel rejection, and at least one preset pair.
- [ ] ac-06: `just check` passes.

## Blocked by

None. Builds on issue 84's `core/project.py` `load_model_tier` + `cost-policy.md` preset infrastructure.

## User stories addressed

- As a Mantle maintainer, I want to compare model strategies on the same issue so my recommended defaults are evidence-based.
- As a Mantle user evaluating budget vs quality presets, I want a single command that gives me a side-by-side comparison without manually running two builds and diffing telemetry.

## Notes

- Replaces issue 75 (closed; 4/5 ACs shipped via 84).
- 84 retrospective lessons applied: split self-referential measurement out, sentinel-check the verifier, no `/mantle:build` nesting.
- Source: brainstorm `2026-04-22-gsd-scout-backlog-reshape.md` (decision 1).