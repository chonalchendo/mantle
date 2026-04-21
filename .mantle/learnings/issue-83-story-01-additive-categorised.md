---
issue: 83
title: 'story-01: additive categorised diff stats'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-21'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Additive wrapper preserved existing tests verbatim.** Keeping `collect_issue_diff_stats(...) -> DiffStats` as a thin wrapper over the new `collect_issue_diff_stats_categorised` meant the 10 pre-existing tests (which never wrote a config.md) passed unchanged. The price — mild duplication of a sum-loop — was worth the zero test-churn cost.
- **`load_diff_paths` catching FileNotFoundError is load-bearing.** It's the seam that makes the additive design work in tmp_path tests and real projects that never init'd a config.md. Caught during story-planning (not implementation), which is the right place.

## Harder Than Expected

- **`--shortstat` → `--numstat` was the right call but wasn't obvious.** Once per-file bucketing was needed, the regex parser was dead code. Worth noting for future "add a dimension to an aggregate" refactors: if the aggregate format was the constraint, swap the source format first, then the aggregate collapses to a sum.

## Recommendations

- **For "add a new config field" stories, auto-include a missing-config fallback path.** Any new field that drives domain behaviour will be queried by tests whose fixtures don't write config.md — catch `FileNotFoundError` from `project.read_config` at the loader boundary, not at every call site.
- **When a function change would break N existing tests, consider the wrapper trick first.** Issue 63's learning ("test churn is part of appetite") is real, but sometimes the feature can land additively and skip the churn entirely — as here.