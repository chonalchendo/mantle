---
issue: 62
title: Add a fast-path through /mantle:build for trivial single-file edits
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-17'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 62

**Add a fast-path through /mantle:build for trivial single-file edits**

## Criteria

- ✓ **Shaped doc names the chosen trigger (A, B, C, or a mix) and gives the rationale** [approved] — passed: true
- ✓ **build.md documents the fast-path branch with a clear skip condition, following the same skip when X, otherwise run Y format that the simplify step already uses** [approved] — passed: true
- ✓ **The fast-path branch still runs just check and the verify agent — the Iron Laws about verification evidence remain intact** [approved] — passed: true
- ✓ **A new regression check (test or template assertion) confirms the fast-path cannot skip Step 8 (Verify)** [approved] — passed: true
- ✓ **Issue 60's profile (single-file docs edit, no new tests) would have taken the fast-path if re-run** [approved] — passed: true
- ✓ **just check passes** [approved] — passed: true
