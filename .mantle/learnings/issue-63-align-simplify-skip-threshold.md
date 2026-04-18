---
issue: 63
title: Align simplify skip-threshold stats with simplify scope
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-18'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Issue body pre-answered its own shaping question.** The issue text literally said "The choice hinges on whether `collect-issue-diff-stats` has any caller besides Step 7 — a grep across the codebase answers it." Shaping became mechanical: run the grep, cite evidence, pick A. Skills (`cli-design-best-practices`, `design-review`) then confirmed YAGNI framing. When the author can frame the decision as a check-to-run, shaping collapses to a minute of work.
- **Third sonnet one-shot in a row (61, 62, 63).** Common factor: story specs that quote the exact text to add/delete, list the exact files, and enumerate the behavioural cases. Sonnet does not need to invent; it transcribes. Real pattern at this point, not survivor bias — each of those three stories was a surgical docs/prompt/pathspec edit with pre-derived test cases.
- **Simplify paid its way this time.** 127 lines > 50 → ran. Refactorer found three real wins: folded 7 standalone `mkdir` calls into `_commit_content`, replaced an inline 8-line `subprocess` block in `test_only_deletions` with `_commit_content(..., "")`, and trimmed a cross-document coupling note from the docstring. None were the target of the issue; all were genuine bloat the new tests had added. Good case for why the gate should stay at 50 rather than being loosened.
- **Verifier evidence was load-bearing for AC3.** It actually ran `git diff --shortstat c825f38^..58dcb9e -- src/ tests/` and saw 17 lines. The AC was a numeric claim about issue 62's commit range; the verifier treated it as one to reproduce, not one to accept on faith.

## Harder Than Expected

- **Existing-test churn was larger than the feature itself.** Four tests modified (`test_single_commit`, `test_multi_commit_aggregation`, `test_only_deletions`, `test_handles_padded_single_digit`) to place files under `src/`. That's 4 tests touched for a 2-line feature change. Reader of `15335d2` in isolation might think "why is the feature commit so big?" — the answer is test-suite alignment, not feature scope. Predictable when changing a function's default behaviour, but worth noting: "adds a default filter" ≈ "every test that committed unfiltered paths needs updating".
- **Nothing else — pipeline was clean.**

## Wrong Assumptions

- **Underestimated the simplify line count.** Called it "small batch" with minimal line change; actual `lines_changed=127` comfortably cleared the 50 threshold. Reason: counted feature lines (~5 in simplify.py, ~1 in build.md), not test-churn lines (~60 across four modifications + four new tests). On refactor issues that force default-behaviour changes, test churn is often larger than the feature. Future shaping should estimate `feature + test-realignment`, not just feature.
- **Open question from issue 62's retro is now partly stale.** "Align fast-path line threshold (10) with simplify-skip (50)" implied the two thresholds should match because they gate similar agent spawns. Issue 63 corrected the *denominator* for one of those thresholds; the fast-path 10-line cap is about total Branch-A eligibility, not simplify scope. They were never really measuring the same thing. Drop this from the carry-over list.

## Recommendations

- **Name the "issue body states the decision criterion" pattern.** For refactor/alignment issues, the author should frame the decision as a runnable check ("grep X", "count callers of Y", "read file Z") rather than as a subjective call. Makes shaping deterministic and leaves an evidence trail. Consider adding to `/mantle:add-issue` as a nudge for refactor-class issues.
- **Keep the simplify threshold at 50.** Second issue in a row (62, 63) where simplify's post-threshold run found real wins. The concern prior to 63 was false-firing on prose diffs; that's structurally fixed now. At 50 with accurate scope, simplify is paying for itself.
- **Loop closed on the simplify-gate pain point.** Three prior issues (60, 61, 62) observed the same misfire; 63 fixed the root cause. Don't expect new edge cases — the fix is structural (same pathspec in both places), not heuristic.
- **Test-suite churn is a shaping signal.** When changing a function's default behaviour, estimate the test-update cost and include it in appetite sizing. A "small batch" feature can carry a "medium batch" test delta. Not a problem — but knowing upfront prevents the next "why is this commit so big?" moment.
- **Scope-at-source over flag-at-callsite.** When a tool's output feeds a downstream decision and only one caller exists, filter at the tool, not at the call. Generalises: same principle applies to any future telemetry/reporting command whose single consumer wants a subset view. The grep-then-decide pattern from shaping directly produces this call.