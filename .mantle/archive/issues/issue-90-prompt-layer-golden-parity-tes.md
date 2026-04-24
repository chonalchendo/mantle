---
title: Prompt-layer golden-parity test harness for top commands
status: approved
slice:
- tests
- claude-code
- core
story_count: 3
verification: null
blocked_by: []
skills_required:
- dirty-equals
- inline-snapshot
- python-314
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: A test helper `run_prompt_parity(command, fixture, baseline)` exists and produces
    a structured comparison result.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-02
  text: At least 3 commands (`build`, `implement`, `plan-stories`) have parity tests
    against captured baselines.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-03
  text: A `normalize_prompt_output()` helper strips timestamps, session IDs, absolute
    paths, and git SHAs; documented inline.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-04
  text: A `test_prompt_coverage_policy.py` enumerates every `/mantle:*` command and
    fails if a command is added without an explicit `INTEGRATED` / `UNIT_ONLY` / `DEFERRED`
    classification.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-05
  text: CI runs the parity tests as part of `just check`.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-06
  text: A short doc (in CLAUDE.md or a new `docs/` note) explains how to capture a
    new baseline and how to add a command to the policy.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-07
  text: '`just check` passes.'
  passes: true
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Mantle's biggest testing gap (per 2026-04-22 GSD scout): no prompt-layer regression safety net. Issues 79 (`@file` include refactor + audit-context cuts), 87 (`mantle compress`), and 88 (audit-tokens follow-on cuts) all want to aggressively trim tokens from the highest-cost commands. Without a parity harness, every cut is a leap of faith — there's no way to know whether a refactored prompt still produces equivalent agent behaviour.

GSD's `read-only-parity.integration.test.ts` + `golden-policy.test.ts` pattern solves this: dual-subprocess runs of the same command on a sandbox fixture, then `expect(strip(refactored)).toEqual(strip(baseline))` with a normaliser that masks volatile fields (timestamps, session IDs). A separate policy test enforces that every command is either covered or explicitly listed in an exception registry with a rationale.

Scope tight on purpose: GSD has the harness across 103 commands. Mantle has ~25 commands and needs coverage on the 3 highest-cost ones — `build`, `implement`, `plan-stories`. Full registry coverage is over-engineered for current surface area; the exception-registry pattern lets future commands either opt in or document the deferral.

## What to build

A pytest-driven dual-run harness:
- Captures a baseline output for each in-scope command on a stable fixture.
- Runs the refactored version under the same fixture and compares with a `normalize_prompt_output()` helper (drops timestamps, session IDs, absolute paths, git SHAs).
- Pairs naturally with `dirty-equals` (already in the stack) for partial-shape comparisons and `inline_snapshot` for exact captures.
- A separate `test_prompt_coverage_policy.py` enumerates every `/mantle:*` command and classifies it as `INTEGRATED`, `UNIT_ONLY`, or `DEFERRED` with a rationale. CI fails if a new command is added without a classification.

Initial coverage: `build`, `implement`, `plan-stories`. All other commands marked `DEFERRED` with a stub rationale, to be promoted as needed.

## Acceptance criteria

- [x] ac-01: A test helper `run_prompt_parity(command, fixture, baseline)` exists and produces a structured comparison result.
- [x] ac-02: At least 3 commands (`build`, `implement`, `plan-stories`) have parity tests against captured baselines.
- [x] ac-03: A `normalize_prompt_output()` helper strips timestamps, session IDs, absolute paths, and git SHAs; documented inline.
- [x] ac-04: A `test_prompt_coverage_policy.py` enumerates every `/mantle:*` command and fails if a command is added without an explicit `INTEGRATED` / `UNIT_ONLY` / `DEFERRED` classification.
- [x] ac-05: CI runs the parity tests as part of `just check`.
- [x] ac-06: A short doc (in CLAUDE.md or a new `docs/` note) explains how to capture a new baseline and how to add a command to the policy.
- [x] ac-07: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle maintainer aggressively cutting tokens from top commands, I want a regression safety net so refactors that change agent behaviour fail loudly.
- As a Mantle contributor adding a new `/mantle:*` command, I want CI to force me to make an explicit decision about parity coverage rather than silently skip it.

## Notes

- Pattern source: GSD `sdk/test/integration/read-only-parity.integration.test.ts` + `golden-policy.test.ts` + `mutation-sandbox.ts`.
- Source: brainstorm `2026-04-22-gsd-scout-backlog-reshape.md` (decision 3a).
- Enables aggressive token cuts in 79, 87, 88.