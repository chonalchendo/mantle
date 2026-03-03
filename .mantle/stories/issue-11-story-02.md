---
issue: 11
title: CLI save-issue command and main.py registration
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Add the `mantle save-issue` and `mantle set-slices` CLI commands. `save-issue` follows the same pattern as `save-shaped-issue`. `set-slices` is a thin wrapper around `state.update_slices()` to let the plan-issues command prompt persist architectural slices. Create the CLI wrapper module and register both commands in `main.py`.

### src/mantle/cli/issues.py (new file)

```python
"""CLI wrapper for issue planning operations."""
```

#### Function

- `run_save_issue(*, title, slice, content, blocked_by=(), verification=None, issue=None, overwrite=False, project_dir=None) -> None` — Resolve `project_dir` (default to `Path.cwd()`), call `issues.save_issue()`, print confirmation with Rich formatting.

Output format matches existing CLI commands:

```
Saved issue-03.md to .mantle/issues/
  Title: Context compilation engine
  Slice: core, tests
  Blocked by: issue-02
  Next: run /mantle:plan-issues for the next issue or /mantle:shape-issue to start shaping
```

When `blocked_by` is non-empty, format as comma-separated `issue-NN` references. When empty, omit the "Blocked by" line.

#### Error handling

Catch `IssueExistsError` and print a user-friendly message suggesting `--overwrite`. Catch `InvalidTransitionError` and print the current status with guidance on what command to run next.

- `run_set_slices(*, slices, project_dir=None) -> None` — Resolve `project_dir`, call `state.update_slices()`, print confirmation listing the saved slices.

Output format:

```
Project slices defined (4):
  ingestion, transformation, api, storage
```

#### Imports

```python
from mantle.core import issues, state
```

### src/mantle/cli/main.py (modify)

#### Imports

Add `issues` to the CLI imports:

```python
from mantle.cli import (
    ...
    issues,
    ...
)
```

#### New command

Register `save-issue` command following the pattern of `save-shaped-issue`:

```python
@app.command(name="save-issue")
def save_issue_command(
    title: Annotated[str, Parameter(name="--title", help="Issue title.")],
    slice: Annotated[tuple[str, ...], Parameter(name="--slice", help="Layer touched (repeatable).")],
    content: Annotated[str, Parameter(name="--content", help="Full issue body (markdown).")],
    blocked_by: Annotated[tuple[int, ...], Parameter(name="--blocked-by", help="Blocking issue number (repeatable).")] = (),
    verification: Annotated[str | None, Parameter(name="--verification", help="Per-issue verification override.")] = None,
    issue: Annotated[int | None, Parameter(name="--issue", help="Explicit issue number (for overwrites).")] = None,
    overwrite: Annotated[bool, Parameter(name="--overwrite", help="Replace existing issue.")] = False,
    path: Annotated[Path | None, Parameter(name="--path", help="Project directory. Defaults to cwd.")] = None,
) -> None:
    """Save a planned issue to .mantle/issues/."""
    issues.run_save_issue(
        title=title,
        slice=slice,
        content=content,
        blocked_by=blocked_by,
        verification=verification,
        issue=issue,
        overwrite=overwrite,
        project_dir=path,
    )
```

Also register `set-slices`:

```python
@app.command(name="set-slices")
def set_slices_command(
    slices: Annotated[tuple[str, ...], Parameter(name="--slice", help="Architectural layer (repeatable).")],
    path: Annotated[Path | None, Parameter(name="--path", help="Project directory. Defaults to cwd.")] = None,
) -> None:
    """Define project architectural slices in state.md."""
    issues.run_set_slices(slices=slices, project_dir=path)
```

#### Design decisions

- **`--slice` is repeatable.** Issues can touch multiple layers (e.g., `--slice core --slice tests --slice claude-code`). Matches the tuple pattern used by `--approaches` in `save-shaped-issue`.
- **`--blocked-by` takes int, not string.** Issue numbers are integers. The CLI accepts `--blocked-by 2 --blocked-by 5`. The command prompt formats these from its knowledge of the issue graph.
- **`--issue` is optional.** When omitted, auto-assigns the next number. When provided (with `--overwrite`), targets a specific issue for correction.
- **`--verification` is optional.** Most issues use the project default. Only issues needing custom verification steps pass this flag.
- **`set-slices` is a separate command.** Slices are defined once during planning setup, not on every issue save. Keeping it separate follows the one-command-one-job principle.

## Tests

### tests/cli/test_issues.py (new file)

Tests use `tmp_path` with `.mantle/` structure. Mock `state.resolve_git_identity()`.

- **run_save_issue**: creates issue file in `.mantle/issues/`
- **run_save_issue**: prints confirmation with title and slice
- **run_save_issue**: prints "Blocked by" line when blocked_by is non-empty
- **run_save_issue**: omits "Blocked by" line when blocked_by is empty
- **run_save_issue**: defaults project_dir to cwd when None
- **run_save_issue**: handles IssueExistsError with user-friendly message
- **run_save_issue**: handles InvalidTransitionError with guidance
- **save_issue_command**: registered in app as "save-issue"
- **run_set_slices**: updates slices in state.md
- **run_set_slices**: prints confirmation with slice count and names
- **run_set_slices**: defaults project_dir to cwd when None
- **set_slices_command**: registered in app as "set-slices"
