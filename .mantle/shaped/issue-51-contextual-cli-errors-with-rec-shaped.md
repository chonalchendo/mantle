---
issue: 51
title: Contextual CLI errors with recovery suggestions
approaches:
- Pure helper module with print_error/exit_with_error functions
- Custom MantleCLIError exception caught at app root
- Decorator wrapping each command
chosen_approach: Pure helper module with print_error/exit_with_error functions
appetite: small batch
open_questions:
- Should we also migrate core/ ValueError/RuntimeError raises that CLI lets bubble,
  or is CLI-layer-only migration sufficient for v1?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-16'
updated: '2026-04-16'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches

### A — Pure helper module (CHOSEN)

Create `src/mantle/cli/errors.py` with two functions:

```python
def print_error(message: str, *, hint: str) -> None:
    """Print formatted error to stderr — [red]Error:[/] + dim hint."""

def exit_with_error(message: str, *, hint: str, code: int = 1) -> NoReturn:
    """Print and raise SystemExit(code)."""
```

Migrate ~40 existing `console.print("[red]Error:[/red] ...") + raise SystemExit(1)` pairs to call the helper. All output goes to stderr via a module-level `Console(stderr=True)`.

- **Tradeoffs**: Smallest deep module — the interface is the problem statement ("print an error with a recovery hint"), the implementation hides stderr routing, Rich styling, and exit behaviour. Direct replacement of the existing pattern.
- **Rabbit holes**: Over-engineering the recovery-hint catalogue into a centralised registry. We want hints supplied at call sites because they're context-specific.
- **No-gos**: No global exception handler wiring; no new control-flow contract.

### B — Custom exception caught at app root

Define `class MantleCLIError(Exception)` carrying message + hint. Wire a handler at the cyclopts app entry point in `cli/main.py` that catches `MantleCLIError`, formats via the same print helper, and `sys.exit(1)`. Call sites `raise MantleCLIError("...", hint="...")` instead of calling a helper + raising SystemExit.

- **Tradeoffs**: Slightly cleaner — call sites only describe *what* is wrong; formatting + exit are centralised at the app root. Matches "define errors out of existence" at the interface layer.
- **Rabbit holes**: How does it interact with `raise SystemExit(1) from None`? Do we catch `SystemExit` too for consistency? What about cyclopts' own error handling (e.g. validator failures)? Testing the handler needs `result_action="return_value"` (per the cyclopts skill) which is new ground for this codebase.
- **No-gos**: Larger blast radius — touches `main.py`'s entry wiring plus every call site.

### C — Decorator wrapping each command

`@handle_errors` decorator that wraps every CLI entrypoint and catches a specific exception type. Rejected early — most commands have several distinct error branches inside a single function, so a decorator would still need call sites to raise typed exceptions (degenerates to approach B with extra indirection).

## Comparison

| | A (pure helper) | B (exception + root handler) | C (decorator) |
|---|---|---|---|
| Appetite | small batch | small batch | small batch |
| Key benefit | smallest diff, matches existing pattern | centralised formatting | decorator-per-command |
| Key risk | each call site carries its hint literal | touches app entry wiring | mostly redundant with B |
| Complexity | low | medium | medium |

## Chosen: Approach A

Approach A is the smallest deep module that satisfies every acceptance criterion:

- "shared error formatting utility" → `errors.print_error`/`exit_with_error`.
- "no raw `print` or `sys.exit` for errors" → migration task.
- "stderr with Rich `[red]Error:[/]` prefix and dim recovery suggestion" → implemented inside the helper via `Console(stderr=True)`.
- "test verifies stderr + recovery hint format" → straightforward unit test.

Approach B's win is aesthetic; the existing code pattern is already `console.print(...) + raise SystemExit(...)` — migrating to a helper that keeps the same shape is minimal churn and maximises review-ability of the migration diff. Every call site already has the message at the raise point; wrapping it in an exception and unwrapping at the root would add one hop without changing the reader's mental model.

**Appetite**: small batch (2 sessions).

## Strategy

### New module — `src/mantle/cli/errors.py`

```python
"""Formatted CLI errors with recovery suggestions — stderr only."""
from typing import NoReturn
from rich.console import Console

_stderr = Console(stderr=True, highlight=False)

def print_error(message: str, *, hint: str) -> None:
    """Print [red]Error:[/] + dim hint to stderr."""
    _stderr.print(f"[red]Error:[/] {message}")
    _stderr.print(f"[dim]{hint}[/dim]")

def exit_with_error(message: str, *, hint: str, code: int = 1) -> NoReturn:
    """Print error and exit with `code` (default 1)."""
    print_error(message, hint=hint)
    raise SystemExit(code)
```

### Migration across `src/mantle/cli/`

Each existing pattern:

```python
console.print(f"[red]Error:[/red] <message>")
raise SystemExit(1)
```

becomes:

```python
from mantle.cli import errors
errors.exit_with_error("<message>", hint="<actionable next step>")
```

Per-site hints (examples from the code I surveyed):

| Site | Message | Hint |
|------|---------|------|
| `cli/compile.py:48` | no .mantle/ directory found | Run `mantle init` to create a project |
| `cli/init_vault.py:33` | project not initialized | Run `mantle init` first |
| `cli/skills.py:69` | personal vault not configured | Set `vault_path` in `~/.mantle/config.yaml` |
| `cli/stories.py:102` | story N for issue M not found | Check the story ID with `mantle list-stories --issue M` |
| `cli/verify.py:82` | cannot transition to 'verified' | Run `mantle verify-issue --issue N` first |
| `cli/review.py:162` | issue N not found | Check the issue number with `mantle list-issues` |
| `cli/review.py:216` | no review found for issue N | Run `mantle review-issue --issue N` first |
| `cli/storage.py:30` | invalid storage mode | Use `local`, `remote`, or `both` |
| `cli/install.py:65` | bundled claude/ not found | Reinstall mantle with `uv tool install mantle` |
| `cli/adopt.py:71` | project at wrong phase | Back up `.mantle/` and re-run `mantle init` if you want to restart |
| generic `Exception as exc` catches | {exc} | File a bug at https://github.com/chonalchendo/mantle/issues |

### Test

New `tests/cli/test_errors.py`:

- `test_print_error_writes_to_stderr_not_stdout` — capture both streams via `capsys`, assert stderr contains the red prefix + hint; stdout empty.
- `test_exit_with_error_raises_systemexit_with_code` — `pytest.raises(SystemExit) as exc`; `exc.value.code == 1`.
- `test_exit_with_error_includes_hint_on_separate_line` — inline snapshot of stderr content for deterministic Rich width.

## Fits architecture by

- Stays inside `cli/` — `core/` never needs to format errors for the terminal.
- Uses the existing Rich `Console` pattern; no new dependency.
- Matches cli-design-best-practices: errors → stderr, exit codes correct (1 for error), actionable "do this next" hints.
- Pulls complexity downward — stderr routing and style are hidden inside the helper; call sites shrink.

## Does not

- Does not wire a global exception handler at the cyclopts entry point (that is approach B, intentionally rejected).
- Does not migrate `core/` layer exceptions — they bubble to the CLI layer where handlers already call `exit_with_error`.
- Does not introduce a recovery-hint catalogue / enum / registry. Hints are literal strings at call sites because they are context-specific.
- Does not change exit codes beyond the existing convention (all existing sites already use `1`).
- Does not change `print(file=sys.stderr)` informational lines in `main.py` (e.g., "Updated skills_required" — those are status messages, not errors).
