---
title: Package skeleton, CLI entry point, and mantle install
status: planned
slice: [package, cli, core, claude-code, tests]
story_count: 5
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

The foundational end-to-end pipeline: a pip-installable Python package with a Cyclopts CLI entry point and an `install` command that mounts files into `~/.claude/`. After this slice, `uv tool install mantle-ai` works, `mantle install --global` copies a `help.md` command into `~/.claude/commands/mantle/`, and `/mantle:help` lists available commands grouped by workflow phase in Claude Code.

This includes:
- `pyproject.toml` with Hatchling build, `mantle` entry point, and all dependencies (Cyclopts, Rich, OmegaConf, Pydantic, Jinja2)
- `src/mantle/cli/main.py` — Cyclopts app with `install` subcommand
- `src/mantle/cli/install.py` — copies `claude/` directory contents into `~/.claude/`, writes `mantle-file-manifest.json` to track installed file hashes
- `src/mantle/core/manifest.py` — file hash tracking for detecting user modifications on upgrade
- `claude/commands/mantle/help.md` — static command listing all commands by workflow phase
- Rich-formatted CLI output for install confirmation and warnings

## Acceptance criteria

- [ ] `uv tool install .` (local) installs the package and makes `mantle` available on PATH
- [ ] `mantle install --global` copies all files from `claude/` into `~/.claude/` preserving directory structure
- [ ] `mantle install --global` writes `mantle-file-manifest.json` tracking installed file hashes
- [ ] `mantle install --global` on re-run detects user-modified files and warns before overwriting
- [ ] `/mantle:help` is available in Claude Code and lists commands grouped by workflow phase
- [ ] `mantle --help` shows available CLI commands with auto-generated help from Cyclopts
- [ ] Tests cover install file copying, manifest creation, and user modification detection

## Blocked by

None — can start immediately.

## User stories addressed

- User story 1: Single command install via `uv tool install mantle-ai`
- User story 2: `mantle install --global` mounts commands, agents, and hooks into `~/.claude/`
- User story 48: `/mantle:help` lists available commands grouped by workflow phase
