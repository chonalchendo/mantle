---
title: Worktree parallel implementation
status: dropped
slice: [core, tests]
story_count: 0
verification: null
tags:
  - type/issue
  - status/dropped
---

## Parent PRD

product-design.md, system-design.md

## Status: Dropped

This issue was designed around passing the `--worktree` flag to `claude --print` subprocess invocations (see `orchestrator.py`). Issue 13 story 5 replaced subprocess orchestration with native Agent subagents — there is no subprocess to pass `--worktree` to. The issue's approach is no longer viable.

Worktree isolation is still available to users via Claude Code's native `/worktree` command or `EnterWorktree` tool. Users who want parallel issue implementation can start a worktree session themselves before running `/mantle:implement`. Automating this is not worth the complexity — it's one user action.

User stories 27-28 are deferred, not deleted. If automated worktree management proves needed, it would be redesigned around the Agent-based architecture (e.g., `implement.md` prompting the user to enter a worktree before starting).

## Original description

Extend the orchestration loop to use Claude Code's native worktree support (`--worktree` flag) for parallel issue implementation. Each issue gets its own worktree and branch, enabling multiple issues to be implemented in separate terminal sessions without conflicts. On successful verify + review, the worktree branch is merged back to main.

## User stories addressed

- User story 27: Auto-create worktree and branch per issue (deferred)
- User story 28: Merge worktree branch on successful verify + review (deferred)
