"""Compile command — render vault context into Claude Code commands."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.cli import errors
from mantle.core import compiler

console = Console()


def run_compile(
    *,
    if_stale: bool = False,
    project_dir: Path | None = None,
    target_dir: Path | None = None,
    issue: int | None = None,
) -> None:
    """Compile vault context into Claude Code commands.

    Args:
        if_stale: Only recompile when source files have changed.
        project_dir: Project directory. Defaults to cwd.
        target_dir: Output directory. Defaults to
            ``~/.claude/commands/mantle/``.
        issue: Compile only skills relevant to this issue number.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        if if_stale:
            result = compiler.compile_if_stale(
                project_dir, target_dir=target_dir, issue=issue
            )
            if result is None:
                console.print("Already up to date — no recompilation needed.")
                return
            compiled = result
        else:
            compiled = compiler.compile(
                project_dir, target_dir=target_dir, issue=issue
            )
    except FileNotFoundError:
        errors.exit_with_error(
            "no .mantle/ directory found.",
            hint="Run 'mantle init' to create a project",
        )

    display_target = (
        target_dir or Path.home() / ".claude" / "commands" / "mantle"
    )
    console.print(
        f"Compiled {len(compiled)} template(s) to {display_target}/\n"
    )
    for name in compiled:
        console.print(f"  - {name}")

    console.print(
        "\n  Commands are ready. "
        "Run [bold]/mantle:status[/bold] in Claude Code."
    )
