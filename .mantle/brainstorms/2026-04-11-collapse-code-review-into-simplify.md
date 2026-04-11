---
date: '2026-04-11'
author: 110059232+chonalchendo@users.noreply.github.com
title: collapse-code-review-into-simplify
verdict: proceed
tags:
- type/brainstorm
---

## Brainstorm Summary

**Idea**: Collapse per-story code review and post-implementation simplify into a single quality gate
**Problem**: The build pipeline runs two overlapping quality checks — a per-story code-reviewer agent (in implement.md step 7) and a post-implementation simplify step (build.md step 7). They check for many of the same things (unnecessary abstractions, dead code, over-engineering), costing extra tokens and time with diminishing returns.
**Vision alignment**: Strong — streamlines the build pipeline without changing the workflow. "Python orchestrates deterministically; AI implements creatively" is better served by one focused AI quality pass than two overlapping ones.

## Exploration

**The overlap**: The code reviewer checks spec compliance + code quality. The simplify step applies an 8-pattern LLM Bloat Checklist. Five of the eight patterns overlap with what the code reviewer already checks. The user wasn't fully aware the per-story code review existed — a signal of hidden complexity.

**Per-story vs post-implementation**: Per-story catches issues early but runs N times (2-5 stories typical). Post-implementation runs once with a cross-story view. TDD already covers spec compliance (tests are the spec). The cross-story view is the thing that can't be replicated per-story.

**What to pull from code review into simplify**: Nothing. The 8-pattern checklist already covers code quality. TDD covers spec compliance. The simplify step itself stress-tests test quality — if tests are testing implementation details, they break during simplification, which is the natural signal.

## Challenges Explored

**Assumptions surfaced:**
1. Per-story code review rarely catches things tests don't — confirmed: TDD covers spec, and most reviews return PASS.
2. Simplify can absorb code review value without bloating — resolved: nothing needs absorbing, the checklist is already sufficient.
3. Smart skip condition is computable cheaply — confirmed: `git diff --stat` gives file count + lines changed in one call.

**Test quality concern**: Code review checks "do tests verify behaviour, not implementation?" — but simplification itself is a refactoring pass that breaks brittle tests naturally. Self-correcting pipeline.

## Approaches Considered

| Approach | Description | Key Trade-off |
|----------|-------------|---------------|
| Clean cut | Remove code-reviewer from implement.md. Update build.md skip condition to composite heuristic (file count + lines changed via git diff --stat). Simplify checklist unchanged. | Minimal change, fast to ship. Needs a sensible default threshold. |
| Always simplify | Same removal, drop skip condition entirely in build mode. | Simpler logic but wastes tokens on trivial changes. |

## Verdict

**Verdict**: proceed
**Reasoning**: The per-story code review is paying a high token/time cost for marginal quality gain over TDD, while missing the cross-story patterns that actually need a separate pass. Collapsing into the simplify step (which already catches issues the code review misses) is a clean efficiency win with no quality loss.
**If proceeding**: Create an issue to (1) remove per-story code-reviewer from implement.md step 7 and its fix cycle, (2) update build.md skip condition to use composite file count + lines changed threshold, (3) keep the simplify checklist unchanged. Small scope — touches two prompt files and possibly the CLI for computing lines changed.