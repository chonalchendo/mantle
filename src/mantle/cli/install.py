"""Install command — mount commands, agents, and hooks into ~/.claude/."""

from __future__ import annotations

import json
import shutil
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from mantle.core import manifest

if TYPE_CHECKING:
    from collections.abc import Iterable

console = Console()


def run_install() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    source_dir = _locate_bundled_claude_dir()
    target_dir = Path.home() / ".claude"

    plan = manifest.plan_install(source_dir, target_dir)

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
    manifest.record_install(source_dir, target_dir, tracked)

    # Register SessionStart hook in settings.json
    hook_registered = _register_hooks(target_dir)

    # Summary
    installed_count = len(plan.safe_to_write) + len(approved)
    _print_summary(
        installed_count, declined, hook_registered=hook_registered
    )


def _locate_bundled_claude_dir() -> Path:
    """Locate the bundled claude/ directory inside the package."""
    ref = resources.files("mantle").joinpath("claude")
    source_dir = Path(str(ref))
    if not source_dir.is_dir():
        console.print(
            "[red]Error:[/red] Bundled claude/ directory not found. "
            "The package may be installed incorrectly."
        )
        raise SystemExit(1)
    return source_dir


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


def _print_summary(
    installed_count: int,
    declined: frozenset[str],
    *,
    hook_registered: bool = False,
) -> None:
    """Print a Rich-formatted install summary."""
    console.print()
    console.print(f"[green]Installed[/green] {installed_count} file(s).")
    if hook_registered:
        console.print(
            "[green]SessionStart hook[/green] registered "
            "in ~/.claude/settings.json"
        )
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


_HOOK_COMMAND = "bash $HOME/.claude/hooks/session-start.sh"


def _register_hooks(target_dir: Path) -> bool:
    """Register Mantle's SessionStart hook in settings.json.

    Reads existing settings, merges the hook entry, and writes
    back. Idempotent — skips if already registered.

    Args:
        target_dir: The ``~/.claude/`` directory.

    Returns:
        True if the hook was newly registered, False if already
        present.
    """
    settings_path = target_dir / "settings.json"

    if settings_path.is_file():
        settings = json.loads(
            settings_path.read_text(encoding="utf-8")
        )
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    session_start = hooks.setdefault("SessionStart", [])

    # Check if already registered
    for entry in session_start:
        for hook in entry.get("hooks", []):
            if "session-start.sh" in hook.get("command", ""):
                return False

    session_start.append(
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": _HOOK_COMMAND,
                }
            ],
        }
    )

    settings_path.write_text(
        json.dumps(settings, indent=2) + "\n",
        encoding="utf-8",
    )
    return True
