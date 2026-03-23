"""Review — checklist construction, feedback collection."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pydantic

if TYPE_CHECKING:
    from mantle.core import verify


# ── Data model ───────────────────────────────────────────────────


class ReviewItem(pydantic.BaseModel, frozen=True):
    """Single review checklist item.

    Attributes:
        criterion: Description of what was checked.
        passed: Whether the verification criterion passed.
        detail: Optional detail from verification.
        status: Review status for this item.
        comment: Optional reviewer comment.
    """

    criterion: str
    passed: bool
    detail: str | None = None
    status: Literal["pending", "approved", "needs-changes"] = "pending"
    comment: str | None = None


class ReviewChecklist(pydantic.BaseModel, frozen=True):
    """Full review checklist for an issue.

    Attributes:
        issue: Issue number under review.
        title: Issue title.
        items: Tuple of review items.
    """

    issue: int
    title: str
    items: tuple[ReviewItem, ...]

    @property
    def all_approved(self) -> bool:
        """True when every item has status 'approved'."""
        return all(item.status == "approved" for item in self.items)

    @property
    def has_needs_changes(self) -> bool:
        """True when any item has status 'needs-changes'."""
        return any(item.status == "needs-changes" for item in self.items)


# ── Exception ────────────────────────────────────────────────────


class InvalidFeedbackError(Exception):
    """Raised when feedback contains an invalid index or status.

    Attributes:
        message: Description of the validation failure.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# ── Public API ───────────────────────────────────────────────────

_VALID_STATUSES = frozenset({"pending", "approved", "needs-changes"})


def build_checklist(report: verify.VerificationReport) -> ReviewChecklist:
    """Construct a review checklist from a verification report.

    Maps each ``VerificationResult`` to a ``ReviewItem`` with
    ``status="pending"``.

    Args:
        report: The verification report to build from.

    Returns:
        A ReviewChecklist with all items in pending status.
    """
    items = tuple(
        ReviewItem(
            criterion=result.criterion,
            passed=result.passed,
            detail=result.detail,
        )
        for result in report.results
    )
    return ReviewChecklist(
        issue=report.issue,
        title=report.title,
        items=items,
    )


def apply_feedback(
    checklist: ReviewChecklist,
    feedback: list[tuple[int, str, str | None]],
) -> ReviewChecklist:
    """Apply feedback to a checklist, returning a new checklist.

    Takes a list of ``(index, status, comment)`` tuples and returns
    a new checklist with the specified items updated.

    Args:
        checklist: The current review checklist.
        feedback: List of (index, status, comment) tuples.

    Returns:
        A new ReviewChecklist with updated items.

    Raises:
        InvalidFeedbackError: If an index is out of bounds or a
            status value is not valid.
    """
    items = list(checklist.items)

    for index, status, comment in feedback:
        if index < 0 or index >= len(items):
            raise InvalidFeedbackError(
                f"Index {index} out of bounds (0..{len(items) - 1})"
            )
        if status not in _VALID_STATUSES:
            raise InvalidFeedbackError(
                f"Invalid status '{status}'"
                f" (must be one of {sorted(_VALID_STATUSES)})"
            )
        items[index] = items[index].model_copy(
            update={"status": status, "comment": comment},
        )

    return checklist.model_copy(update={"items": tuple(items)})


def format_checklist(checklist: ReviewChecklist) -> str:
    """Render a review checklist as markdown.

    Args:
        checklist: The review checklist to format.

    Returns:
        Markdown string with pass/fail marks and approval status.
    """
    lines = [
        f"# Review Checklist — Issue {checklist.issue}",
        "",
        f"**{checklist.title}**",
        "",
        "## Items",
        "",
    ]
    for item in checklist.items:
        mark = "\u2713" if item.passed else "\u2717"
        status_label = item.status.upper()
        line = f"- {mark} {item.criterion} [{status_label}]"
        if item.detail:
            line += f" — {item.detail}"
        if item.comment:
            line += f"\n  > {item.comment}"
        lines.append(line)

    lines.append("")
    return "\n".join(lines)
