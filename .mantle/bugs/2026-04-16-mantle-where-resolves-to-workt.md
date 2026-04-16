---
date: '2026-04-16'
author: 110059232+chonalchendo@users.noreply.github.com
summary: mantle where resolves to worktree .mantle/ instead of the project's real
  .mantle/
severity: high
status: open
related_issue: null
related_files:
- src/mantle/cli/
- .mantle/state.md
fixed_by: null
tags:
- type/bug
- severity/high
- status/open
---

## Description

When Claude Code runs inside a git worktree under .claude/worktrees/, 'mantle where' returns the worktree's own .mantle/ path. But the project's state lives in the primary repo's .mantle/ — worktrees typically don't carry .mantle/ state (it's local/untracked, and each worktree starts without it or with stale copies). Result: /mantle:build and other commands read an empty/wrong issues/ directory and falsely report that an issue doesn't exist. Discovered while running /mantle:build 60 from a worktree — issue 60 was reported missing, but it exists in /Users/conal/Development/mantle/.mantle/issues/.

## Reproduction

1. From the primary mantle checkout, create an issue (e.g. issue 60) via /mantle:plan-issues. 2. Create or enter a git worktree under .claude/worktrees/<name>. 3. Run 'mantle where' — it returns <worktree>/.mantle. 4. Run /mantle:build 60 — the pipeline reports 'Issue 60 does not exist' even though it exists in the primary repo's .mantle/issues/.

## Expected Behaviour

mantle where should resolve to the project's canonical .mantle/ directory regardless of which worktree the caller is in. Option A: detect git worktree and walk up to the primary worktree's root (git rev-parse --path-format=absolute --git-common-dir -> parent). Option B: store .mantle/ in the user's global/project-config area indexed by primary repo path. Either way, all worktrees of the same project should share the same .mantle/.

## Actual Behaviour

mantle where returns <cwd-worktree>/.mantle, which is a separate and usually empty/stale copy. Downstream commands (build, status, plan-issues) operate on the wrong state.
