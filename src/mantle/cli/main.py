"""Mantle CLI entry point."""

from cyclopts import App

from mantle.cli.install import run_install

app = App(name="mantle", help="AI workflow engine with persistent context.")


@app.command
def install() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    run_install()


if __name__ == "__main__":
    app()
