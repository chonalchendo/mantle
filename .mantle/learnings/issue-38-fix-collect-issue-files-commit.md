---
issue: 38
title: Fix collect-issue-files commit detection
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-07'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- Shaping correctly identified the root cause (loose grep pattern) before code was written
- Scope-delimited grep `(issue-N)` was the right fix — simpler than regex, naturally fits conventional commits
- Single-story decomposition was appropriate for a focused bug fix
- Clean pipeline run: shape → plan → implement → simplify → verify all passed first try

## Harder Than Expected

- Nothing — this was a clean, well-scoped bug fix that went exactly as planned

## Wrong Assumptions

- The original issue description suggested story-implementer agents don't reliably follow the commit pattern. In reality, agents follow `feat(issue-N):` consistently — the bug was the grep being too loose, not the commit messages being wrong. Lesson: investigate the query logic before assuming the data is at fault.

## Recommendations

- When grepping conventional commits, use the parenthesized scope `(issue-N)` rather than bare text `issue-N` to prevent partial number matches
- When debugging "command returns wrong results", check the query/filter logic first before assuming the input data is wrong
- Small bug fixes with clear root causes work well as single-story issues — no need to artificially split