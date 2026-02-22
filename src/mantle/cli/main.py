"""Mantle CLI entry point."""

from pathlib import Path  # noqa: TC003 — needed at runtime for cyclopts
from typing import Annotated

from cyclopts import App, Parameter

from mantle.cli import init, init_vault, install

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


@app.command(name="install")
def install_command() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    install.run_install()


if __name__ == "__main__":
    app()
