"""Init-vault command — create personal vault and link it."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import project

console = Console()


def run_init_vault(vault_path: Path) -> None:
    """Create personal vault structure and link to project config.

    Args:
        vault_path: Path for the personal vault directory.
    """
    project_root = Path.cwd()

    try:
        project.init_vault(vault_path, project_root)
    except FileExistsError:
        resolved = vault_path.expanduser().resolve()
        console.print(
            f"[yellow]Warning:[/yellow] Personal vault already "
            f"exists at {resolved}. Nothing to do."
        )
        return
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] Project not initialized. "
            "Run [bold]mantle init[/bold] first."
        )
        raise SystemExit(1) from None

    resolved = vault_path.expanduser().resolve()
    console.print()
    console.print(f"[green]Created personal vault at {resolved}[/green]")
    console.print("  - skills/")
    console.print("  - knowledge/")
    console.print("  - inbox/")
    console.print()
    console.print("Vault path saved to .mantle/config.md")
    console.print(
        "  Tip: Place in iCloud Drive for automatic sync across machines."
    )
