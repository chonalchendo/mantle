"""Save-system-design command — persist the system design document."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import system_design
from mantle.core.state import InvalidTransitionError

console = Console()


def run_save_system_design(
    *,
    content: str,
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Save system design document and print confirmation.

    Args:
        content: Full system design document body.
        overwrite: Replace existing system-design.md if True.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If document exists without overwrite, or if
            state transition is invalid.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        result = system_design.save_system_design(
            project_dir,
            content,
            overwrite=overwrite,
        )
    except system_design.SystemDesignExistsError:
        console.print(
            "[yellow]Warning:[/yellow]"
            " system-design.md already exists. "
            "Use --overwrite to replace."
        )
        raise SystemExit(1) from None
    except InvalidTransitionError:
        console.print(
            "[yellow]Warning:[/yellow] Run /mantle:design-product first."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(
        "[green]System design saved to .mantle/system-design.md[/green]"
    )
    console.print()
    console.print(f"  Author: {result.author}")
    console.print(f"  Date:   {result.created}")
    console.print()
    console.print(
        "  Next: run [bold]/mantle:plan-issues[/bold] to break down the work"
    )


def run_revise_system_design(
    *,
    content: str,
    change_topic: str,
    change_summary: str,
    change_rationale: str,
    project_dir: Path | None = None,
) -> None:
    """Revise system design and print confirmation.

    Args:
        content: Full revised system design document body.
        change_topic: Short slug for the decision log.
        change_summary: What changed.
        change_rationale: Why it changed.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If system-design.md does not exist.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        _, decision_path = system_design.update_system_design(
            project_dir,
            content,
            change_topic=change_topic,
            change_summary=change_summary,
            change_rationale=change_rationale,
        )
    except FileNotFoundError:
        console.print(
            "[yellow]Warning:[/yellow]"
            " system-design.md does not exist."
            " Run /mantle:design-system first."
        )
        raise SystemExit(1) from None

    console.print()
    console.print(
        "[green]System design revised in .mantle/system-design.md[/green]"
    )
    console.print()
    console.print(f"  Change:   {change_topic}")
    console.print(f"  Decision: {decision_path.name}")
    console.print()
    console.print("  Next: review the revision in .mantle/system-design.md")
