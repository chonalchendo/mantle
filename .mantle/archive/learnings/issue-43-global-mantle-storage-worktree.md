---
issue: 43
title: Global .mantle/ storage — worktree limitations and large mechanical changes
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-07'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Thin Resolver approach was exactly right.** A single `resolve_mantle_dir()` function plus mechanical replacement was the correct level of abstraction — no over-engineering needed.
- **4-story decomposition was clean.** Resolver → module updates → migration → CLI mapped naturally to the work and allowed parallel execution of stories 2 and 3.
- **Simplification step caught real issues.** The refactorer found and removed a dead `_write_stub_config` helper in migration.py that duplicated logic from project.py.

## Harder Than Expected

- **Story 2 (update 22+ modules) was too large for a single agent.** The worktree agent only completed 3 of 22 files before running out of context. Required re-spawning 3 parallel agents to finish the job. Significant friction.
- **Worktree branches were based on pre-story-1 commits**, meaning parallel agents didn't have the resolver function they depended on. Story 3's agent re-implemented story 1's functions independently.
- **Worktree agents didn't commit their changes**, so merging required manual file copying and fix-up rather than clean git merge.

## Wrong Assumptions

- None significant. The approach was sound; execution friction was the main issue.

## Recommendations

- **Split "update N files" stories when N > 7.** A story touching 22 files is too large for a single agent context window. Split into 2-3 stories of ~7 files each.
- **Improve worktree setup in the build pipeline.** Worktrees should be based on the latest commit including completed dependency stories, not the branch head at pipeline start.
- **For mechanical replacements, use parallel implementer agents (not story-implementer).** The `implementer` subagent type with batches of 5-7 files was more reliable than a single story-implementer for 22+ files.
- **Grep audit after mechanical changes.** Running `grep -rn '".mantle"' src/` before and after was essential for verifying completeness. Include this as a standard step in stories that do bulk replacements.