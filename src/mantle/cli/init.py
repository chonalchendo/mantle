"""Init command — create .mantle/ in a project repository."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import project

console = Console()


def run_init(project_dir: Path | None = None) -> None:
    """Initialize .mantle/ in the current project repository.

    Args:
        project_dir: Directory to initialize. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    mantle_path = project_dir / project.MANTLE_DIR
    if mantle_path.exists():
        console.print(
            f"[yellow]Warning:[/yellow] {project.MANTLE_DIR}/ already exists. "
            "Nothing to do."
        )
        return

    project_name = project_dir.name
    project.init_project(project_dir, project_name)
    _print_onboarding()


def _print_onboarding() -> None:
    """Print interactive onboarding message after init."""
    console.print()
    console.print("[green]Mantle initialized in .mantle/[/green]")
    console.print()
    console.print("  Run [bold]/mantle:idea[/bold] to log your first idea")
    console.print("  Run [bold]/mantle:help[/bold] to see all commands")
    console.print()
    console.print(
        "  Want cross-project skills? "
        "Run: [bold]mantle init-vault ~/vault[/bold]"
    )
