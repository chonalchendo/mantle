---
issue: 33
title: Tag discovery — clean build, skills matching too aggressive, import conventions
  not absorbed
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-05'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Full pipeline in one session**: From idea discussion → add-issue → build → verify → review → approved in a single conversation. The /mantle:build pipeline is maturing — four consecutive issues (27, 28, 30, 33) with zero blocked stories.
- **Code review catches consistent issues**: Both stories had import style violations and test quality issues caught by the post-implementation review step. The review-then-fix cycle is reliable and prevents quality debt from accumulating.
- **Small batch sizing accurate**: The shaped plan (minimal approach, 2 stories, 1 session) held exactly. No scope creep, no surprises, no rabbit holes.

## Harder Than Expected

- **Review fix rounds on both stories**: Both implementing agents produced code that violated the project's import convention ("import modules, not individual names"). This is a recurring pattern — agents read CLAUDE.md but don't reliably absorb all coding standards. Each story needed a fix agent after code review.

## Wrong Assumptions

- **update-skills matching is too aggressive**: `mantle update-skills --issue 33` auto-detected 18 irrelevant skills (Tom Gayner investment philosophy, streamlit, lakehouse architecture, etc.) for a simple CLI tag-listing feature. The matching heuristic needs tightening — it's pulling in skills that share no meaningful overlap with the issue.

## Recommendations

1. **Include import convention explicitly in story specs**: The "import modules, not individual names" rule should be stated in each story's implementation section, not just in CLAUDE.md. Implementing agents absorb story-level instructions more reliably than project-level config.
2. **File a bug for update-skills matching**: The skill detection is too aggressive — matching on broad terms rather than specific technology overlap. This loads implementation agents with irrelevant context and wastes the skills budget.
3. **Build pipeline maturity confirmed**: Four consecutive clean builds validates the pipeline design. The shape → plan → implement → review → verify → approve flow is reliable for small-to-medium issues.