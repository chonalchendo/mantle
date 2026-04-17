---
issue: 62
title: Add a fast-path through /mantle:build for trivial single-file edits
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-17'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Shape's auto-choice rule produced the right call.** B over A wasn't a close call — "smallest appetite that satisfies all ACs" cleanly eliminated A (wider surface) and C (too narrow per the issue body itself). No hand-wringing.
- **Story spec was implementer-ready.** Verbatim text to add, exact subsection headings, full test function body, three design decisions with rationale. Sonnet completed the story with no retry, no NEEDS_CONTEXT.
- **Regression test approach was right-sized.** Three plain assertions over `inline-snapshot` — the test specifies an invariant (Iron Law #2 must survive refactors), not captures drift-prone text. The skill's own anti-pattern list (`"Don't use inline-snapshot for business-logic thresholds or security constants — those need *specification*, not *capture*"`) made the choice obvious.
- **Verifier's AC 5 check was load-bearing.** It pulled the archived issue-60 shaped doc and re-ran the new four-item rubric against it mechanically. That's exactly the kind of evidence the fast-path itself will need to produce when it decides to fire.

## Harder Than Expected

- **Simplify ran on a prose-dominated diff.** files=2, lines_changed=55 — five lines over threshold. Scope filter (`src/` + `tests/`) correctly excluded the build.md prose, leaving only the 17-line new test for the refactorer to inspect. One genuine (if tiny) win — a case-fold fold — but the setup cost (agent spawn, verification) felt disproportionate. Root cause: `collect-issue-diff-stats` counts all changed lines while Step 7's scope is `src/` + `tests/` only. Filed as **issue 63** during the retrospective.
- **Nothing else, really.** Pipeline clean end-to-end.

## Wrong Assumptions

- **Assumed the `cli` slice declaration in the issue frontmatter would matter.** It was a pre-emptive hint for the discarded Approach A. Approach B ended up touching `claude-code` + `tests` only. Issue-time slice declarations bound the upper envelope — shaping can narrow them. No action needed, but future coverage checks should tolerate this.
- **Expected skill-selection signal to be thin again** (as flagged in issue 60/61 learnings). It actually landed: `inline-snapshot`'s anti-pattern list directly informed the regression-test design ("specify, don't capture"), and `design-review` prompted the "branch, not mode boolean" framing in the shaped Strategy. First time in the last three issues that skill reads demonstrably steered a design decision.

## Recommendations

- **Issue 62 is itself meta — the next trivial docs edit is the real test.** The fast-path rubric was implemented but never exercised. When the next single-file template edit comes through `/mantle:build`, watch whether the orchestrator (a) correctly identifies the rubric match, (b) takes Branch A, (c) still routes to Step 8. If Branch A is skipped when it should fire, that's a prose-clarity bug in build.md, not a rubric bug.
- **Consider aligning the fast-path line threshold with simplify-skip (open question from shaping).** Currently fast-path uses ≤10 lines, simplify-skip uses ≤50. Two thresholds for "trivial" across two adjacent steps is cognitive overhead. Either align to 50 (more permissive fast-path, fewer agent spawns) or document why 10 is intentionally stricter. Defer unless the next few fast-path firings show the 10-line cap being hit artificially.
- **Filed issue 63 to align simplify-skip stats with simplify scope.** Third Mantle-internal issue in a row where Step 7's gate over-triggered on a diff dominated by `claude/` prose that the scope filter correctly excludes from the agent. Single source of truth for "what counts as a changed line" in Step 7.
- **Keep the "story spec written at the level of surgical instructions" pattern.** Third issue in a row where sonnet completed a docs-heavy story first-try. The investment in shape-time specificity keeps paying implementation-time dividends.