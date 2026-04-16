"""CLI wrappers for verification operations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import issues, verify

console = Console()


def run_save_verification_strategy(
    *,
    strategy: str,
    project_dir: Path | None = None,
) -> None:
    """Save verification strategy, print confirmation.

    Args:
        strategy: Verification strategy text to persist.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    verify.save_strategy(project_dir, strategy)

    console.print()
    console.print("[green]Verification strategy saved to config.md[/green]")
    console.print(f"  Strategy: {strategy}")


def run_introspect_project(
    *,
    project_dir: Path | None = None,
) -> None:
    """Detect test/lint/check commands and print introspection.

    Prints the introspection dict as JSON to stdout (for machine
    consumption) and the generated strategy to stderr (for human
    readability).

    Args:
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    introspection = verify.introspect_project(project_dir)
    strategy = verify.generate_structured_strategy(introspection)

    print(json.dumps(introspection))
    print("=== Detected Verification Strategy ===", file=sys.stderr)
    print(strategy, file=sys.stderr)


def run_transition_to_verified(
    *,
    issue: int,
    project_dir: Path | None = None,
) -> None:
    """Transition issue to verified, print confirmation.

    Args:
        issue: Issue number to transition.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If the transition is not allowed.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        path = issues.transition_to_verified(project_dir, issue)
    except issues.InvalidTransitionError as exc:
        errors.exit_with_error(
            (
                f"Cannot transition to 'verified'"
                f" from '{exc.current_status}' status."
            ),
            hint=(
                f"Run 'mantle verify-issue --issue {issue}' first"
                " to record verification result"
            ),
        )

    console.print()
    console.print(
        f"[green]Issue {issue} transitioned to verified ({path.name})[/green]"
    )
    console.print(
        "  Next: run [bold]/mantle:review[/bold]"
        " for checklist-based human review"
    )
