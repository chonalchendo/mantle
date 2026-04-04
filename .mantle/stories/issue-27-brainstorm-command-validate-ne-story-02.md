---
issue: 27
title: CLI save-brainstorm command and registration
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer using the `/mantle:brainstorm` slash command, I want a `mantle save-brainstorm` CLI command so that the interactive prompt can persist brainstorm output via a shell call.

## Depends On

Story 1 (imports `core/brainstorm.py`).

## Approach

Follow the pattern of `cli/challenge.py` and `cli/research.py` — a thin `run_save_brainstorm()` function that calls `core.brainstorm.save_brainstorm()`, handles errors, and prints confirmation with Rich. Register in `cli/main.py` as `save-brainstorm` with the same cyclopts parameter style used by all other commands.

## Implementation

### src/mantle/cli/brainstorm.py (new file)

Module docstring: `"""Save-brainstorm command — persist a brainstorm session."""`

```python
from __future__ import annotations

from pathlib import Path

from rich.console import Console

from mantle.core import brainstorm

console = Console()
```

**Public function:**
- `run_save_brainstorm(*, title: str, verdict: str, content: str, project_dir: Path | None = None) -> None`:
  - If `project_dir is None`, set to `Path.cwd()`
  - Try: `note, path = brainstorm.save_brainstorm(project_dir, content, title=title, verdict=verdict)`
  - Catch `ValueError as exc` → `console.print(f"[red]Error:[/red] {exc}")`, `raise SystemExit(1) from None`
  - Print confirmation (same style as `cli/research.py`):
    ```
    Brainstorm saved to {path.name}

      Date:    {note.date}
      Author:  {note.author}
      Title:   {note.title}
      Verdict: {note.verdict}

      Next: run /mantle:add-issue to create the issue
    ```
  - Verdict-aware next step:
    - proceed → "Next: run [bold]/mantle:add-issue[/bold] to create the issue"
    - research → "Next: run [bold]/mantle:research[/bold] to gather evidence"
    - scrap → "Idea scrapped — focus on existing backlog"

### src/mantle/cli/main.py (modify)

**Import addition** — add `brainstorm` to the import block:
```python
from mantle.cli import (
    adopt,
    brainstorm,   # <-- new
    bugs,
    challenge,
    ...
)
```

**Command registration** — add after `save-challenge`, before `save-research`:
```python
@app.command(name="save-brainstorm")
def save_brainstorm_command(
    title: Annotated[
        str,
        Parameter(
            name="--title",
            help="Short title for the brainstormed idea.",
        ),
    ],
    verdict: Annotated[
        str,
        Parameter(
            name="--verdict",
            help="Outcome: proceed, research, or scrap.",
        ),
    ],
    content: Annotated[
        str,
        Parameter(
            name="--content",
            help="Full brainstorm session content.",
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
    """Save a brainstorm session to .mantle/brainstorms/."""
    brainstorm.run_save_brainstorm(
        title=title,
        verdict=verdict,
        content=content,
        project_dir=path,
    )
```

#### Design decisions

- **Thin CLI layer**: No business logic in CLI — just parameter wiring, error handling, and Rich output. All logic lives in `core/brainstorm.py`.
- **Same error handling pattern as cli/research.py**: Catch `ValueError` for invalid verdict, print with Rich, exit 1.
- **No overwrite flag**: Brainstorms are append-only (date-prefixed, auto-incremented). Unlike issues or shaped issues, you never overwrite a previous brainstorm.

## Tests

### tests/cli/test_brainstorm.py (new file)

Fixture: `project(tmp_path)` creates `.mantle/` with `state.md` (status=planning) and `.mantle/brainstorms/` directory. Mock `resolve_git_identity`.

- **test_save_brainstorm_cli_success**: invoke `run_save_brainstorm()` with valid args (title="test idea", verdict="proceed", content="some content"), verify no exception and file exists in `.mantle/brainstorms/`
- **test_save_brainstorm_cli_invalid_verdict**: invoke with verdict="maybe", verify `SystemExit` with code 1 is raised
- **test_save_brainstorm_cli_default_cwd**: invoke with `project_dir=None` while monkeypatching `Path.cwd()` to tmp project, verify file is created in the right location