---
issue: 64
title: Fix archive_issue shaped-doc glob to match slug-less filenames
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-18'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## What went well
- Shaping correctly identified Approach A (widen glob) as strictly narrower than Approach B (second glob call) — the one-character edit beat the extra-branch defense.
- TDD cycle was textbook: new test failed against the old pattern, passed after the one-char fix, existing regression held. 1212-test suite green in 68s.
- Simplify skipped (files=2, lines_changed=23 below the 3/50 threshold) — the threshold is doing its job, not running a refactorer agent over a one-char diff.

## Harder than expected
- Nothing. End-to-end build + review + retrospective cycle for a one-char fix is still ~10 minutes of overhead, which is the realistic lower bound for the ceremony — not a problem with this issue.

## Wrong assumptions
- None. The bug report (inbox 2026-04-09) correctly identified both the location (archive.py:46) and the proposed fix pattern. Implementation matched the report.

## Recommendations
- **Reusable pattern — glob-pattern bugs in Mantle:** whenever an archive/compile/lookup pipeline silently misses files, suspect the glob or regex first. Mantle filename conventions vary (slug vs no-slug, with/without date prefix), so any pattern that hardcodes a separator between NN and the rest is brittle. Audit other globs in core/ with the same NN-followed-by-separator shape: `core/issues.py`, `core/stories.py`, `core/learning.py`, `core/shaping.py`.
- **Fast-path rubric refinement:** the build pipeline's fast-path rejected this issue because AC2 required a new test — correct call. A future refinement could distinguish "new test" (warrants an agent) from "new test as a single assertion in an existing class" (could still be fast-path). Not urgent; agent-path worked fine.
- **Keep retros proportional to the work:** for one-char fixes, a 3-line auto-drafted learning is the right dose. Full four-section guided retros on surgical bugs would be theatre.