---
issue: 37
title: Backward status transitions — minimal change, full pipeline
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-07'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- Shaping correctly identified this as a single frozenset expansion — no new modules, functions, or CLI changes needed.
- Existing test infrastructure (_write_issue_direct helper, TestTransitionToImplementing class) made adding coverage trivial.
- Full build pipeline ran cleanly end-to-end on a 1-line production change.

## Harder Than Expected

- Nothing — this was the smallest possible issue. Pipeline overhead exceeded implementation effort.

## Wrong Assumptions

- None. The status machine design was exactly as expected.

## Recommendations

- **Expanding _ALLOWED_TRANSITIONS is the pattern** for future status machine changes — add the source status to the target's frozenset, add one test following the existing pattern.
- **Full pipeline is appropriate even for trivial issues** — consistency matters more than speed optimisation at this stage.
- If more backward transitions are needed (e.g., approved → implementing), the same one-line pattern applies.