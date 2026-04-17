---
issue: 61
title: Reconcile implement.md internal inconsistency on skill-file injection
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-17'
confidence_delta: '+1'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Shaped doc's Investigation section did the work.** Numbered line citations for the contradiction (Step 3 line 106, Step 4 lines 145-147, Step 4/5 lines 180-183) made Direction B an obvious call. AC #1 collapsed into the shaping step itself.
- **Issue-60 precedent set direction cleanly.** "Skills load once at shape" is now consistently applied across `plan-stories.md` and `implement.md` — no second-guessing on which of A/B/C was canonical.
- **Surgical-deletion story spec left zero room for implementer interpretation.** Sonnet story-implementer completed the 4-line diff with no retry. Quoting the exact text to delete in the story eliminates ambiguity entirely.
- **Simplify skip-threshold fired correctly.** files=1, lines_changed=4 — well below the 3/50 cutoff. No wasted agent spawn on nothing-to-simplify.

## Harder Than Expected

- **Nothing, honestly.** Pipeline ran end-to-end without surprise. That itself reinforces the issue-60 observation: `/mantle:build` is heavy for a docs deletion. Issue 62 is already queued to add the fast-path.

## Wrong Assumptions

- **Assumed Iron Law #5 would force 2-4 meaningful skill Reads.** Only `design-review` marginally applied (red flags #13 Hard-to-Describe, #14 Non-Obvious Code). Same meta-template signal/noise problem flagged in issue 60's retro — *skill selection rules designed for code work produce weak matches on template-editing issues*. Second occurrence.

## Recommendations

- **When issue 62 ships the fast-path, route this class of issue there.** Single-file template deletion with no tests should skip story-implementer agent spawn entirely. Issue 61 would have benefitted directly.
- **Add a meta-template carve-out to `shape-issue.md` Step 2.3.** If the issue slice is exclusively `claude-code` and the files touched are `claude/commands/mantle/*.md`, make skill selection advisory rather than mandatory. Reduces Iron-Law-#5 theatre when no vault skill genuinely applies.
- **Keep the "Investigation does the work" pattern** for contradiction/reconciliation issues. Turning what could have been a debate into a mechanical deletion is the payoff — repeat for any future "do these docs/prompts agree with each other?" issue.
- **Issue-60 + Issue-61 together validate the single-owner principle** for skill loading: shape is the step that reads skills; downstream stages consume the shaped doc. Any future edit that re-introduces a "scan skills here too" bullet anywhere in `plan-stories.md`, `implement.md`, or `build.md` is a regression and should be reverted.