---
title: Context compilation engine + /mantle:status
status: planned
slice: [cli, core, claude-code, tests]
story_count: 4
verification: null
tags:
  - type/issue
  - status/planned
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

- [ ] `mantle compile` reads vault state and renders all `.j2` templates into concrete markdown files in `~/.claude/commands/mantle/`
- [ ] `mantle compile --if-stale` only recompiles when source files have changed (hash-based comparison)
- [ ] A manifest file tracks content hashes of source files used in compilation
- [ ] `/mantle:status` is available in Claude Code and shows current project state compiled from vault data
- [ ] The compiled status includes: project name, status, current focus, blockers, recent decisions, next steps
- [ ] Compilation respects context budgets (status output fits within ~2-3K tokens)
- [ ] Tests cover compilation, staleness detection, hash manifest, and template rendering

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory with state.md)

## User stories addressed

- User story 39: `/mantle:status` shows current project state compiled from vault data
