"""CLI wrappers for lifecycle hook examples."""

from __future__ import annotations

import sys
from importlib import resources

from rich.console import Console

console = Console()

_EXAMPLES_PACKAGE = "mantle.assets.hook_examples"
_AVAILABLE = ("linear", "jira", "slack")


def run_show_hook_example(*, name: str) -> None:
    """Print a shipped example hook script to stdout.

    Args:
        name: Example name (e.g. "linear", "jira", "slack").

    Raises:
        SystemExit: If the named example does not exist.
    """
    if name not in _AVAILABLE:
        console.print(
            f"[red]No hook example named '{name}'. "
            f"Available: {', '.join(_AVAILABLE)}.[/red]",
            highlight=False,
        )
        sys.exit(1)
    content = (resources.files(_EXAMPLES_PACKAGE) / f"{name}.sh").read_text(
        encoding="utf-8",
    )
    sys.stdout.write(content)
