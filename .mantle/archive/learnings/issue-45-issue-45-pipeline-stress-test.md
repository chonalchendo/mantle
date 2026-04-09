---
issue: 45
title: 'issue-45: pipeline stress-test surfaced two build.md design collisions'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-09'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Auto-shape picked the right approach without human input.** Approach A (inline archive scan in `next_issue_number`) was correctly chosen over B (new helper) and C (`include_archive` param on `list_issues`). Approach C would have silently broken `count_issues`, which depends on `list_issues` returning active-only paths — a non-obvious constraint that shaping surfaced by reading the code.
- **Single-story fit sonnet cleanly.** 1 story, 1 wave, no worktree, no retries, TDD followed correctly. Tests written first, watched fail, then implementation made them pass. 42 tests green on first run. No blocked stories.
- **Post-implementation review passed cleanly.** The code-reviewer agent found zero issues. Confirms that a tight story spec + a focused refactorer-style change leaves little for review to catch.
- **Verification was evidence-based, not surface-level.** The verifier actually called `next_issue_number` against the live repo state and observed return value 46 — proving the archive scan works end-to-end, not just that tests pass.

## Harder Than Expected

- **`mantle save-learning` auto-archives the issue, breaking build-pipeline ordering.** `implement.md` Step 9 calls `save-learning`, which triggers `archive.archive_issue()` (via `cli/learning.py:73`). This moves the issue, shaped, and story files from active to `.mantle/archive/` BEFORE `build.md` Steps 7 (simplify) and 8 (verify) run. Mid-pipeline workaround was: `git restore` the active files, delete the duplicate archive copies, keep the learning file, re-run `transition-issue-implemented`, then re-archive at the very end. This is a genuine design collision between two commands that were designed in isolation: `implement.md` treats implementation-complete as terminal, `build.md` treats it as one stage of many. Already captured in `.mantle/inbox/2026-04-09-save-learning-auto-archive-bre.md`.
- **`mantle update-skills --issue 45` matched DuckLake to an issue about issue numbering.** Zero semantic relevance. The matcher appears to use slug/word similarity without domain filtering. Build-mode pipeline ignored it in practice (the story-implementer didn't cite it), so it was wasted compute rather than damaging, but it's noise in every build run and undermines trust in the matcher output. Already captured in `.mantle/inbox/2026-04-09-update-skills-auto-detection-i.md`.

## Wrong Assumptions

- **"Single-story trivial issues don't need shaping."** I assumed shaping would be overhead for a 14-line bug fix. It wasn't. The `list_issues` vs `count_issues` constraint was non-obvious from the issue description alone — shaping caught it by reading the surrounding code. Keep shaping mandatory in build mode even for "obvious" fixes.
- **"Build pipeline state management is airtight."** It isn't. The pipeline stitches together commands (`implement.md`, `simplify.md`, `verify.md`) that were each designed as standalone entry points. Each assumes it's the terminal step. `build.md` is the first command to compose them and it exposes the collision.

## Recommendations

- **Fix the save-learning auto-archive collision before the next `build.md` run.** Options (pick one in a follow-up issue):
  - (a) Defer `save-learning` call to AFTER verification in `build.md`, skipping it in `implement.md` Step 9 when running under build mode.
  - (b) Add a `--no-archive` flag to `mantle save-learning` that the build pipeline uses, and make archiving an explicit step triggered by `transition-issue-verified`.
  - (c) Stop auto-archiving in `save-learning` entirely and make archiving an explicit action.
  Option (c) is cleanest — it separates "capturing a learning" from "marking the issue done." The current coupling is a hidden side effect.
- **Add a confidence threshold or relevance filter to `mantle update-skills`.** A cheap fix: have the matcher read the issue body (not just title/slug) and reject skills whose domain tokens (from their `TRIGGER when ...` description) don't overlap with the issue body. Current matcher is slug-similarity only.
- **Keep auto-shape mandatory in `build.md` even for trivial issues.** It pays for itself by surfacing non-obvious constraints. The "3 approaches all small-batch" format is the right shape for simple issues — it forces consideration without ceremony.
- **For future `core/issues.py` changes touching numbering, find_issue_path, or issue_exists**: remember that `list_issues` is deliberately active-only because `count_issues` depends on it. Bypass `list_issues` and glob both directories, do NOT extend `list_issues` with an `include_archive` flag.

## Meta

This retrospective exists only because the previous `/mantle:add-issue` call reused the archived issue-43 number — filing that new issue surfaced the bug we just fixed. The bug was discovered by falling into it during routine use, not by auditing. That is actually a good signal for Mantle's methodology: dogfooding finds real bugs.