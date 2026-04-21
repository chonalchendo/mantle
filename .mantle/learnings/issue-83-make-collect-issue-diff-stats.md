---
issue: 83
title: Make collect-issue-diff-stats source/test paths configurable for non-src/tests
  projects
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-21'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Additive wrapper was the right call.** Keeping `collect_issue_diff_stats` as a thin wrapper over the new `collect_issue_diff_stats_categorised` avoided churning ~10 existing tests and kept `build.md` Step 7's grep contract intact — slice stayed at `core, cli, tests` and never leaked into `claude-code`. Directly inverts issue 63's "test churn is part of appetite" lesson: sometimes the feature lands additively and skips the churn entirely.
- **Story-plan caught the `FileNotFoundError` seam before implementation.** Spotting that `_init_git_repo` in existing tests never writes `config.md` — and that `load_diff_paths` therefore must swallow the error — happened during story planning, not mid-implementation. Saved at least one debug loop.
- **Shape was mechanical, not subjective.** Issue body implicitly dictated approach ("Keep current defaults" + slice excludes `claude-code`). Second issue in a row (63, 83) on `collect_issue_diff_stats` where the body pre-answered its own shaping question — pattern worth naming.

## Harder Than Expected

- **`--shortstat` → `--numstat` swap wasn't obvious up front.** Once per-file bucketing was needed, the regex parser was dead code. Reasonable catch during implementation, but the shaped doc could have flagged it.
- **Nothing else surprising** — pipeline ran clean through shape, plan, implement, simplify, verify.

## Wrong Assumptions

- **Underestimated the diff would stay under the simplifier threshold.** 502 `lines_changed` (mostly test rows), well over 50. Same underestimate pattern as issue 63. Shaping appetite for "add a dimension to an aggregate" stories should bake in ~60-100 test-row lines by default.
- **Assumed `just check` would be the tight point.** Whole check suite passed first try. The tight point was the verifier's live E2E, which validated the `"other"` bucket end-to-end on a `/tmp` fixture — worth more than any unit test.

## Recommendations

- **"Add a dimension to an aggregate" is a named shape.** If the aggregate format (like `--shortstat`) was the constraint, swap to a per-element format (`--numstat`) first — the aggregate collapses to a sum. Add to shaping vocabulary.
- **Wrapper-trick over signature-change when existing tests are numerous.** Issue 63 paid the churn cost; issue 83 skipped it with a wrapper. When > 3 existing tests would need updating, check the wrapper option first.
- **For new config-driven behaviour, add a missing-config fallback at the loader.** Not at every call site. Catch `FileNotFoundError` from `project.read_config` once, in the domain helper (`load_diff_paths`-style).
- **Live E2E in verifier keeps paying its weight.** Second issue in a row (82, 83) where the verifier caught real end-to-end behaviour the unit tests couldn't. Keep in default verification strategy.