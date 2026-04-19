"""Init-vault command — create personal vault and link it."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import project

console = Console()


def run_init_vault(vault_path: Path) -> None:
    """Create personal vault structure and link to project config.

    Args:
        vault_path: Path for the personal vault directory.
    """
    project_root = Path.cwd()

    try:
        created = project.init_vault(vault_path, project_root)
    except FileNotFoundError:
        errors.exit_with_error(
            "Project not initialized.",
            hint="Run 'mantle init' first",
        )

    resolved = vault_path.expanduser().resolve()

    console.print()
    if created:
        console.print(f"[green]Created personal vault at {resolved}[/green]")
        console.print("  - skills/")
        console.print("  - knowledge/")
        console.print("  - inbox/")
        console.print()
        console.print("Vault path saved to .mantle/config.md")
        console.print(
            "  Tip: Place in iCloud Drive for automatic sync across machines."
        )
    else:
        console.print(f"[green]Linked existing vault at {resolved}[/green]")
        console.print("Vault path saved to .mantle/config.md")
