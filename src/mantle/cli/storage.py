"""CLI wrappers for storage configuration and migration."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import migration, project

console = Console()


def run_storage(
    *,
    mode: str,
    project_dir: Path | None = None,
) -> None:
    """Set the storage mode for the project.

    Args:
        mode: Storage mode — "global" or "local".
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If mode is invalid.
    """
    if mode not in ("global", "local"):
        console.print(
            f"[red]Error:[/red] Invalid storage mode"
            f" '{mode}'. Must be 'global' or 'local'."
        )
        raise SystemExit(1)

    if project_dir is None:
        project_dir = Path.cwd()

    config = project.read_config(project_dir)

    if config.get("storage_mode") == mode:
        console.print(f"Storage mode is already '{mode}'.")
        return

    project.update_config(project_dir, storage_mode=mode)

    console.print(
        f"Storage mode set to {mode}."
        f" Run `mantle migrate-storage` to move"
        f" existing files."
    )


def run_migrate_storage(
    *,
    direction: str,
    project_dir: Path | None = None,
) -> None:
    """Migrate .mantle/ storage between local and global.

    Args:
        direction: Migration direction — "global" or "local".
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If direction is invalid or migration fails.
    """
    if direction not in ("global", "local"):
        console.print(
            f"[red]Error:[/red] Invalid direction"
            f" '{direction}'. Must be 'global' or 'local'."
        )
        raise SystemExit(1)

    if project_dir is None:
        project_dir = Path.cwd()

    try:
        if direction == "global":
            result_path = migration.migrate_to_global(project_dir)
        else:
            result_path = migration.migrate_to_local(project_dir)
    except FileExistsError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from None

    console.print(f"Migrated to {direction} storage: {result_path}")


def run_where(*, project_dir: Path | None = None) -> None:
    """Print the resolved .mantle/ absolute path to stdout.

    Args:
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    resolved = project.resolve_mantle_dir(project_dir).resolve()
    print(resolved)
