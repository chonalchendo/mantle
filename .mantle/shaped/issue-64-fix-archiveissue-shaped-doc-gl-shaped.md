---
issue: 64
title: Fix archive_issue shaped-doc glob to match slug-less filenames
approaches:
- 'Approach A — Widen the glob pattern: change ''issue-{NN:02d}-*-shaped.md'' to ''issue-{NN:02d}*-shaped.md''
  (drop the required ''-'' between NN and the wildcard). Single-character edit. Matches
  both ''issue-24-shaped.md'' (no slug) and ''issue-24-slug-shaped.md'' in one glob
  call.'
- 'Approach B — Add a second glob for the no-slug case: keep existing pattern and
  add an explicit ''issue-{NN:02d}-shaped.md'' glob. Preserves original specificity
  but adds a second loop iteration and an extra line of code. Slightly more defensive
  but lower signal-to-code ratio.'
chosen_approach: Approach A — Widen the glob pattern
appetite: small batch
open_questions:
- None
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-18'
updated: '2026-04-18'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Shaping: Fix archive_issue shaped-doc glob

### Problem

`core/archive.py:46` globs `issue-{NN:02d}-*-shaped.md`. The `-*-` requires at least one character between the issue number and `-shaped.md`. Files like `issue-24-shaped.md` (no slug) are silently missed during archive — the issue file, stories, and learnings get archived, but the shaped doc is orphaned in `.mantle/shaped/`. Surfaced during batch archive of issues 01-40 and confirmed by inspecting the archive directory, where `issue-24-shaped.md` is present only because it was manually moved.

### Chosen Approach: A — Widen the glob

Change line 46 from:

    shaped_dir.glob(f"issue-{issue:02d}-*-shaped.md")

to:

    shaped_dir.glob(f"issue-{issue:02d}*-shaped.md")

Dropping the inter-`-` makes the wildcard match zero-or-more characters, so both the slug-less and slugged forms match in one call. No branching, no extra variable, no helper — strictly narrower in code than Approach B.

### Tradeoffs

- **Gain**: One-character fix. No new code paths. Existing tests still pass because the slugged case remains covered.
- **Give up**: Nothing material. Pattern is now slightly looser — `issue-64xyz-shaped.md` would also match, but that form is not produced by any code path (shaped filenames are always either `issue-NN-shaped.md` or `issue-NN-<slug>-shaped.md`), so the theoretical looseness has no real surface.

### Rabbit Holes

- None — the fix is surgical. Avoid the temptation to refactor the whole archive module.

### No-Gos

- Do not introduce a regex or a helper function for a one-character glob fix.
- Do not widen the simplifier's scope beyond archive.py + test_archive.py.