"""CLI wrappers for review operations."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import issues

console = Console()


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
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        path = issues.transition_to_approved(project_dir, issue)
    except issues.InvalidTransitionError as exc:
        console.print(
            f"[red]Error:[/red] Cannot transition to 'approved'"
            f" from '{exc.current_status}' status."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(
        f"[green]Issue {issue} transitioned to approved ({path.name})[/green]"
    )
    console.print("  Issue approved — ready for release or deployment.")


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
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        path = issues.transition_to_implementing(project_dir, issue)
    except issues.InvalidTransitionError as exc:
        console.print(
            f"[red]Error:[/red] Cannot transition to 'implementing'"
            f" from '{exc.current_status}' status."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(
        f"[green]Issue {issue} transitioned to implementing"
        f" ({path.name})[/green]"
    )
    console.print("  Review flagged changes — fix and re-verify.")


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
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        path = issues.transition_to_implemented(project_dir, issue)
    except issues.InvalidTransitionError as exc:
        console.print(
            f"[red]Error:[/red] Cannot transition to 'implemented'"
            f" from '{exc.current_status}' status."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(
        f"[green]Issue {issue} transitioned to implemented"
        f" ({path.name})[/green]"
    )
    console.print(
        "  Implementation complete — run [bold]/mantle:verify[/bold]"
        " to begin verification."
    )
