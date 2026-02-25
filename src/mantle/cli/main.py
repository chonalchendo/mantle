"""Mantle CLI entry point."""

from pathlib import Path  # noqa: TC003 — needed at runtime for cyclopts
from typing import Annotated

from cyclopts import App, Parameter

from mantle.cli import challenge, idea, init, init_vault, install

app = App(name="mantle", help="AI workflow engine with persistent context.")


@app.command(name="init")
def init_command(
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory to initialize. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Initialize .mantle/ in the current project repository."""
    init.run_init(path)


@app.command(name="init-vault")
def init_vault_command(
    path: Annotated[
        Path,
        Parameter(
            name="--path",
            help="Directory for the personal vault (e.g. ~/vault).",
        ),
    ],
) -> None:
    """Create personal vault and link it to this project."""
    init_vault.run_init_vault(path)


@app.command(name="save-idea")
def save_idea_command(
    problem: Annotated[
        str,
        Parameter(
            name="--problem",
            help="The specific pain or friction that exists.",
        ),
    ],
    insight: Annotated[
        str,
        Parameter(
            name="--insight",
            help="What makes a new solution possible.",
        ),
    ],
    target_user: Annotated[
        str,
        Parameter(
            name="--target-user",
            help="Who this idea is for.",
        ),
    ],
    success_criteria: Annotated[
        tuple[str, ...],
        Parameter(
            name="--success-criteria",
            help="Measurable outcome (repeatable).",
        ),
    ],
    overwrite: Annotated[
        bool,
        Parameter(
            name="--overwrite",
            help="Replace existing idea.md.",
        ),
    ] = False,
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Capture a structured idea in .mantle/idea.md."""
    idea.run_save_idea(
        problem=problem,
        insight=insight,
        target_user=target_user,
        success_criteria=success_criteria,
        overwrite=overwrite,
        project_dir=path,
    )


@app.command(name="save-challenge")
def save_challenge_command(
    transcript: Annotated[
        str,
        Parameter(
            name="--transcript",
            help="Full challenge session transcript.",
        ),
    ],
    path: Annotated[
        Path | None,
        Parameter(
            name="--path",
            help="Project directory. Defaults to cwd.",
        ),
    ] = None,
) -> None:
    """Save a challenge session transcript to .mantle/challenges/."""
    challenge.run_save_challenge(
        transcript=transcript,
        project_dir=path,
    )


@app.command(name="install")
def install_command() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    install.run_install()


if __name__ == "__main__":
    app()
