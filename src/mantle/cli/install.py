"""Install command — mount commands, agents, and hooks into ~/.claude/."""

from __future__ import annotations

import json
import shutil
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from mantle.cli import errors
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

    # Enhance settings with best-practice defaults
    settings_enhanced = _enhance_settings(target_dir)

    # Summary
    installed_count = len(plan.safe_to_write) + len(approved)
    _print_summary(
        installed_count,
        declined,
        hook_registered=hook_registered,
        settings_enhanced=settings_enhanced,
    )


def _locate_bundled_claude_dir() -> Path:
    """Locate the bundled claude/ directory inside the package."""
    ref = resources.files("mantle").joinpath("claude")
    source_dir = Path(str(ref))
    if not source_dir.is_dir():
        errors.exit_with_error(
            "Bundled claude/ directory not found.",
            hint="Reinstall mantle with 'uv tool install mantle'",
        )
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
    settings_enhanced: bool = False,
) -> None:
    """Print a Rich-formatted install summary."""
    console.print()
    console.print(f"[green]Installed[/green] {installed_count} file(s).")
    if hook_registered:
        console.print(
            "[green]Hooks[/green] registered "
            "in ~/.claude/settings.json "
            "(SessionStart, PostToolUse, Stop)"
        )
    if settings_enhanced:
        console.print(
            "[green]Settings enhanced[/green] with schema "
            "and auto-compact defaults"
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


_SETTINGS_SCHEMA = "https://json.schemastore.org/claude-code-settings.json"
_DEFAULT_AUTOCOMPACT = "80"
_DEFAULT_DENY = [
    "Bash(rm -rf *)",
    "Bash(git push --force*)",
    "Bash(git reset --hard*)",
]

_HOOK_COMMAND = "bash $HOME/.claude/hooks/session-start.sh"
_POST_TOOL_USE_COMMAND = "bash $HOME/.claude/hooks/post-tool-use-format.sh"
_STOP_HOOK_COMMAND = "bash $HOME/.claude/hooks/stop.sh"


def _enhance_settings(target_dir: Path) -> bool:
    """Add best-practice defaults to settings.json.

    Sets ``$schema`` for IDE autocompletion,
    ``CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`` for long-session stability,
    and default ``permissions.deny`` rules. Never overwrites existing
    values.

    Args:
        target_dir: The ``~/.claude/`` directory.

    Returns:
        True if any changes were made, False otherwise.
    """
    settings_path = target_dir / "settings.json"

    if settings_path.is_file():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        settings = {}

    changed = False

    # Schema reference for IDE autocompletion
    if "$schema" not in settings:
        settings["$schema"] = _SETTINGS_SCHEMA
        changed = True

    # Auto-compact threshold
    env = settings.setdefault("env", {})
    if "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE" not in env:
        env["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = _DEFAULT_AUTOCOMPACT
        changed = True

    # Default deny permissions
    permissions = settings.setdefault("permissions", {})
    deny = permissions.setdefault("deny", [])
    if not deny:
        permissions["deny"] = list(_DEFAULT_DENY)
        changed = True

    if changed:
        settings_path.write_text(
            json.dumps(settings, indent=2) + "\n",
            encoding="utf-8",
        )

    return changed


def _register_hooks(target_dir: Path) -> bool:
    """Register Mantle's hooks in settings.json.

    Registers SessionStart, PostToolUse (auto-format), and Stop
    (session-log nudge) hooks. Reads existing settings, merges
    entries, and writes back. Idempotent — skips hooks already
    registered.

    Args:
        target_dir: The ``~/.claude/`` directory.

    Returns:
        True if any hook was newly registered, False if all were
        already present.
    """
    settings_path = target_dir / "settings.json"

    if settings_path.is_file():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    changed = False

    # SessionStart hook
    changed |= _ensure_hook(
        hooks, "SessionStart", "session-start.sh", _HOOK_COMMAND
    )

    # PostToolUse hook — auto-format after Write/Edit
    changed |= _ensure_hook(
        hooks,
        "PostToolUse",
        "post-tool-use-format.sh",
        _POST_TOOL_USE_COMMAND,
        matcher="Write|Edit",
    )

    # Stop hook — session-log nudge
    changed |= _ensure_hook(hooks, "Stop", "stop.sh", _STOP_HOOK_COMMAND)

    if changed:
        settings_path.write_text(
            json.dumps(settings, indent=2) + "\n",
            encoding="utf-8",
        )

    return changed


def _ensure_hook(
    hooks: dict,
    event: str,
    script_name: str,
    command: str,
    *,
    matcher: str = "",
) -> bool:
    """Add a hook entry if not already registered.

    Args:
        hooks: The ``hooks`` dict from settings.json.
        event: Hook event name (e.g. ``"SessionStart"``).
        script_name: Substring to match in existing commands for
            idempotency.
        command: The shell command to register.
        matcher: Optional tool matcher (e.g. ``"Write|Edit"``).

    Returns:
        True if the hook was newly added, False if already present.
    """
    entries = hooks.setdefault(event, [])

    for entry in entries:
        for hook in entry.get("hooks", []):
            if script_name in hook.get("command", ""):
                return False

    entries.append(
        {
            "matcher": matcher,
            "hooks": [
                {
                    "type": "command",
                    "command": command,
                }
            ],
        }
    )
    return True
