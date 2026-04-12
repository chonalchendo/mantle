---
issue: 55
title: Composite skip heuristic in build.md step 7
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a developer, I want the build pipeline to skip simplification only when both files changed AND lines changed are small so that real refactors still get the quality pass even when they touch few files.

## Depends On

Story 1 — needs the `mantle collect-issue-diff-stats` CLI helper to exist.

## Approach

Pure prompt edit to `claude/commands/mantle/build.md` step 7 (Simplify — conditional). Replace the file-count-only skip check with a composite heuristic that reads files + lines_changed from the new CLI command and skips only when both are small.

## Implementation

### claude/commands/mantle/build.md (modify)

Locate Step 7 "Simplify (conditional)" — specifically the `**Skip condition:**` paragraph starting around line 217 that currently reads:

> **Skip condition:** Run `mantle collect-issue-files --issue {NN}` to count files changed. If **3 or fewer files** were changed across all stories, skip this step — the post-implementation review (in Step 6) already caught quality issues, and simplification overhead isn't justified for small changes. Report:
> > **Simplification:** Skipped (≤3 files changed)

Replace with:

> **Skip condition:** Run `mantle collect-issue-diff-stats --issue {NN}` to read `files`, `lines_added`, `lines_removed`, and `lines_changed` (added+removed). Skip simplification only when **both** `files ≤ 3` **AND** `lines_changed ≤ 50`. Otherwise, run simplification. Report one of:
> > **Simplification:** Skipped (files=N, lines_changed=N — below threshold)
> > **Simplification:** Running (files=N, lines_changed=N — above threshold)

Also remove the parenthetical clause "the post-implementation review (in Step 6) already caught quality issues, and" — after story 2 the per-story review no longer exists, so the justification is just "simplification overhead isn't justified for very small changes."

The `**If more than 3 files changed**,` sentence below (that introduces the refactorer agent spawn) must be updated to `**If the skip condition is not met**,` so it reflects the composite heuristic.

Thresholds as constants inside the prompt text — `3` and `50` — cited explicitly so they are easy to tune later.

#### Design decisions

- **AND semantics**: both conditions must be small to skip. A single-file change with a 300-line rewrite must still run simplify.
- **Threshold 50 for lines_changed**: a round number small enough that refactors exceed it, large enough that true triviality (typo fix, one-line correction, tiny config tweak) falls below. Cited in the shaped issue's open questions for tuning after first runs.
- **key=value output from story 1**: build.md Bash can grep/cut without JSON parsing.

## Tests

No production-code tests — pure prompt edit.

Manual verification (verify step):
- Grep `claude/commands/mantle/build.md` for `collect-issue-files` — must be absent (replaced by `collect-issue-diff-stats`).
- Grep for `lines_changed ≤ 50` and `files ≤ 3` — both must appear in the skip condition.
- Grep for `≤3 files changed` (the old wording) — must be absent.
- The standalone `/mantle:simplify` command file is NOT modified (AC 4 sanity check).

## Out of scope

- Any change to the simplify checklist content.
- Any change to the `/mantle:simplify` standalone command.
- Any change to implement.md (separate story).
- Any change to CLI (story 1 delivered the helper).