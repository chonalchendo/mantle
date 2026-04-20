---
title: flip-ac --pass flag errors; verify.md drives users into the broken path
status: verified
slice:
- cli
- claude-code
- tests
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- cyclopts
- pydantic-discriminated-unions
- python-314
tags:
- type/issue
- status/verified
acceptance_criteria:
- id: ac-01
  text: Running the exact command shown in `verify.md` for marking an AC passed succeeds
    without error.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-02
  text: '`--fail` still marks an AC failed.'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-03
  text: A test covers the "mark passed" CLI path using the form documented in verify.md.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-04
  text: '`just check` passes.'
  passes: true
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

verify.md instructs agents to run `mantle flip-ac --issue N --ac-id X --pass`, but cyclopts rejects `--pass` with `Unknown option: "--pass"`. `passes=True` is the default, so the bare form works and `--fail` works — but agents following the prose hit the error path first. Surfaced live during /mantle:build 77 on 2026-04-20.

## What to build

Choose one of two fixes (pick the cheaper and land it):

- (a) Make cyclopts accept `--pass` explicitly as a negation-friendly alias for `passes=True`, so the documented form matches the CLI.
- (b) Drop the `--pass` form from verify.md and document `mantle flip-ac --issue N --ac-id X` (default = pass) alongside `--fail`.

Whichever is chosen, the CLI and the prompt prose must agree.

## Acceptance criteria

- [x] ac-01: Running the exact command shown in `verify.md` for marking an AC passed succeeds without error.
- [x] ac-02: `--fail` still marks an AC failed.
- [x] ac-03: A test covers the "mark passed" CLI path using the form documented in verify.md.
- [x] ac-04: `just check` passes.

## Blocked by

None

## User stories addressed

- As an agent running /mantle:verify, I want the documented flip-ac command to execute without error on the first try.