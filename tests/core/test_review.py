"""Tests for mantle.core.review."""

from __future__ import annotations

import pytest

from mantle.core import review, verify

# ── Helpers ──────────────────────────────────────────────────────


def _make_report(
    *,
    results: list[tuple[str, bool, str | None]] | None = None,
) -> verify.VerificationReport:
    """Build a minimal verification report for testing."""
    if results is None:
        results = [
            ("Tests pass", True, None),
            ("Coverage >= 80%", False, "Coverage is 72%"),
        ]
    return verify.build_report(
        issue_number=1,
        title="Feature A",
        results=results,
        strategy_used="Standard",
        is_override=False,
    )


# ── build_checklist ──────────────────────────────────────────────


class TestBuildChecklist:
    def test_build_checklist_from_report(self) -> None:
        """Items match the criteria from the verification report."""
        report = _make_report()
        checklist = review.build_checklist(report)

        assert checklist.issue == 1
        assert checklist.title == "Feature A"
        assert len(checklist.items) == 2
        assert checklist.items[0].criterion == "Tests pass"
        assert checklist.items[1].criterion == "Coverage >= 80%"

    def test_build_checklist_items_start_pending(self) -> None:
        """All items have status='pending' initially."""
        report = _make_report()
        checklist = review.build_checklist(report)

        for item in checklist.items:
            assert item.status == "pending"

    def test_build_checklist_preserves_pass_fail(self) -> None:
        """Pass/fail from verification carries through."""
        report = _make_report()
        checklist = review.build_checklist(report)

        assert checklist.items[0].passed is True
        assert checklist.items[1].passed is False
        assert checklist.items[1].detail == "Coverage is 72%"


# ── apply_feedback ───────────────────────────────────────────────


class TestApplyFeedback:
    def test_apply_feedback_approved(self) -> None:
        """Apply 'approved' to an item, verify status updated."""
        report = _make_report()
        checklist = review.build_checklist(report)

        updated = review.apply_feedback(checklist, [(0, "approved", None)])

        assert updated.items[0].status == "approved"
        assert updated.items[0].comment is None
        # Other items unchanged.
        assert updated.items[1].status == "pending"

    def test_apply_feedback_needs_changes_with_comment(self) -> None:
        """Apply 'needs-changes' with a comment."""
        report = _make_report()
        checklist = review.build_checklist(report)

        updated = review.apply_feedback(
            checklist,
            [(1, "needs-changes", "Coverage too low")],
        )

        assert updated.items[1].status == "needs-changes"
        assert updated.items[1].comment == "Coverage too low"

    def test_apply_feedback_invalid_index(self) -> None:
        """Raises InvalidFeedbackError for out-of-bounds index."""
        report = _make_report()
        checklist = review.build_checklist(report)

        with pytest.raises(review.InvalidFeedbackError):
            review.apply_feedback(checklist, [(5, "approved", None)])

    def test_apply_feedback_invalid_status(self) -> None:
        """Raises InvalidFeedbackError for bad status value."""
        report = _make_report()
        checklist = review.build_checklist(report)

        with pytest.raises(review.InvalidFeedbackError):
            review.apply_feedback(checklist, [(0, "rejected", None)])


# ── Properties ───────────────────────────────────────────────────


class TestChecklistProperties:
    def test_all_approved_true(self) -> None:
        """Checklist with all items approved returns True."""
        report = _make_report()
        checklist = review.build_checklist(report)
        checklist = review.apply_feedback(
            checklist,
            [
                (0, "approved", None),
                (1, "approved", None),
            ],
        )

        assert checklist.all_approved is True

    def test_all_approved_false_when_pending(self) -> None:
        """Returns False when items still pending."""
        report = _make_report()
        checklist = review.build_checklist(report)

        assert checklist.all_approved is False

    def test_has_needs_changes(self) -> None:
        """Returns True when any item is needs-changes."""
        report = _make_report()
        checklist = review.build_checklist(report)
        checklist = review.apply_feedback(
            checklist,
            [(0, "needs-changes", "Fix this")],
        )

        assert checklist.has_needs_changes is True


# ── format_checklist ─────────────────────────────────────────────


class TestFormatChecklist:
    def test_format_checklist(self) -> None:
        """Markdown output contains criteria, marks, and status."""
        report = _make_report()
        checklist = review.build_checklist(report)
        checklist = review.apply_feedback(
            checklist,
            [(0, "approved", None)],
        )

        text = review.format_checklist(checklist)

        assert "Issue 1" in text
        assert "Feature A" in text
        assert "\u2713 Tests pass" in text
        assert "\u2717 Coverage >= 80%" in text
        assert "APPROVED" in text
        assert "PENDING" in text
        assert "Coverage is 72%" in text
