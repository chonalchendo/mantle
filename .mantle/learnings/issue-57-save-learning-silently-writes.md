---
issue: 57
title: save-learning silently writes after issue archived
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-15'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Happened

Fixed a side-effect-ordering bug: `mantle save-learning --issue NN` used to silently write a learning file even when the target issue had been archived (or never existed). Added an `IssueNotFoundError` precondition in `core.learning.save_learning` using `issues.find_issue_path`, caught it in the CLI shim with an actionable message. Flipped the staleness-regression test from `xfail` to a real assertion.

Ran end-to-end through `/mantle:build` with auto-shape (option 1, strict) and a single small story. Simplify pass cleaned up test-file import style. Verification and review both passed first time.

## What Went Well

- **xfail-as-spec pattern** — The regression test was already written in `test_staleness_regressions.py` marked `xfail(strict=False)`. Implementation reduced to "make this xfail go away," which gave an unambiguous, verifiable target. Worth replicating deliberately for the remaining staleness-family issues (46, 47, 49, 56 and any future siblings).
- Issue body had the two behaviour options (strict vs permissive) written up front, which made auto-shaping safe — the build orchestrator just picked the smallest-appetite option that satisfied all criteria. Suggests issues authored with explicit approach alternatives are good candidates to skip `/mantle:shape-issue` manual review.
- Precedent from issues 46/47/49 made the shape obvious: same `find_issue_path` guard pattern, same CLI catch/exit-1 shape. Consistency across the family is paying off.

## Harder Than Expected

Nothing material. One-shot implementation passed first time; tests, verify, and review all green.

## Wrong Assumptions

None that surfaced.

## Recommendations

- **Adopt xfail-as-spec explicitly** for the staleness-family follow-ups: when a regression test lives ahead of the fix, put it in place as `xfail(strict=False)`, open the issue citing the test path, and let the fix be "flip the marker." This minimises shape-time ambiguity.
- When issues describe 2 behaviour options up front (strict vs permissive, etc.), flag them as auto-shape-friendly so the build pipeline doesn't need a human shape pass for every family-sibling bug.