"""CLI wrappers for review operations."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rich.console import Console

from mantle.core import issues

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
