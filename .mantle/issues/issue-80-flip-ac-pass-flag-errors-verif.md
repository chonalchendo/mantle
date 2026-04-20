---
title: flip-ac --pass flag errors; verify.md drives users into the broken path
status: planned
slice:
- cli
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

verify.md instructs agents to run `mantle flip-ac --issue N --ac-id X --pass`, but cyclopts rejects `--pass` with `Unknown option: "--pass"`. `passes=True` is the default, so the bare form works and `--fail` works — but agents following the prose hit the error path first. Surfaced live during /mantle:build 77 on 2026-04-20.

## What to build

Choose one of two fixes (pick the cheaper and land it):

- (a) Make cyclopts accept `--pass` explicitly as a negation-friendly alias for `passes=True`, so the documented form matches the CLI.
- (b) Drop the `--pass` form from verify.md and document `mantle flip-ac --issue N --ac-id X` (default = pass) alongside `--fail`.

Whichever is chosen, the CLI and the prompt prose must agree.

## Acceptance criteria

- [ ] ac-01: Running the exact command shown in `verify.md` for marking an AC passed succeeds without error.
- [ ] ac-02: `--fail` still marks an AC failed.
- [ ] ac-03: A test covers the "mark passed" CLI path using the form documented in verify.md.
- [ ] ac-04: `just check` passes.

## Blocked by

None

## User stories addressed

- As an agent running /mantle:verify, I want the documented flip-ac command to execute without error on the first try.