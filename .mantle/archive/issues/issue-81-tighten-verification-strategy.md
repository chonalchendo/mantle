---
title: Tighten verification-strategy handoff to prevent agents skipping config.md
status: approved
slice:
- claude-code
story_count: 1
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- Production Project Readiness
- Python package structure
- cyclopts
- edgartools
- pydantic-project-conventions
- python-314
- streamlit-aggrid
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: The handoff prose in `verify.md` (and any other affected command) states the
    precedence explicitly — config.md first, introspect-project only as a fallback.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-02
  text: The prose uses directive language ("check", "only if absent") rather than
    loose conditionals.
  passes: true
  waived: false
  waiver_reason: null
- id: ac-03
  text: A smoke run of /mantle:verify against a project with a configured verification_strategy
    does not invoke `mantle introspect-project`.
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

The subagent handoff currently reads along the lines of "if no verification strategy is configured, run `mantle introspect-project`" — agents interpret that loosely and sometimes skip the config.md check or run introspect-project on every call. The intent is: config.md's `verification_strategy` is the source of truth; introspect-project is a last-resort fallback only when the field is missing or empty.

## What to build

Reword the prompt so the precedence and the last-resort nature are unambiguous:

1. Check `config.md` for a `verification_strategy` field with a non-empty value.
2. If present, use it verbatim.
3. Only if absent or empty, fall back to `mantle introspect-project`.

Update every place the handoff prose appears (verify.md and any other command that defers to it).

## Acceptance criteria

- [x] ac-01: The handoff prose in `verify.md` (and any other affected command) states the precedence explicitly — config.md first, introspect-project only as a fallback.
- [x] ac-02: The prose uses directive language ("check", "only if absent") rather than loose conditionals.
- [x] ac-03: A smoke run of /mantle:verify against a project with a configured verification_strategy does not invoke `mantle introspect-project`.
- [x] ac-04: `just check` passes.

## Blocked by

None

## User stories addressed

- As a maintainer, I want verify.md to unambiguously use the configured verification strategy so agents don't waste turns re-detecting it.