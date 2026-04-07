"""CLI wrappers for review operations."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rich.console import Console

from mantle.core import issues, review

console = Console()


def _transition(
    issue: int,
    project_dir: Path,
    target: str,
    fn: Callable[[Path, int], Path],
    note: str,
) -> None:
    """Run a transition, print confirmation, or exit on failure.

    Args:
        issue: Issue number to transition.
        project_dir: Resolved project directory.
        target: Target status name (for error messages).
        fn: Core transition function to call.
        note: Follow-up message printed after the success line.

    Raises:
        SystemExit: If the transition is not allowed.
    """
    try:
        path = fn(project_dir, issue)
    except issues.InvalidTransitionError as exc:
        console.print(
            f"[red]Error:[/red] Cannot transition to '{target}'"
            f" from '{exc.current_status}' status."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(
        f"[green]Issue {issue} transitioned to {target} ({path.name})[/green]"
    )
    console.print(f"  {note}")


def run_transition_to_approved(
    *,
    issue: int,
    project_dir: Path | None = None,
) -> None:
    """Transition issue to approved, print confirmation.

    Args:
        issue: Issue number to transition.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If the transition is not allowed.
    """
    _transition(
        issue,
        project_dir or Path.cwd(),
        "approved",
        issues.transition_to_approved,
        "Issue approved — ready for release or deployment.",
    )


def run_transition_to_implementing(
    *,
    issue: int,
    project_dir: Path | None = None,
) -> None:
    """Transition issue to implementing, print confirmation.

    Args:
        issue: Issue number to transition.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If the transition is not allowed.
    """
    _transition(
        issue,
        project_dir or Path.cwd(),
        "implementing",
        issues.transition_to_implementing,
        "Review flagged changes — fix and re-verify.",
    )


def run_transition_to_implemented(
    *,
    issue: int,
    project_dir: Path | None = None,
) -> None:
    """Transition issue to implemented, print confirmation.

    Args:
        issue: Issue number to transition.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If the transition is not allowed.
    """
    _transition(
        issue,
        project_dir or Path.cwd(),
        "implemented",
        issues.transition_to_implemented,
        "Implementation complete — run [bold]/mantle:verify[/bold]"
        " to begin verification.",
    )


def run_save_review_result(
    *,
    issue: int,
    feedback: tuple[str, ...],
    project_dir: Path | None = None,
) -> None:
    """Parse feedback, build checklist, save review result.

    Each feedback value is ``"criterion|status|comment"``
    (pipe-delimited).

    Args:
        issue: Issue number under review.
        feedback: Tuple of pipe-delimited feedback strings.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If issue is not found.
    """
    project_dir = project_dir or Path.cwd()

    issue_path = issues.find_issue_path(project_dir, issue)
    if issue_path is None:
        console.print(
            f"[red]Error:[/red] Issue {issue} not found."
        )
        raise SystemExit(1)

    issue_note, _ = issues.load_issue(issue_path)

    items: list[review.ReviewItem] = []
    for entry in feedback:
        parts = entry.split("|", maxsplit=2)
        criterion = parts[0]
        status = parts[1] if len(parts) > 1 else "approved"
        comment = parts[2] if len(parts) > 2 else None
        items.append(
            review.ReviewItem(
                criterion=criterion,
                passed=status == "approved",
                status=status,
                comment=comment,
            )
        )

    checklist = review.ReviewChecklist(
        issue=issue,
        title=issue_note.title,
        items=tuple(items),
    )

    note, path = review.save_review_result(
        project_dir, checklist,
    )
    console.print()
    console.print(
        f"[green]Review saved to {path.name}[/green]"
    )
    console.print(f"  Status: {note.status}")


def run_load_review_result(
    *,
    issue: int,
    project_dir: Path | None = None,
) -> None:
    """Load and print a review result.

    Args:
        issue: Issue number to load the review for.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If no review exists for the issue.
    """
    project_dir = project_dir or Path.cwd()

    try:
        _, body = review.load_review_result(project_dir, issue)
    except FileNotFoundError:
        console.print(
            f"[red]Error:[/red] No review found"
            f" for issue {issue}."
        )
        raise SystemExit(1) from None

    console.print(body)
