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
acceptance_criteria:
- id: ac-01
  text: A CLI entrypoint (`mantle ab-build compare <baseline.md> <candidate.md>`)
    accepts two already-written build report files and produces a single comparison
    report.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: The report includes per-stage tokens, wall-clock seconds, and dollar cost
    for both strategies, plus a delta column. Per-stage rows are sourced from
    `StoryRun.stage` (populated by issue 92); runs with `stage=None` group under
    `Unattributed`.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Report cells contain real numerical content — verifier rejects `<fill>`, `TBD`,
    `pending`, `<x>`, `<y>` placeholder sentinels (84-retro lesson).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: The harness runs from outside `/mantle:build` (no nested-build invocation).
    Implementation constraint — takes already-written build files as input so the
    path to nest is closed by construction.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: 'Tests cover: argument parsing, report format (including stage-grouped rows
    and an Unattributed bucket), sentinel rejection, and at least one preset pair.'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Issue 84 shipped per-stage model-tier config + presets + tests (4 of issue 75's 5 ACs). The remaining live AC from 75 is the A/B harness: a way to compare the same issue under two model strategies and produce a side-by-side cost + quality report so default recommendations are evidence-based.

Issue 84's retrospective surfaced the load-bearing constraint: the harness cannot satisfy itself inside a single `/mantle:build` session — `/mantle:build` cannot nest another `/mantle:build`. Any AC that says "produce real numbers" must either run as a standalone CLI (not through build) or be measured by a separate user-driven session and verified with placeholder-sentinel checks.

Issue 92 (landed 2026-04-24) supplied the prerequisite telemetry: `StoryRun.stage` populated from sub-agent `.meta.json` sidecars (`story-implementer→implement`, `refactorer→simplify`, `general-purpose→verify`) plus `StageWindow` attribution for inline parent-session turns (shape, plan_stories, review, retrospective) driven by `mantle stage-begin` marks in `.mantle/telemetry/stages-<session_id>.jsonl`. This issue consumes that data.

This issue replaces issue 75 (now closed). The 2026-04-22 GSD scout (gsd-build/get-shit-done) confirmed this carve — model-profile shape is solved by 84; only the comparison harness remains.

## What to build

A standalone `mantle ab-build compare <baseline> <candidate>` CLI (name confirmed at shape time) that:

- Takes two **already-written** build report paths (from `.mantle/builds/`). Does NOT run builds itself.
- For each input: resolves session_id from the build file frontmatter, uses `telemetry.find_session_file` + `telemetry.read_session` + `telemetry.find_subagent_files` + `stages.read_stages` + `telemetry.group_stories` to reconstruct the per-stage `StoryRun` set.
- Loads prices from a new `prices:` block in `.mantle/cost-policy.md` frontmatter (extends existing file; no new reader path).
- Emits a markdown side-by-side report grouped by stage: per-stage tokens, wall-clock seconds, dollar cost, plus a delta column. Quality signals (retry count, blocked-story count, per-AC pass/fail, simplifier lines-changed) come from already-written state files (`.mantle/issues/issue-NN.md`, `.mantle/stories/issue-NN-story-*.md`) — no new quality instrumentation.

The shape chose **Approach B (split) with post-hoc execution (A.1)**: harness is read-only over existing artefacts. AC-04 holds by construction — no path to nest `/mantle:build`.

See `.mantle/shaped/issue-89-ab-harness-for-build-pipeline-shaped.md` for the full design and approaches considered.

## Acceptance criteria

- [ ] ac-01: A CLI entrypoint (`mantle ab-build compare <baseline.md> <candidate.md>`) accepts two already-written build report files and produces a single comparison report.
- [ ] ac-02: The report includes per-stage tokens, wall-clock seconds, and dollar cost for both strategies, plus a delta column. Per-stage rows are sourced from `StoryRun.stage` (populated by issue 92); runs with `stage=None` group under `Unattributed`.
- [ ] ac-03: Report cells contain real numerical content — verifier rejects `<fill>`, `TBD`, `pending`, `<x>`, `<y>` placeholder sentinels (84-retro lesson).
- [ ] ac-04: The harness runs from outside `/mantle:build` (no nested-build invocation). Implementation constraint — takes already-written build files as input so the path to nest is closed by construction.
- [ ] ac-05: Tests cover: argument parsing, report format (including stage-grouped rows and an Unattributed bucket), sentinel rejection, and at least one preset pair.
- [ ] ac-06: `just check` passes.

## Blocked by

None — issue 92 (per-stage telemetry) is verified as of 2026-04-24.

## User stories addressed

- As a Mantle maintainer, I want to compare model strategies on the same issue so my recommended defaults are evidence-based.
- As a Mantle user evaluating budget vs quality presets, I want a single command that gives me a side-by-side comparison without manually running two builds and diffing telemetry.

## Notes

- Replaces issue 75 (closed; 4/5 ACs shipped via 84).
- 84 retrospective lessons applied: split self-referential measurement out, sentinel-check the verifier, no `/mantle:build` nesting.
- 92 delivered the telemetry contract this harness consumes: `StoryRun.stage`, `find_subagent_files`, `read_meta`, the rewritten `group_stories(parent_turns, subagent_paths, stage_windows)` signature, and the `mantle stage-begin` CLI that populates inline-stage windows.
- Pre-92 builds can still be input A/B files but will show only sub-agent stage attribution (implement / simplify / verify). Inline stages (shape / plan_stories / review / retrospective) only populate for builds captured after their template got the `mantle stage-begin` instrumentation. The renderer should handle this without an error banner — just fewer per-stage rows.
- Source: brainstorm `2026-04-22-gsd-scout-backlog-reshape.md` (decision 1).
- Pure-YAML migration of `.mantle/config.md` + `.mantle/cost-policy.md` (raised as Open Question 1 in shape) is explicitly deferred to a separate small-batch issue under v0.24.0 — do not let plan-stories widen 89 to include it.
