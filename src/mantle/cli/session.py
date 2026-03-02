"""CLI wiring for session log commands."""

from __future__ import annotations

import warnings
from pathlib import Path

from rich.console import Console

from mantle.core import session

console = Console()


def run_save_session(
    *,
    content: str,
    commands_used: tuple[str, ...] = (),
    project_dir: Path | None = None,
) -> None:
    """Save session log, print confirmation with word count.

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
