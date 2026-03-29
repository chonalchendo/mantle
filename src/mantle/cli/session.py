"""CLI wiring for session log commands."""

from __future__ import annotations

import subprocess
import warnings
from pathlib import Path

from rich.console import Console

from mantle.core import project, session

console = Console()


def run_save_session(
    *,
    content: str,
    commands_used: tuple[str, ...] = (),
    project_dir: Path | None = None,
) -> None:
    """Save session log, auto-commit .mantle/ changes, print confirmation.

    After saving the session log, stages all .mantle/ changes and creates
    a commit. If ``auto_push`` is enabled in config, pushes to remote.

    Args:
        content: Session log body (markdown).
        commands_used: Mantle commands used during the session.
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        note, path = session.save_session(
            project_dir,
            content,
            commands_used=commands_used,
        )

    session_warnings = [
        x for x in w if issubclass(x.category, session.SessionTooLongWarning)
    ]
    for warning in session_warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning.message}")

    word_count = session.count_words(content)
    console.print()
    console.print(f"[green]Session log saved to {path.name}[/green]")
    console.print()
    console.print(f"  Words:    {word_count}")
    console.print(f"  Author:   {note.author}")
    if note.commands_used:
        console.print(f"  Commands: {', '.join(note.commands_used)}")

    # Auto-commit .mantle/ changes
    command_label = commands_used[0] if commands_used else "session"
    summary = _extract_summary(content)
    _auto_commit(project_dir, command_label, summary)

    # Auto-push if configured
    try:
        config = project.read_config(project_dir)
        if config.get("auto_push"):
            _auto_push(project_dir)
    except FileNotFoundError:
        pass


def _extract_summary(content: str) -> str:
    """Extract the first meaningful line from session log content.

    Looks for the Summary section and returns the first non-empty
    line after it.

    Args:
        content: Session log body (markdown).

    Returns:
        First summary line, or "update artifacts" as fallback.
    """
    lines = content.splitlines()
    in_summary = False
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("## summary"):
            in_summary = True
            continue
        if in_summary and stripped and not stripped.startswith("#"):
            return stripped[:72]
    return "update artifacts"


def _auto_commit(
    project_dir: Path,
    command: str,
    summary: str,
) -> None:
    """Stage .mantle/ changes and commit if there are any.

    Args:
        project_dir: Project directory (git root).
        command: Command name for the commit message.
        summary: Summary line for the commit message.
    """
    mantle_dir = project_dir / ".mantle"
    if not mantle_dir.is_dir():
        return

    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "status", "--porcelain", ".mantle/"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        return

    # Stage and commit
    subprocess.run(
        ["git", "add", ".mantle/"],
        cwd=project_dir,
        capture_output=True,
    )
    message = f"chore(mantle): {command} — {summary}"
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        console.print()
        console.print(f"[green]Auto-committed .mantle/ changes[/green]")
    else:
        console.print()
        console.print(
            f"[yellow]Warning:[/yellow] Auto-commit failed: "
            f"{result.stderr.strip()}"
        )


def _auto_push(project_dir: Path) -> None:
    """Push to remote if auto_push is enabled.

    Args:
        project_dir: Project directory (git root).
    """
    result = subprocess.run(
        ["git", "push"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        console.print(f"[green]Auto-pushed to remote[/green]")
    else:
        console.print(
            f"[yellow]Warning:[/yellow] Auto-push failed: "
            f"{result.stderr.strip()}"
        )
