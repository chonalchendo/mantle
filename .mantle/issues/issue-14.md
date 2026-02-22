---
title: Worktree parallel implementation
status: planned
slice: [core, tests]
story_count: 0
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

Extend the orchestration loop to use Claude Code's native worktree support (`--worktree` flag) for parallel issue implementation. Each issue gets its own worktree and branch, enabling multiple issues to be implemented in separate terminal sessions without conflicts. On successful verify + review, the worktree branch is merged back to main.

This includes:
- Extend `src/mantle/core/orchestrator.py` — worktree creation via `claude --worktree mantle-issue-{N}`, branch management, merge on completion
- Each story's Claude Code invocation uses the same worktree for the issue
- Merge logic: after verify + review, merge `worktree-mantle-issue-{N}` branch to main
- `.claude/worktrees/` added to `.gitignore` (handled by Claude Code)

## Acceptance criteria

- [ ] `mantle implement --issue N` invokes Claude Code with `--worktree mantle-issue-{N}` flag
- [ ] All stories for an issue execute within the same worktree
- [ ] Multiple issues can be implemented in parallel in separate terminal sessions without conflicts
- [ ] On successful verify + review, the worktree branch is merged back to main
- [ ] Tests verify worktree flag is passed to Claude Code subprocess, and merge logic

## Blocked by

- Blocked by issue-13 (needs the base implementation loop)

## User stories addressed

- User story 27: Auto-create worktree and branch per issue
- User story 28: Merge worktree branch on successful verify + review
