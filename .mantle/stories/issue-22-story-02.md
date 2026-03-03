---
issue: 22
title: CLI save-shaped-issue command and main.py registration
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Add the `mantle save-shaped-issue` CLI command. Follows the same pattern as `save-skill` and `save-session`. Create the CLI wrapper module and register the command in `main.py`.

### `src/mantle/cli/shaping.py` (new file)

#### Function

- `run_save_shaped_issue(*, issue, title, approaches, chosen_approach, appetite, content, open_questions=(), overwrite=False, project_dir=None) -> None` — Resolve `project_dir` (default to `Path.cwd()`), call `shaping.save_shaped_issue()`, print confirmation with Rich formatting.

Output format matches existing CLI commands:

```
Shaped issue saved to issue-22-shaped.md

  Issue:    22
  Title:    Shape issue
  Approach: Approach A
  Appetite: medium batch
  Author:   user@example.com

  Next: run /mantle:plan-stories to decompose into stories
```

#### Error handling

Catch `ShapedIssueExistsError` and print a user-friendly message suggesting `--overwrite`. Exit with code 1.

#### Imports

```python
from mantle.core import shaping
```

### `src/mantle/cli/main.py` (modify)

#### Imports

Add `shaping` to the CLI imports:

```python
from mantle.cli import (
    ...
    shaping,
    ...
)
```

#### New command

Register `save-shaped-issue` command:

```python
@app.command(name="save-shaped-issue")
def save_shaped_issue_command(
    issue: Annotated[int, Parameter(name="--issue", help="Issue number being shaped.")],
    title: Annotated[str, Parameter(name="--title", help="Short title for the shaped issue.")],
    approaches: Annotated[tuple[str, ...], Parameter(name="--approaches", help="Approach name (repeatable).")],
    chosen_approach: Annotated[str, Parameter(name="--chosen-approach", help="Selected approach name.")],
    appetite: Annotated[str, Parameter(name="--appetite", help="Time/effort budget.")],
    content: Annotated[str, Parameter(name="--content", help="Full shaping write-up body.")],
    open_questions: Annotated[tuple[str, ...], Parameter(name="--open-questions", help="Unresolved question (repeatable).")] = (),
    overwrite: Annotated[bool, Parameter(name="--overwrite", help="Replace existing shaped issue.")] = False,
    path: Annotated[Path | None, Parameter(name="--path", help="Project directory.")] = None,
) -> None:
    """Save a shaped issue to .mantle/shaped/."""
    shaping.run_save_shaped_issue(
        issue=issue,
        title=title,
        approaches=approaches,
        chosen_approach=chosen_approach,
        appetite=appetite,
        content=content,
        open_questions=open_questions,
        overwrite=overwrite,
        project_dir=path,
    )
```

### Design decisions

- **`--approaches` is repeatable.** The command prompt passes each approach as a separate `--approaches` flag. Cyclopts handles tuple parameters natively.
- **`--open-questions` is optional and repeatable.** Many shaping sessions have no unresolved questions. Default to empty tuple.
- **Exit code 1 on exists.** Consistent with other CLI commands (`save-skill`, `save-session`) that exit 1 on conflict errors.
- **No separate `list-shaped-issues` command.** Shaped issues are only read by the command prompts (plan-stories loads the shaped artifact). No CLI consumer needs listing.

## Tests

### tests/cli/test_shaping.py (new file)

Tests use `tmp_path` with `.mantle/` structure. Mock `state.resolve_git_identity()`.

- **run_save_shaped_issue**: creates shaped issue file in `.mantle/shaped/`
- **run_save_shaped_issue**: prints confirmation with issue number, title, approach, appetite
- **run_save_shaped_issue**: defaults project_dir to cwd when None
- **run_save_shaped_issue**: handles ShapedIssueExistsError with user-friendly message and exit code 1
- **save_shaped_issue_command**: registered in app as "save-shaped-issue"
