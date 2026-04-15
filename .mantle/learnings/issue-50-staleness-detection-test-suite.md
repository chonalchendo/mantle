---
issue: 50
title: staleness-detection-test-suite
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-15'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Single-file, three-class structure** matched the work — workflow-level regressions don't naturally belong to one source module, so a top-level `tests/test_staleness_regressions.py` was the right home. Approach A (smallest appetite) was correct; Approach C (fixture-factory library) would have been YAGNI.
- **xfail surfaced a real bug** instead of hiding it: `save-learning` silently writes for archived issues. Pattern worth repeating — when a test asserts a desired contract and the contract isn't implemented, xfail it with a clear reason and file the bug separately. Don't let scope creep into the test PR.
- **`uv run mantle` for subprocess CLI tests** dodged the issue-46 installed-vs-working-tree divergence cleanly. Now a documented pattern (saved in story-level learning).

## Harder than expected

- Less hard than expected, actually — single story, single context window, tests passed on first agent run. Small-batch shaping was accurate.

## Wrong assumptions

- **Build briefing claimed issue-49 left orphan-index cleanup unimplemented.** Wrong — `skills.generate_index_notes` already cleans up orphans. The orphan-cleanup test passed outright; no xfail needed. Lesson: when a build orchestrator hands a learning down to a story-implementer agent, that learning may be stale or misframed. The agent grepped before assuming and saved time. Future build prompts should explicitly tell the implementer "verify the claim before treating it as fact."
- **Assumed `python -m mantle` would work** — package has no `__main__`. Would have wasted time without the agent's verify-first instinct.
- **Implementer used `from x import Name` for SkillNote/ProjectState/_ConfigFrontmatter** despite CLAUDE.md's import-modules-not-names rule. Refactorer fixed one (StoryNote) but missed the others. Reviewer caught them. Lesson: convention violations slip past both implementer AND simplify pass for test files — the design-review skill needs to be loaded explicitly during simplify, not just verify.

## Recommendations

- **Adopt:** xfail-with-inbox-bug pattern for tests asserting unmet contracts. Documents the bug, prevents regression once fixed, keeps PR scope tight.
- **Adopt:** `[\"uv\", \"run\", \"mantle\", ...]` for any subprocess CLI test in this repo. Matches `tests/test_package.py`.
- **Fix in build prompt:** when constructing the per-story context brief, mark each learning bullet with "verify before applying" if it's >2 days old or claims a bug exists. The orphan-cleanup misclaim could have been a long detour.
- **Fix in simplify pass:** simplify agent should re-check CLAUDE.md import rules on test files; right now it focuses on production code conventions.
- **Avoid:** importing private (underscore-prefixed) symbols across module boundaries even in tests. `issues._slugify_title`, `skills._slugify`, `project._ConfigFrontmatter` all create test brittleness for unrelated refactors.

## Confidence delta

+2. The build pipeline produced a working test suite that surfaced a real bug, in one story, with no blockers. Convention nits noted but didn't block. Pattern is now repeatable for issue 51 / 56.