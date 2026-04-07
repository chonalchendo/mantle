"""Knowledge commands — save, list, and load distillation notes."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import knowledge

console = Console()


def run_save_distillation(
    *,
    topic: str,
    source_paths: list[str],
    content: str,
    project_dir: Path | None = None,
) -> None:
    """Save a distillation note, print confirmation.

    Args:
        topic: The distillation subject.
        source_paths: Relative paths to source notes.
        content: Distillation body content.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If topic or source_paths are invalid.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    if not topic:
        console.print("[red]Error:[/red] --topic is required")
        raise SystemExit(1)

    try:
        note, path = knowledge.save_distillation(
            project_dir,
            content,
            topic=topic,
            source_paths=tuple(source_paths),
        )
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from None

    console.print()
    console.print(f"[green]Distillation saved to {path.name}[/green]")
    console.print()
    console.print(f"  Topic:        {note.topic}")
    console.print(f"  Source count: {note.source_count}")
    console.print(f"  Date:         {note.date}")
    console.print(f"  Author:       {note.author}")


def run_list_distillations(
    *,
    topic: str | None = None,
    project_dir: Path | None = None,
) -> None:
    """List distillation notes, optionally filtered by topic.

    Args:
        topic: Optional topic filter (case-insensitive substring).
        project_dir: Project directory. Defaults to cwd.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    paths = knowledge.list_distillations(project_dir, topic=topic)

    console.print()
    count = len(paths)
    console.print(f"{count} distillation(s)")
    if topic is not None:
        console.print(f"  filtered by: {topic}")
    console.print()

    for path in paths:
        note, _ = knowledge.load_distillation(path)
        console.print(f"  {path.name}  —  {note.topic}")


def run_load_distillation(
    *,
    path: str,
    project_dir: Path | None = None,
) -> None:
    """Load and print a distillation note.

    Args:
        path: Absolute path to the distillation file.
        project_dir: Unused; kept for interface consistency.

    Raises:
        SystemExit: If the file does not exist.
    """
    try:
        note, body = knowledge.load_distillation(Path(path))
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise SystemExit(1) from None

    console.print()
    console.print(f"  Topic:        {note.topic}")
    console.print(f"  Date:         {note.date}")
    console.print(f"  Author:       {note.author}")
    console.print(f"  Source count: {note.source_count}")
    console.print(f"  Tags:         {', '.join(note.tags)}")
    console.print()
    console.print(body)
