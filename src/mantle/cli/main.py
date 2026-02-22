"""Mantle CLI entry point."""

from cyclopts import App

app = App(name="mantle", help="AI workflow engine with persistent context.")


@app.command
def install() -> None:
    """Mount commands, agents, and hooks into ~/.claude/."""
    raise NotImplementedError("Install command not yet implemented.")


if __name__ == "__main__":
    app()
