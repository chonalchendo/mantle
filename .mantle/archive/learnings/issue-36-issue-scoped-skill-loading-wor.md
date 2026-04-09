---
issue: 36
title: Issue-scoped skill loading — worktree friction, prompt-code surface area
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-07'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Shape held perfectly**: The "Frontmatter filter" approach mapped 1:1 to implementation with no mid-build pivots. Explicit, debuggable design choices in shaping pay off during implementation.
- **Simplification caught a real bug**: Pre-existing broken Python 3 `except` syntax (`except A, B:` instead of `except (A, B):`) in compiler.py was caught during simplification. Two consecutive issues (35 and 36) have had simplification find real issues.
- **Verification caught a wiring gap**: The `--issue` CLI flag worked end-to-end in code, but neither `build.md` nor `implement.md` actually used it. Without the verify step, the feature would have shipped unwired.

## Harder Than Expected

- **Worktree merge complexity**: Stories 2 and 3 ran in parallel worktrees that branched before story 1 committed. Story 2 re-implemented story 1's core changes, requiring manual sorting of which files to keep from each worktree. For a 3-story issue, sequential would have been simpler.
- **Circular import avoidance**: `skills.py` needed to call `issues.load_issue()`, requiring two deferred local imports to avoid circular dependency (`issues → state ← skills → issues`). Code review flagged this as a growing smell.

## Wrong Assumptions

- **Prompt files don't auto-update with code**: Added `compile --issue` flag to CLI and core, but prompt orchestrators (`build.md`, `implement.md`) still called `mantle compile` without it. The build pipeline is code + prompts — changes to one don't propagate to the other.

## Recommendations

1. **Avoid worktree parallelism for small issues**: With ≤3 stories and dependency chains, sequential is faster than dealing with worktree merge conflicts. Reserve worktrees for issues with 4+ truly independent stories.
2. **Prompt files are part of the acceptance criteria surface**: When a feature adds CLI flags or changes command invocation, verify all prompt files that call those commands are updated. Add this as a story planning checklist item.
3. **Simplification has proven value**: Don't skip it even when code looks clean — two consecutive issues have had it catch real issues (security constraint in 35, broken syntax in 36).