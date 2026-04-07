---
issue: 37
title: Allow implemented → implementing transition with tests
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer whose code was flagged in review, I want to transition an issue back to implementing without editing frontmatter manually.

## Depends On

None — independent (single story issue).

## Approach

Expand the `_ALLOWED_TRANSITIONS` dict in `core/issues.py` to include `"implemented"` as an allowed source for the `"implementing"` target. This is a one-line change to the existing status machine. Add tests to verify the new transition works and that other invalid transitions still fail.

## Implementation

### src/mantle/core/issues.py (modify)

Line ~221: Change the `"implementing"` entry in `_ALLOWED_TRANSITIONS` from:
```python
"implementing": frozenset({"planned", "verified", "implementing"}),
```
to:
```python
"implementing": frozenset({"planned", "verified", "implementing", "implemented"}),
```

No other changes needed — `_transition_issue()`, `transition_to_implementing()`, and the CLI command all work as-is because they delegate to this dict.

#### Design decisions

- **Only add implemented → implementing**: The issue explicitly requires that other invalid transitions still fail. We only expand this one frozenset.
- **No new functions or modules**: The existing infrastructure handles everything.

## Tests

### tests/core/test_issues.py (modify)

Add to `TestTransitionToImplementing`:

- **test_transition_to_implementing_from_implemented**: Creates an issue with status `"implemented"`, calls `transition_to_implementing()`, asserts status is `"implementing"` and tags contain `"status/implementing"`. Follows the exact pattern of `test_transition_to_implementing_from_verified`.
- **test_transition_to_implementing_invalid_from_approved_still_fails**: Verify that `approved → implementing` still raises `InvalidTransitionError` (guards against accidentally opening all backward transitions). This test already exists as `test_transition_to_implementing_invalid_status` — verify it still passes.