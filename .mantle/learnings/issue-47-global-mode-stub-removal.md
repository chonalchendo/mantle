---
issue: 47
title: global-mode-stub-removal
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-10'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Shaped approach was the clear winner** — `dir-existence-as-signal` was obvious from the start; the two alternatives (sentinel marker, env var) were dismissed in seconds. Shaping took minutes, not a full session.
- **Single-story sizing was correct** — the 2-file production change across `core/project.py` and `core/migration.py` was too tightly coupled to split. Story-implementer delivered it in one pass, no retries.
- **Test migration was mechanical but thorough** — 4 test files rewritten, 3 tests deleted, 2 added, all green first try. TDD approach worked well: rewrote tests first, then made production changes.
- **Post-implementation review caught real cleanup** — orphaned `_update_config_at` helper and redundant `test_missing_config` were flagged and fixed before verification. This is the review step earning its keep.
- **Net deletion (-117 lines)** — the change removed more code than it added, which is the right shape for "remove a load-bearing workaround."

## Harder than expected

- Issue was straightforward overall. No blocked stories, no test failures, no rabbit holes.

## Wrong assumptions

- **Story plan claimed "keep `TestMigrateToLocal` unchanged" but one of its tests asserted the exact dead write being removed.** The implementer correctly resolved the contradiction (deleted the test), but the planning step should have caught it. When a story says "keep X unchanged," the planner needs to verify that X doesn't assert behaviour the production changes remove.
- **Build pipeline assumed verification would transition the issue status.** The verify agent confirmed 8/8 pass but didn't call `transition-issue-verified`, causing a two-step manual fix during review. Either the verify prompt or the build orchestrator should handle this.
- **The `save-review-result` → `transition-issue-approved` ordering bug from issue 46 recurred.** `transition-issue-approved` archives the issue file; `save-review-result` then can't find it. Same side-effect-ordering pattern, different command pair. The issue-46 learning ("trace all downstream dependents") wasn't embedded into the review.md prompt flow yet.

## Recommendations

1. **Story planner: cross-check "keep unchanged" claims against the production diff.** Scan every test in modules marked "unchanged" for assertions that contradict the planned production changes. This catches planning-implementation mismatches before the implementer has to use judgement.
2. **Fix the review.md prompt ordering: `save-review-result` before `transition-issue-approved`.** This is the recurring side-effect-ordering issue from issue 46. The transition archives files; any command that reads the issue file must run before the transition fires.
3. **Build orchestrator or verify.md should call `transition-issue-verified` after passing verification.** Currently the verify agent confirms pass but leaves the issue in `implemented` status, requiring manual intervention during review.
4. **Story spec should include direct cleanup of dead code created by its own edits.** When a story removes all call sites of a helper, the spec should say "remove the helper too." Deferring to a separate simplify pass is artificial — the implementer has the full context right now.