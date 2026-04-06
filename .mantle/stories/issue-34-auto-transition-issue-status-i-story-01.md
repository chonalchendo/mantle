---
issue: 34
title: Core + CLI — add implemented status and transition
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a developer, I want the build pipeline to track when implementation is complete so that issue status reflects reality without manual CLI calls.

## Depends On

None — independent (foundation story).

## Approach

Add `implemented` as a target status in `core/issues.py` following the existing `transition_to_*` pattern. Wire a CLI command in `cli/review.py` and `cli/main.py` following the existing `transition-issue-*` pattern. Also make `transition_to_implementing` accept `implementing` as a source (idempotent — no-op if already at target) so the build pipeline can safely call it without checking current status first.

## Implementation

### src/mantle/core/issues.py (modify)

1. Add `"implemented"` to `_ALLOWED_TRANSITIONS`:
   ```python
   "implemented": frozenset({"implementing"}),
   ```

2. Add `transition_to_implemented()` public function following the exact pattern of `transition_to_verified()`:
   ```python
   def transition_to_implemented(project_root: Path, issue_number: int) -> Path:
   ```

3. Add `"implementing"` as an allowed source for itself in `_ALLOWED_TRANSITIONS` to make the call idempotent:
   ```python
   "implementing": frozenset({"planned", "verified", "implementing"}),
   ```

### src/mantle/cli/review.py (modify)

Add `run_transition_to_implemented()` following the exact pattern of `run_transition_to_approved()`:
- Print green confirmation on success
- Print red error and SystemExit(1) on InvalidTransitionError

### src/mantle/cli/main.py (modify)

Add `transition-issue-implemented` command following the exact pattern of `transition-issue-verified`:
```python
@app.command(name="transition-issue-implemented")
def transition_issue_implemented_command(...)
```

## Tests

### tests/core/test_issues.py (modify)

- **test_transition_to_implemented_from_implementing**: implementing issue transitions to implemented, status and tags updated
- **test_transition_to_implemented_invalid_status**: planned issue raises InvalidTransitionError
- **test_transition_to_implementing_idempotent**: implementing issue transitions to implementing (no-op, no error)

### tests/cli/test_review.py (modify)

- **test_transition_to_implemented_success**: calls core function, prints confirmation
- **test_transition_to_implemented_invalid_status**: prints error and exits