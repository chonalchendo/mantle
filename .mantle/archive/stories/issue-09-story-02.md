---
issue: 9
title: CLI save-session command and vault template
status: done
failure_log: null
tags:
  - type/story
  - status/done
---

## Implementation

Add the `mantle save-session` CLI command and the vault template for session logs. The CLI command is a thin wrapper around `core/session.save_session()`, following the same pattern as `cli/learning.py`.

### src/mantle/cli/session.py

```python
"""CLI wiring for session log commands."""
```

#### Functions

- `run_save_session(*, content, commands_used=(), project_dir=None) -> None` — Resolve `project_dir` (default `Path.cwd()`). Call `session.save_session()` inside a `warnings.catch_warnings()` block to intercept `SessionTooLongWarning`. Print yellow warning via Rich console if word cap exceeded. Print green confirmation with file path and word count on success.

Follow the same pattern as `cli/learning.py`:

1. Resolve project_dir to `Path.cwd()` if None
2. Call core function in a try/except block
3. Handle warnings with Rich console yellow output
4. Print green confirmation with path

### src/mantle/cli/main.py (modify)

Add `save-session` command following the existing command patterns:

```python
@app.command(name="save-session")
def save_session_command(
    content: Annotated[str, Parameter(name="--content", help="Session log body (markdown)")],
    commands_used: Annotated[tuple[str, ...], Parameter(name="--command", help="Commands used during session")] = (),
    project_dir: Annotated[Path | None, Parameter(name="--project-dir", help="Project directory")] = None,
) -> None:
    """Save a session log to .mantle/sessions/."""
    session_cli.run_save_session(
        content=content,
        commands_used=commands_used,
        project_dir=project_dir,
    )
```

Add import: `from mantle.cli import session as session_cli` (at module level or lazy, following the existing convention in main.py).

### vault-templates/session-log.md

Obsidian-compatible note template for session logs:

```markdown
---
project: {{project}}
author: {{author}}
date: {{date}}
commands_used: []
tags:
  - type/session-log
---

## Summary

_One or two sentences summarising the session._

## What Was Done

- _Key accomplishments_

## Decisions Made

- _Decisions and their rationale_

## What's Next

- _Immediate next steps_

## Open Questions

- _Unresolved questions_
```

### Design decisions

- **Content as a single string, not structured fields.** Claude formats the body with the right sections. The CLI just passes it through. This matches the challenge/learning pattern where the command orchestrates the content.
- **`--command` flag is repeatable.** Pass `--command challenge --command design-product` for multiple commands. Cyclopts handles tuple accumulation.
- **Warning interception, not suppression.** The CLI catches `SessionTooLongWarning` and re-presents it as a Rich-formatted yellow message rather than a raw Python warning.

## Tests

### tests/cli/test_session.py

- **save_session_command**: `mantle save-session --help` outputs help text (subprocess call)
- **save_session_command**: `mantle save-session --content "..." --command "idea"` creates file in `.mantle/sessions/` (subprocess test with `tmp_path`)
