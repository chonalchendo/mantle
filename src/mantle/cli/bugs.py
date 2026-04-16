"""CLI wrappers for bug capture operations."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import bugs

console = Console()


def run_save_bug(
    *,
    summary: str,
    severity: str,
    description: str,
    reproduction: str,
    expected: str,
    actual: str,
    related_issue: str | None = None,
    related_files: tuple[str, ...] = (),
    project_dir: Path | None = None,
) -> None:
    """Capture a bug report and write it to .mantle/bugs/.

    Args:
        summary: One-line bug summary.
        severity: Bug severity (blocker, high, medium, low).
        description: What happened (paragraph).
        reproduction: Steps to reproduce.
        expected: Expected behaviour.
        actual: Actual behaviour.
        related_issue: Related issue (e.g. issue-08).
        related_files: Related file paths.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: On duplicate bug or invalid severity.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        note, path = bugs.create_bug(
            project_dir,
            summary=summary,
            severity=severity,
            description=description,
            reproduction=reproduction,
            expected=expected,
            actual=actual,
            related_issue=related_issue,
            related_files=related_files,
        )
    except bugs.BugExistsError:
        console.print(
            "[yellow]Warning:[/yellow] "
            "A bug with this summary already exists today."
        )
        raise SystemExit(1) from None
    except ValueError as exc:
        errors.exit_with_error(
            str(exc),
            hint=errors.UNEXPECTED_BUG_HINT,
        )

    console.print()
    console.print("[green]Bug captured in .mantle/bugs/[/green]")
    console.print(f"  Summary: {note.summary}")
    console.print(f"  Severity: {note.severity}")
    console.print(f"  File: {path.name}")
    console.print(
        "  Next: run [bold]/mantle:plan-issues[/bold]"
        " to surface bugs during planning"
    )


def run_update_bug_status(
    *,
    bug: str,
    status: str,
    fixed_by: str | None = None,
    project_dir: Path | None = None,
) -> None:
    """Update a bug's status.

    Args:
        bug: Bug filename (e.g. 2026-03-03-compilation-fails.md).
        status: New status (open, fixed, wont-fix).
        fixed_by: Issue that fixes this bug (optional).
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: On missing bug or invalid status.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        updated, old_status = bugs.update_bug_status(
            project_dir,
            bug,
            status=status,
            fixed_by=fixed_by,
        )
    except FileNotFoundError:
        errors.exit_with_error(
            f"Bug not found: {bug}",
            hint="List bugs with 'mantle list-bugs'",
        )
    except ValueError as exc:
        errors.exit_with_error(
            str(exc),
            hint=errors.UNEXPECTED_BUG_HINT,
        )

    console.print()
    console.print(f"[green]Bug updated:[/green] {bug}")
    console.print(f"  Status: {old_status} \u2192 {updated.status}")
    if updated.fixed_by:
        console.print(f"  Fixed by: {updated.fixed_by}")
