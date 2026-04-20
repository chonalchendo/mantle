---
title: Export MANTLE_DIR via Claude Code SessionStart hook instead of per-command
  'mantle where'
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
acceptance_criteria:
- id: ac-01
  text: A SessionStart hook exists that exports `MANTLE_DIR` for the current session.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: At least the highest-frequency command (/mantle:build or equivalent) uses
    `$MANTLE_DIR` and no longer asks the LLM to run `mantle where` when the env var
    is set.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: When `MANTLE_DIR` is not set, commands still function (fallback to the prior
    path).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: A test covers the hook generation / installation path.
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

## Why

Many /mantle:* commands resolve the mantle directory by asking the LLM to run `mantle where`. That's a tool call every invocation, paying latency and token cost for a value that is stable for the whole session. Claude Code hooks (SessionStart) can resolve it once and export `MANTLE_DIR` into the session env, and prompts can reference `$MANTLE_DIR` directly.

Fits the cost-optimisation lens (API billing makes every avoidable call expensive). Also more reliable: no LLM re-derivation, no drift.

## What to build

1. Ship a SessionStart bash hook (via `mantle show-hook-example` or the existing install path) that runs `mantle where` once and exports `MANTLE_DIR`.
2. Update /mantle:* commands that currently prompt the agent to run `mantle where` to reference `$MANTLE_DIR` (with a graceful fallback for users who haven't installed the hook).
3. Document the hook's role and how to opt in.

## Acceptance criteria

- [ ] ac-01: A SessionStart hook exists that exports `MANTLE_DIR` for the current session.
- [ ] ac-02: At least the highest-frequency command (/mantle:build or equivalent) uses `$MANTLE_DIR` and no longer asks the LLM to run `mantle where` when the env var is set.
- [ ] ac-03: When `MANTLE_DIR` is not set, commands still function (fallback to the prior path).
- [ ] ac-04: A test covers the hook generation / installation path.
- [ ] ac-05: `just check` passes.

## Blocked by

None

## User stories addressed

- As a mantle user on API billing, I want high-frequency setup steps resolved once per session so per-command token cost drops.
- As a maintainer, I want a deterministic way to pass session-stable paths into prompts instead of relying on the LLM to re-derive them.