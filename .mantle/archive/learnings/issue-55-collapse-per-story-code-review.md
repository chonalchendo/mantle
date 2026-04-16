---
issue: 55
title: Collapse per-story code review into simplify step
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-12'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What went well

- Brainstorm pre-work made shaping near-trivial — two approaches pre-evaluated, Clean cut clearly beat Always-simplify because ACs 5/6 require a skip condition. Inline shape-in-build-mode took <1 minute.
- Wave-1 parallelism (story 1 opus + story 2 sonnet, concurrent agents) was a real wall-clock win since story 2 was a pure prompt edit. Model choice per story (opus for Python, sonnet for prompt edits) scaled appropriately.
- Simplification caught genuine duplication — `_grep_commits` closure duplicated between `collect_issue_files` and `collect_issue_diff_stats`. The build pipeline's new single quality gate immediately paid rent on its own implementation.

## Harder than expected

- **Story 1 worktree isolation leaked into main.** The Agent result for the isolated worktree run didn't return a `worktreePath` and yet all its file changes appeared directly in the main working tree. Had to commit from main rather than merge a worktree. Mental model of `isolation: "worktree"` may be wrong, or the harness silently fell back.
- **CLI divergence bit at verify and simplify time.** `mantle collect-issue-diff-stats` didn't exist in the globally installed `mantle` yet — had to switch to `uv run mantle`. Known pattern for in-flight CLI changes but still a papercut.
- **`git diff first^..last` counts leak from non-issue commits in the range.** `uv run mantle collect-issue-diff-stats --issue 55` reported 11 files / 422 lines, but only 7 unique files were touched by `feat(issue-55):` commits. Existing `collect_issue_files` has the same quirk. For the 50-line threshold to be accurate, this likely needs per-commit aggregation instead of a single range diff.

## Wrong assumptions

- Assumed worktree isolation is airtight within a single-story-within-wave run. Evidence suggests it isn't, or harness behaviour changed.
- Assumed a range-diff approach matches "lines changed by this issue". It measures "lines changed in the range spanning the issue's commits", which drifts when other commits land mid-issue.

## Recommendations

- When an issue changes `mantle` CLI surface, add `uv run mantle` hints in build.md's Step 7 / Step 8 so future builds don't trip on the staleness. Consider detecting `command not found` in those prompts and falling back automatically.
- Switch `collect_issue_diff_stats` (and probably `collect_issue_files`) to per-commit aggregation (`git show --stat --format= <hash>` per matching commit) for accuracy. File this as a follow-up issue.
- If single-story waves don't need worktree isolation, drop it — it adds cleanup cost without clear benefit. Revisit build.md's per-wave rule: use worktree only when wave has ≥2 parallel stories.