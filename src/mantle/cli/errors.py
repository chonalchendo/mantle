"""CLI error-printing utilities.

Provides a single place for formatting and emitting CLI errors to stderr,
with a consistent prefix and optional recovery hint.
"""

from __future__ import annotations

from typing import NoReturn

from rich.console import Console

_stderr = Console(stderr=True, highlight=False)


def print_error(message: str, *, hint: str) -> None:
    """Print a formatted error message and recovery hint to stderr.

    Does not exit. Use :func:`exit_with_error` when the command should
    terminate after printing.

    Args:
        message: The error description shown after the ``Error:`` prefix.
        hint: A recovery suggestion shown below the error message. Keyword-only
            to force call sites to be explicit about the recovery suggestion.
    """
    _stderr.print(f"[red]Error:[/] {message}")
    _stderr.print(f"[dim]{hint}[/dim]")


def exit_with_error(message: str, *, hint: str, code: int = 1) -> NoReturn:
    """Print a formatted error message to stderr then exit.

    Args:
        message: The error description shown after the ``Error:`` prefix.
        hint: A recovery suggestion shown below the error message. Keyword-only
            to force call sites to be explicit about the recovery suggestion.
        code: The exit code passed to :exc:`SystemExit`. Defaults to ``1``.

    Raises:
        SystemExit: Always raised with the given *code*.
    """
    print_error(message, hint=hint)
    raise SystemExit(code)
