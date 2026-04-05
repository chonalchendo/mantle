---
issue: 30
title: Improve skill discovery — critical thinking first, parallel stories, code review
  value
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-05'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Critical thinking before code**: Running /critical-thinking before creating the issue produced a clear problem decomposition, ruled out unnecessary work (index-note-as-discovery-mechanism), and identified the right two-pronged solution (tag filtering + auto-generated indexes). This pattern should be repeated for any issue that starts as a vague idea.
- **Parallel independent stories**: All 3 stories were genuinely independent (different functions in the same module), ran in parallel via worktree isolation, and completed STATUS: DONE on first attempt. Designing for story independence during planning pays off in build speed.
- **Small batch sizing was accurate**: The issue was correctly scoped — no scope creep, no surprises, no blocked stories. The shaped plan held exactly.
- **Code review caught a real bug**: The post-implementation review found that the generated marker was placed before YAML frontmatter, which would break Obsidian parsing. This was fixed before verification. The review step earns its keep.

## Harder Than Expected

- Nothing — this was a clean run from start to finish.

## Wrong Assumptions

- None — the shaped plan held exactly as designed.

## Recommendations

1. **Run /critical-thinking for idea-stage features**: When a user has a vague idea (not a well-defined feature), critical thinking analysis before issue creation saves significant rework by narrowing the solution space.
2. **Design for story independence**: When all stories in an issue are independent, the build pipeline runs them in parallel, cutting implementation time significantly. Prioritise this during story planning.
3. **Code review is non-negotiable**: Even with all tests passing, the review step caught a bug that would have caused real problems in production (broken Obsidian frontmatter). Never skip it.
4. **Sonnet is sufficient for pattern-following stories**: All 3 stories were single-module extensions following existing patterns. Sonnet completed all of them first-try, confirming the model selection heuristic from previous issues.