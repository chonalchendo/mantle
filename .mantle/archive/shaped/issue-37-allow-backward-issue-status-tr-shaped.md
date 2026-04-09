---
issue: 37
title: Allow backward issue status transitions for review workflow
approaches:
- Add implemented to implementing sources
chosen_approach: Add implemented to implementing sources
appetite: small batch
open_questions:
- none
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-07'
updated: '2026-04-07'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen Approach: Add implemented to implementing sources

Add `"implemented"` to the frozenset of allowed source statuses for the `"implementing"` target in `_ALLOWED_TRANSITIONS`.

### Strategy

Modify `src/mantle/core/issues.py` line ~220:
- Change `"implementing": frozenset({"planned", "verified", "implementing"})` to `"implementing": frozenset({"planned", "verified", "implementing", "implemented"})`

No new modules, no new functions. The existing `_transition_issue()` validation logic and `transition_to_implementing()` public API already handle this — the only change is expanding the allowed source set.

Tests in `tests/core/test_issues.py`:
- Add a test in `TestTransitionToImplementing` that starts from `implemented` status
- Verify other invalid transitions still fail (e.g., `approved → implementing` should still be rejected)

### Fits architecture by

- Change is in `core/issues.py` where the status machine is already defined
- No CLI changes needed — `transition-issue-implementing` command already calls `transition_to_implementing()` which delegates to `_transition_issue()`
- Follows the core-never-imports-cli boundary

### Does not

- Does not open up all backward transitions (only `implemented → implementing`)
- Does not add new CLI commands
- Does not change the transition validation logic or error handling
- Does not add logging or audit trail for backward transitions