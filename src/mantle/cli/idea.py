"""Save-idea command — capture a structured idea in .mantle/idea.md."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import idea

console = Console()


def run_save_idea(
    *,
    hypothesis: str,
    target_user: str,
    success_criteria: tuple[str, ...],
    overwrite: bool = False,
    project_dir: Path | None = None,
) -> None:
    """Capture a structured idea and write it to .mantle/idea.md.

    Args:
        hypothesis: Core belief or value proposition.
        target_user: Who this idea is for.
        success_criteria: Measurable outcomes that prove success.
        overwrite: Replace existing idea.md if True.
        project_dir: Project directory. Defaults to cwd.

    Raises:
        SystemExit: If idea.md already exists and overwrite is False.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        result = idea.create_idea(
            project_dir,
            hypothesis=hypothesis,
            target_user=target_user,
            success_criteria=success_criteria,
            overwrite=overwrite,
        )
    except idea.IdeaExistsError:
        console.print(
            "[yellow]Warning:[/yellow] idea.md already exists. "
            "Use --overwrite to replace."
        )
        raise SystemExit(1) from None

    console.print()
    console.print("[green]Idea captured in .mantle/idea.md[/green]")
    console.print()
    console.print(f"  Hypothesis: {result.hypothesis}")
    console.print(
        f"  Criteria:   {len(result.success_criteria)}"
    )
    console.print()
    console.print(
        "  Next: run [bold]/mantle:challenge[/bold] "
        "to stress-test your idea"
    )
