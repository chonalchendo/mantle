---
issue: 16
title: Core review module — checklist construction, feedback collection, status transitions
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a developer, I want review logic that builds a checklist from acceptance criteria and verification results and processes my feedback, so that the review command has a solid foundation to present and act on.

## Approach

Follows the exact pattern of `core/verify.py` — frozen Pydantic models for data, pure functions for construction and formatting. Builds on `core/verify.VerificationReport` for input and `core/issues.py` for status transitions. This is story 1 of 2; story 2 adds the Claude Code command and CLI wiring.

## Implementation

### src/mantle/core/review.py (new file)

- `ReviewItem` (Pydantic, frozen): `criterion: str`, `passed: bool`, `detail: str | None`, `status: Literal["pending", "approved", "needs-changes"]`, `comment: str | None`
- `ReviewChecklist` (Pydantic, frozen): `issue: int`, `title: str`, `items: tuple[ReviewItem, ...]`
  - Property `all_approved -> bool`: True when every item has `status == "approved"`
  - Property `has_needs_changes -> bool`: True when any item has `status == "needs-changes"`
- `build_checklist(report: VerificationReport) -> ReviewChecklist`: Constructs a checklist from a verification report, mapping each `VerificationResult` to a `ReviewItem` with `status="pending"`
- `apply_feedback(checklist: ReviewChecklist, feedback: list[tuple[int, str, str | None]]) -> ReviewChecklist`: Takes list of `(index, status, comment)` tuples, returns new checklist with updated items. Validates index bounds and status values.
- `format_checklist(checklist: ReviewChecklist) -> str`: Renders checklist as markdown with pass/fail from verification and approval status
- `InvalidFeedbackError` exception for bad index or status values

### src/mantle/core/issues.py (modify)

- `transition_to_approved(project_root, issue_number) -> Path`: From `verified` to `approved` status. Updates tags like `transition_to_verified`.
- `transition_to_implementing(project_root, issue_number) -> Path`: From `verified` back to `implementing` (needs-changes flow). Reuses existing pattern.
- Add `_APPROVED_FROM = frozenset({"verified"})` and `_IMPLEMENTING_FROM` extended to include `"verified"`

#### Design decisions

- **Frozen Pydantic models**: Matches the established pattern in verify.py. Immutability ensures checklist state is predictable.
- **apply_feedback returns new checklist**: Rather than mutating in place, follows the immutable data pattern used throughout the codebase.
- **Status transitions as separate functions**: Keeps the same pattern as transition_to_verified — one function per transition, explicit allowed-from sets.

## Tests

### tests/core/test_review.py (new file)

- **test_build_checklist_from_report**: Builds checklist from a verification report, items match criteria
- **test_build_checklist_items_start_pending**: All items have status="pending" initially
- **test_build_checklist_preserves_pass_fail**: Pass/fail from verification carries through
- **test_apply_feedback_approved**: Apply "approved" to an item, verify status updated
- **test_apply_feedback_needs_changes_with_comment**: Apply "needs-changes" with comment
- **test_apply_feedback_invalid_index**: Raises InvalidFeedbackError for out-of-bounds index
- **test_apply_feedback_invalid_status**: Raises InvalidFeedbackError for bad status value
- **test_all_approved_true**: Checklist with all items approved returns True
- **test_all_approved_false_when_pending**: Returns False when items still pending
- **test_has_needs_changes**: Returns True when any item is needs-changes
- **test_format_checklist**: Markdown output contains criteria, pass/fail marks, and approval status

### tests/core/test_issues.py (modify — add transition tests)

- **test_transition_to_approved_from_verified**: Verified issue transitions to approved
- **test_transition_to_approved_invalid_status**: Non-verified issue raises InvalidTransitionError
- **test_transition_to_implementing_from_verified**: Verified issue transitions back to implementing
- **test_transition_to_implementing_invalid_status**: Non-verified issue raises error