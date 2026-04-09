---
issue: 20
title: CLI save-bug + update-bug-status commands, init integration
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Add the `mantle save-bug` and `mantle update-bug-status` CLI commands. Create the CLI wrapper module and register both commands in `main.py`. Also add `bugs` to the SUBDIRS created by `mantle init` and extend the tag taxonomy with bug-related tags.

### src/mantle/cli/bugs.py (new file)

```python
"""CLI wrappers for bug capture operations."""
```

#### Functions

- `run_save_bug(*, summary, severity, description, reproduction, expected, actual, related_issue=None, related_files=(), project_dir=None) -> None` — Resolve `project_dir` (default to `Path.cwd()`), call `bugs.create_bug()`, print confirmation with Rich formatting.

Output format matches existing CLI commands:

```
Bug captured in .mantle/bugs/
  Summary: Compilation fails when no idea.md exists
  Severity: medium
  File: 2026-03-03-compilation-fails.md
  Next: run /mantle:plan-issues to surface bugs during planning
```

Error handling: catch `BugExistsError` and print a user-friendly message. Catch `ValueError` (invalid severity) and print valid options.

- `run_update_bug_status(*, bug, status, fixed_by=None, project_dir=None) -> None` — Resolve `project_dir`, call `bugs.update_bug_status()`, print confirmation.

Output format:

```
Bug updated: 2026-03-03-compilation-fails.md
  Status: open → fixed
  Fixed by: issue-21
```

Error handling: catch `FileNotFoundError` and print "Bug not found". Catch `ValueError` (invalid status) and print valid options.

#### Imports

```python
from mantle.core import bugs
```

### src/mantle/cli/main.py (modify)

#### Imports

Add `bugs` to the CLI imports block (alphabetically, before `challenge`):

```python
from mantle.cli import (
    adopt,
    bugs,
    challenge,
    ...
)
```

#### New commands

Register `save-bug`:

```python
@app.command(name="save-bug")
def save_bug_command(
    summary: Annotated[str, Parameter(name="--summary", help="One-line bug summary.")],
    severity: Annotated[str, Parameter(name="--severity", help="Bug severity: blocker, high, medium, low.")],
    description: Annotated[str, Parameter(name="--description", help="What happened (paragraph).")],
    reproduction: Annotated[str, Parameter(name="--reproduction", help="Steps to reproduce.")],
    expected: Annotated[str, Parameter(name="--expected", help="Expected behaviour.")],
    actual: Annotated[str, Parameter(name="--actual", help="Actual behaviour.")],
    related_issue: Annotated[str | None, Parameter(name="--related-issue", help="Related issue (e.g. issue-08).")] = None,
    related_files: Annotated[tuple[str, ...], Parameter(name="--related-file", help="Related file path (repeatable).")] = (),
    path: Annotated[Path | None, Parameter(name="--path", help="Project directory. Defaults to cwd.")] = None,
) -> None:
    """Capture a bug report in .mantle/bugs/."""
    bugs.run_save_bug(
        summary=summary,
        severity=severity,
        description=description,
        reproduction=reproduction,
        expected=expected,
        actual=actual,
        related_issue=related_issue,
        related_files=related_files,
        project_dir=path,
    )
```

Register `update-bug-status`:

```python
@app.command(name="update-bug-status")
def update_bug_status_command(
    bug: Annotated[str, Parameter(name="--bug", help="Bug filename (e.g. 2026-03-03-compilation-fails.md).")],
    status: Annotated[str, Parameter(name="--status", help="New status: open, fixed, wont-fix.")],
    fixed_by: Annotated[str | None, Parameter(name="--fixed-by", help="Issue that fixes this bug (e.g. issue-21).")] = None,
    path: Annotated[Path | None, Parameter(name="--path", help="Project directory. Defaults to cwd.")] = None,
) -> None:
    """Update a bug's status."""
    bugs.run_update_bug_status(
        bug=bug,
        status=status,
        fixed_by=fixed_by,
        project_dir=path,
    )
```

### src/mantle/core/project.py (modify)

#### SUBDIRS

Add `"bugs"` to `SUBDIRS` (alphabetically, before `"challenges"`):

```python
SUBDIRS: tuple[str, ...] = (
    "bugs",
    "challenges",
    "decisions",
    ...
)
```

#### TAGS_BODY

Add bug-related tags to the taxonomy. Under the Type section, add:

```
- `type/bug`
```

Add a new Severity section after the Confidence section:

```markdown
### Severity

- `severity/blocker`
- `severity/high`
- `severity/medium`
- `severity/low`
```

### Design decisions

- **`--related-file` is repeatable.** A bug may involve multiple files. Matches the tuple pattern used by `--slice` in `save-issue`.
- **`--bug` takes a filename, not a path.** The CLI resolves the full path internally from `project_dir + .mantle/bugs/ + filename`. This keeps the command prompt simple — it just passes the filename from the listing.
- **`update-bug-status` is a separate command.** Bug creation and status updates are distinct operations with different contexts — creation happens during `/mantle:bug`, status updates happen when an issue that fixes the bug is completed. Separate commands follow the one-command-one-job principle.
- **SUBDIRS updated, not a migration.** New projects get `.mantle/bugs/` automatically. Existing projects that run `/mantle:bug` before re-init will get a `FileNotFoundError` from `create_bug()` — the command prompt handles this by telling the user to create the directory.

## Tests

### tests/cli/test_bugs.py (new file)

Tests use `tmp_path` with `.mantle/` structure including `bugs/` directory. Mock `state.resolve_git_identity()`.

- **run_save_bug**: creates bug file in `.mantle/bugs/`
- **run_save_bug**: prints confirmation with summary and severity
- **run_save_bug**: defaults project_dir to cwd when None
- **run_save_bug**: handles BugExistsError with user-friendly message
- **run_save_bug**: handles ValueError (invalid severity) with valid options
- **save_bug_command**: registered in app as "save-bug"
- **run_update_bug_status**: updates bug status
- **run_update_bug_status**: prints confirmation with old and new status
- **run_update_bug_status**: handles FileNotFoundError with "Bug not found"
- **run_update_bug_status**: handles ValueError (invalid status) with valid options
- **update_bug_status_command**: registered in app as "update-bug-status"

### tests/core/test_project.py (modify)

- **SUBDIRS**: includes "bugs"
- **init_project**: creates `.mantle/bugs/` directory
