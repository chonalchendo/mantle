---
title: Context compilation engine + /mantle:status
status: done
slice:
- cli
- core
- claude-code
- tests
story_count: 4
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/done
acceptance_criteria:
- id: ac-01
  text: '`mantle compile` reads vault state and renders all `.j2` templates into concrete
    markdown files in `~/.claude/commands/mantle/`'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: '`mantle compile --if-stale` only recompiles when source files have changed
    (hash-based comparison)'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: A manifest file tracks content hashes of source files used in compilation
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: '`/mantle:status` is available in Claude Code and shows current project state
    compiled from vault data'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: 'The compiled status includes: project name, status, current focus, blockers,
    recent decisions, next steps'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Compilation respects context budgets (status output fits within ~2-3K tokens)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: Tests cover compilation, staleness detection, hash manifest, and template
    rendering
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## What to build

The context compilation engine that reads vault state and renders Jinja2 templates into concrete markdown commands, plus the `/mantle:status` compiled command. This includes staleness detection via content hashing so compilation only runs when vault files have changed.

This includes:
- `src/mantle/cli/compile.py` — `mantle compile` and `mantle compile --if-stale` CLI commands
- `src/mantle/core/compiler.py` — compile vault context into commands: read vault state, render Jinja2 templates, write output to `~/.claude/commands/mantle/`
- `src/mantle/core/manifest.py` — content hash tracking for source files, staleness detection (compare current hashes against stored manifest)
- `src/mantle/core/templates.py` — Jinja2 template rendering with vault state context
- `claude/commands/mantle/status.md.j2` — Jinja2 template that renders current project state (status, current focus, blockers, recent decisions, next steps)

## Acceptance criteria

- [ ] ac-01: `mantle compile` reads vault state and renders all `.j2` templates into concrete markdown files in `~/.claude/commands/mantle/`
- [ ] ac-02: `mantle compile --if-stale` only recompiles when source files have changed (hash-based comparison)
- [ ] ac-03: A manifest file tracks content hashes of source files used in compilation
- [ ] ac-04: `/mantle:status` is available in Claude Code and shows current project state compiled from vault data
- [ ] ac-05: The compiled status includes: project name, status, current focus, blockers, recent decisions, next steps
- [ ] ac-06: Compilation respects context budgets (status output fits within ~2-3K tokens)
- [ ] ac-07: Tests cover compilation, staleness detection, hash manifest, and template rendering

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory with state.md)

## User stories addressed

- User story 39: `/mantle:status` shows current project state compiled from vault data
