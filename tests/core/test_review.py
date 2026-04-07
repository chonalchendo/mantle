"""Tests for mantle.core.review."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from mantle.core import review, vault, verify

if TYPE_CHECKING:
    from pathlib import Path

MOCK_EMAIL = "reviewer@example.com"

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


# ── Helpers for persistence tests ───────────────────────────────


def _mock_git_identity() -> str:
    return MOCK_EMAIL


def _make_checklist(
    *,
    issue: int = 1,
    title: str = "Feature A",
    statuses: list[tuple[str, bool, str | None, str, str | None]] | None = None,
) -> review.ReviewChecklist:
    """Build a ReviewChecklist for persistence tests.

    Each entry in *statuses* is
    (criterion, passed, detail, status, comment).
    """
    if statuses is None:
        statuses = [
            ("Tests pass", True, None, "approved", None),
            (
                "Coverage >= 80%",
                False,
                "Coverage is 72%",
                "needs-changes",
                "Raise coverage",
            ),
        ]
    items = tuple(
        review.ReviewItem(
            criterion=criterion,
            passed=passed,
            detail=detail,
            status=status,
            comment=comment,
        )
        for criterion, passed, detail, status, comment in statuses
    )
    return review.ReviewChecklist(
        issue=issue,
        title=title,
        items=items,
    )


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create a minimal .mantle/ directory."""
    (tmp_path / ".mantle").mkdir()
    return tmp_path


# ── save_review_result ──────────────────────────────────────────


class TestSaveReviewResult:
    @patch(
        "mantle.core.review.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_creates_file(
        self,
        _mock: object,
        project: Path,
    ) -> None:
        """save_review_result creates the review file."""
        checklist = _make_checklist()
        _, path = review.save_review_result(project, checklist)

        assert path.exists()
        assert path.name == "issue-01-review.md"

    @patch(
        "mantle.core.review.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_frontmatter(
        self,
        _mock: object,
        project: Path,
    ) -> None:
        """Saved file has correct ReviewResultNote frontmatter."""
        checklist = _make_checklist()
        note, _ = review.save_review_result(project, checklist)

        assert note.issue == 1
        assert note.title == "Feature A"
        assert note.status == "needs-changes"
        assert note.author == MOCK_EMAIL
        assert note.date == date.today()
        assert note.tags == ("type/review", "phase/reviewing")

    @patch(
        "mantle.core.review.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_body_contains_criteria(
        self,
        _mock: object,
        project: Path,
    ) -> None:
        """Body contains each criterion with status and comment."""
        checklist = _make_checklist()
        _, path = review.save_review_result(project, checklist)
        read = vault.read_note(path, review.ReviewResultNote)

        assert "Tests pass" in read.body
        assert "Coverage >= 80%" in read.body
        assert "approved" in read.body
        assert "needs-changes" in read.body
        assert "Raise coverage" in read.body

    @patch(
        "mantle.core.review.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_needs_changes_status(
        self,
        _mock: object,
        project: Path,
    ) -> None:
        """Checklist with needs-changes items => status needs-changes."""
        checklist = _make_checklist()
        note, _ = review.save_review_result(project, checklist)

        assert note.status == "needs-changes"

    @patch(
        "mantle.core.review.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_approved_status(
        self,
        _mock: object,
        project: Path,
    ) -> None:
        """Checklist with all approved items => status approved."""
        checklist = _make_checklist(
            statuses=[
                ("Tests pass", True, None, "approved", None),
                ("Lint clean", True, None, "approved", None),
            ],
        )
        note, _ = review.save_review_result(project, checklist)

        assert note.status == "approved"

    @patch(
        "mantle.core.review.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_overwrites(
        self,
        _mock: object,
        project: Path,
    ) -> None:
        """Saving twice for same issue overwrites the file."""
        checklist_v1 = _make_checklist()
        _, path1 = review.save_review_result(project, checklist_v1)

        checklist_v2 = _make_checklist(
            statuses=[
                ("Tests pass", True, None, "approved", None),
                ("Lint clean", True, None, "approved", None),
            ],
        )
        note2, path2 = review.save_review_result(
            project,
            checklist_v2,
        )

        assert path1 == path2
        assert note2.status == "approved"

    @patch(
        "mantle.core.review.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_creates_directory(
        self,
        _mock: object,
        tmp_path: Path,
    ) -> None:
        """Saves correctly when .mantle/reviews/ doesn't exist."""
        (tmp_path / ".mantle").mkdir()
        checklist = _make_checklist()
        _, path = review.save_review_result(tmp_path, checklist)

        assert path.exists()
        assert path.parent.name == "reviews"


# ── load_review_result ──────────────────────────────────────────


class TestLoadReviewResult:
    @patch(
        "mantle.core.review.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_load_review_result(
        self,
        _mock: object,
        project: Path,
    ) -> None:
        """load_review_result reads back saved review correctly."""
        checklist = _make_checklist()
        saved_note, _ = review.save_review_result(
            project,
            checklist,
        )

        loaded_note, body = review.load_review_result(project, 1)

        assert loaded_note.issue == saved_note.issue
        assert loaded_note.title == saved_note.title
        assert loaded_note.status == saved_note.status
        assert loaded_note.author == saved_note.author
        assert "Tests pass" in body

    def test_not_found(self, project: Path) -> None:
        """Raises FileNotFoundError when no review exists."""
        with pytest.raises(FileNotFoundError):
            review.load_review_result(project, 99)


# ── list_reviews ────────────────────────────────────────────────


class TestListReviews:
    @patch(
        "mantle.core.review.state.resolve_git_identity",
        side_effect=_mock_git_identity,
    )
    def test_list_reviews(
        self,
        _mock: object,
        project: Path,
    ) -> None:
        """list_reviews returns paths sorted oldest-first."""
        review.save_review_result(
            project,
            _make_checklist(issue=3),
        )
        review.save_review_result(
            project,
            _make_checklist(issue=1),
        )
        paths = review.list_reviews(project)

        assert len(paths) == 2
        assert paths[0].name < paths[1].name

    def test_empty(self, tmp_path: Path) -> None:
        """Returns empty list when no reviews directory."""
        assert review.list_reviews(tmp_path) == []
