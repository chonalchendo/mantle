"""Install command — mount commands, agents, and hooks into ~/.claude/."""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from mantle.core.manifest import plan_install, record_install

if TYPE_CHECKING:
    from collections.abc import Iterable

console = Console()


def run_install() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    source_dir = _locate_bundled_claude_dir()
    target_dir = Path.home() / ".claude"

    plan = plan_install(source_dir, target_dir)

    # Copy safe files (new + source_changed)
    _copy_files(source_dir, target_dir, plan.safe_to_write)

    # Prompt for user-modified and conflicting files
    approved = _prompt_overwrites(plan.needs_prompt)
    _copy_files(source_dir, target_dir, approved)
    declined = plan.needs_prompt - approved

    # Handle removed files (leave in place for safety)
    # Users can manually delete files that mantle no longer ships.

    # Record what was installed
    tracked = plan.safe_to_write | approved | plan.unchanged
    record_install(source_dir, target_dir, tracked)

    # Summary
    installed_count = len(plan.safe_to_write) + len(approved)
    _print_summary(installed_count, declined)


def _locate_bundled_claude_dir() -> Path:
    """Locate the bundled claude/ directory inside the package.

    In a wheel install, Hatchling's force-include puts claude/ inside
    the package. In an editable dev install, it stays at the repo root.
    We check both locations.
    """
    # Wheel install: claude/ is inside the package
    ref = resources.files("mantle").joinpath("claude")
    source_dir = Path(str(ref))
    if source_dir.is_dir():
        return source_dir

    # Editable install: claude/ is at the repo root
    # src/mantle/ -> repo root is two levels up from the package
    repo_root = Path(str(resources.files("mantle"))).parent.parent
    source_dir = repo_root / "claude"
    if source_dir.is_dir():
        return source_dir

    console.print(
        "[red]Error:[/red] Bundled claude/ directory not found. "
        "The package may be installed incorrectly."
    )
    raise SystemExit(1)


def _copy_files(
    source_dir: Path,
    target_dir: Path,
    rel_paths: Iterable[str],
) -> None:
    """Copy files from source to target, preserving directory structure."""
    for rel in rel_paths:
        src = source_dir / rel
        dst = target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))


def _prompt_overwrites(rel_paths: frozenset[str]) -> frozenset[str]:
    """Prompt the user for each modified file. Return approved paths."""
    if not rel_paths:
        return frozenset()

    from rich.prompt import Confirm

    approved: set[str] = set()
    for rel in sorted(rel_paths):
        if Confirm.ask(
            f"  [yellow]{rel}[/yellow] has been modified. Overwrite?"
        ):
            approved.add(rel)
    return frozenset(approved)


def _print_summary(installed_count: int, declined: frozenset[str]) -> None:
    """Print a Rich-formatted install summary."""
    console.print()
    console.print(f"[green]Installed[/green] {installed_count} file(s).")
    if declined:
        console.print(
            f"[yellow]Skipped[/yellow] {len(declined)} file(s) (user declined):"
        )
        for rel in sorted(declined):
            console.print(f"  - {rel}")
    console.print()
    console.print(
        "Run [bold]/mantle:help[/bold] in Claude Code "
        "to see available commands."
    )
