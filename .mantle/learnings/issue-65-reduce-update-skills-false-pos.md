---
issue: 65
title: Reduce update-skills false positives from description-overlap matching
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-20'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What went well

The shaping's empirical per-issue diff across issues 40-63 (see archived shaped doc) was the decisive step. It converted 'should we drop this rule?' from a judgement call into a counted decision: 83 skills would be dropped, zero added, with visible false-positive patterns (investor philosophies on CLI work, DuckLake on path fixes, etc.). That measurement effectively pre-satisfied AC #1 and AC #2 before any code was written.

The implementation followed the shaped doc line-by-line: +13/-60, pure deletion. Three deletions in core/skills.py (rule, precomputation, dead helpers) plus two test removals and one pin test. Clean.

## Harder than expected

Nothing. This is a signal the shaping was well-calibrated for a small-batch change — pricey empirical sweep up front, trivial implementation after.

## Wrong assumptions

The shaped doc flagged a follow-up: add tags to skills like cyclopts, Design Review, CLI design best practices to recover legitimate matches lost by dropping the description-overlap rule. Nothing has been done on that follow-up in the week since, and no subsequent issue (66, 74, 76, 77, 78, 79) has surfaced a concrete missing-match report. Soft evidence the narrower matching is fine in practice and the follow-up is premature work. Revisit only when a concrete miss is reported.

## Recommendations

1. **For heuristic / matching / scoring rule changes, bake an empirical sweep across the past N issues into shaping as standard.** It collapses judgement calls into obvious calls and pre-satisfies measurement-shaped ACs.

2. **Pure-deletion shaping ACs are great.** AC #1 and AC #2 were literally about the count/diff produced during shaping itself. When the shaping artifact IS the evidence, verification is cheap.

3. **/mantle:simplify observation (d955a87):** the post-impl simplify pass spidered into unrelated pre-existing code in the same file — cleaned up a duplicate msg assignment in _validate_proficiency and hardcoded marker strings in TestMigratedSkillLineCount. Net-positive for codebase quality but blurs 'what did this issue change' in git blame. Not a bug, but worth knowing: simplify has opinions about the neighbors, not just your diff.