---
issue: 51
title: Core errors module — print_error and exit_with_error
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer writing mantle CLI commands, I want a single error-printing utility so that all CLI error paths route to stderr with a consistent [red]Error:[/] prefix and dim recovery hint.

## Depends On

None — foundational.

## Approach

New self-contained module `src/mantle/cli/errors.py` that owns stderr routing, Rich red/dim styling, and the SystemExit convention. Matches existing `rich.console.Console` usage in the CLI layer (every other `cli/*.py` module already builds a `Console()` for stdout); this module is the stderr counterpart. Future call sites import it as `from mantle.cli import errors` and call `errors.exit_with_error(...)` or `errors.print_error(...)`.

## Implementation

### src/mantle/cli/errors.py (new file)

Single responsibility: format and emit CLI errors. No business logic.

- Module-level `_stderr = Console(stderr=True, highlight=False)` — one instance, reused across calls.
- `print_error(message: str, *, hint: str) -> None` — prints `[red]Error:[/] {message}` then `[dim]{hint}[/dim]` to stderr. Returns None (does not exit).
- `exit_with_error(message: str, *, hint: str, code: int = 1) -> NoReturn` — calls `print_error` then `raise SystemExit(code)`. Return-annotated `NoReturn` so type checkers treat subsequent code as unreachable.
- Google-style module docstring and Google-style function docstrings. Type hints required.
- Absolute imports only: `from rich.console import Console`, `from typing import NoReturn`.
- `hint` is keyword-only to force call sites to be explicit about the recovery suggestion.

#### Design decisions

- **stderr via `Console(stderr=True)`**: Rich's own flag, not manual `file=sys.stderr` — keeps the same styling pipeline as stdout `console.print` calls elsewhere.
- **`highlight=False`**: prevents Rich from auto-colouring numbers/paths inside the hint, which would override the dim style.
- **Hint is mandatory, not optional**: every call site must provide a recovery suggestion. The acceptance criterion says *every* error includes one — making the parameter required enforces this at the type-checker level rather than via code review.
- **No exit on `print_error`**: keeps the function composable — a caller with cleanup work between the print and the exit can call `print_error` then exit itself. `exit_with_error` covers the common case.

## Tests

### tests/cli/test_errors.py (new file)

Use `capsys` to capture stdout and stderr independently. No filesystem setup required.

- **test_print_error_writes_to_stderr_only**: `print_error("msg", hint="hint")`; `captured = capsys.readouterr()`; assert stderr contains both `Error:` and the hint; assert stdout is empty.
- **test_print_error_includes_red_prefix_and_dim_hint**: use a `Console(stderr=True, width=80, force_terminal=True, color_system="truecolor")` inside the test — actually, simpler: use `inline_snapshot` to capture the exact stderr string with ANSI codes stripped (`Console` already strips when `force_terminal` is False). Verify the rendered output contains the message and the hint on separate lines.
- **test_exit_with_error_raises_systemexit_with_default_code_1**: `with pytest.raises(SystemExit) as exc: errors.exit_with_error("m", hint="h")`; `assert exc.value.code == 1`.
- **test_exit_with_error_respects_custom_code**: `errors.exit_with_error("m", hint="h", code=2)`; assert `exc.value.code == 2`.
- **test_exit_with_error_prints_before_exit**: combines `pytest.raises(SystemExit)` with `capsys`; assert stderr captured both message and hint before the exit.
- **test_hint_is_keyword_only**: `with pytest.raises(TypeError): errors.print_error("m", "h")` — positional `hint` is rejected.

No mocks. No fixtures beyond pytest's built-in `capsys`.