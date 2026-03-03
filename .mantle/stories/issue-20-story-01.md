---
issue: 20
title: Core bugs module — BugNote model, create, load, list, update status
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Create `src/mantle/core/bugs.py` with the data model, CRUD operations, and status update logic. Bug reports are dated markdown files in `.mantle/bugs/` with structured frontmatter. Follows the same module pattern as `core/issues.py` and `core/idea.py`.

### src/mantle/core/bugs.py (new file)

```python
"""Bug capture — structured bug reports with severity and status tracking."""
```

#### Data model

```python
class BugNote(pydantic.BaseModel, frozen=True):
    date: date
    author: str
    summary: str
    severity: str                          # blocker | high | medium | low
    status: str = "open"                   # open | fixed | wont-fix
    related_issue: str | None = None       # e.g. "issue-08"
    related_files: tuple[str, ...] = ()
    fixed_by: str | None = None            # e.g. "issue-21"
    tags: tuple[str, ...] = ("type/bug", "status/open")
```

`severity` is validated on create — must be one of `blocker`, `high`, `medium`, `low`. `status` is validated on update — must be one of `open`, `fixed`, `wont-fix`. Tags include both type and initial severity/status tags.

#### Constants

```python
VALID_SEVERITIES: frozenset[str] = frozenset({"blocker", "high", "medium", "low"})
VALID_STATUSES: frozenset[str] = frozenset({"open", "fixed", "wont-fix"})
```

#### Exceptions

```python
class BugExistsError(Exception):
    """Raised when a bug file already exists at the target path."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Bug already exists at {path}")
```

#### Functions

- `create_bug(project_dir, *, summary, severity, description, reproduction, expected, actual, related_issue=None, related_files=()) -> tuple[BugNote, Path]` — Save bug to `.mantle/bugs/<date>-<slug>.md`. Slug is derived from summary via `_slugify()`. Validates severity against `VALID_SEVERITIES`, raises `ValueError` on invalid. Stamps `author` with `state.resolve_git_identity()`. Tags include `type/bug`, `severity/<severity>`, `status/open`. Raises `BugExistsError` if file exists. Returns the note and written path.

- `load_bug(path) -> tuple[BugNote, str]` — Read a bug file by absolute path via `vault.read_note()`. Returns `(BugNote, body)` tuple. Composable with `list_bugs()`.

- `list_bugs(project_dir, *, status=None) -> list[Path]` — All bug paths in `.mantle/bugs/`, sorted by filename (oldest-first). When `status` is provided, filter to only bugs matching that status (reads frontmatter). Returns empty list if directory doesn't exist or has no matching files.

- `update_bug_status(project_dir, bug_filename, *, status, fixed_by=None) -> BugNote` — Update a bug's status and optionally set `fixed_by`. Validates `status` against `VALID_STATUSES`. Updates tags to reflect new status (replaces `status/open` with `status/fixed` or `status/wont-fix`, etc.). Raises `FileNotFoundError` if bug doesn't exist. Raises `ValueError` on invalid status. When `status` is `fixed`, `fixed_by` should be provided (but not enforced — it's optional metadata).

#### Internal helpers

- `_bug_path(project_dir, date_str, slug) -> Path` — Compute bug file path: `.mantle/bugs/<date>-<slug>.md`.

- `_slugify(summary) -> str` — Convert summary to filename-safe slug. Lowercase, replace spaces with hyphens, strip non-alphanumeric characters (except hyphens), truncate to 50 chars.

- `_build_bug_body(description, reproduction, expected, actual) -> str` — Build the markdown body from bug content. Structure:
  1. `## Description` — one-paragraph description
  2. `## Reproduction` — steps or context
  3. `## Expected Behaviour` — what should happen
  4. `## Actual Behaviour` — what actually happens

- `_validate_severity(severity) -> None` — Check against `VALID_SEVERITIES`. Raise `ValueError` on invalid.

#### Imports

```python
from mantle.core import state, vault
```

#### Design decisions

- **Dated filenames, not auto-numbered.** Bugs are a log, not a numbered backlog. The date prefix (`2026-03-03-compilation-fails.md`) provides natural chronological ordering and makes filenames meaningful at a glance. This is different from issues which use sequential numbering because issues are referenced by number (`issue-08`) while bugs are referenced by description.
- **Slug from summary.** The filename includes a slug derived from the summary so that multiple bugs on the same day are distinguishable. Truncated to 50 chars to avoid filesystem issues.
- **No state transition.** Bugs are ambient — they don't affect project status. Like session logs, they're a side-channel input to the workflow. The state machine doesn't know about bugs.
- **Filtered listing.** `list_bugs(status="open")` is the primary use case for plan-issues integration. Reading frontmatter for each file is acceptable because bug counts are typically small (tens, not thousands).
- **Status update is a targeted operation.** Unlike `update_idea()` which allows partial field updates, `update_bug_status()` only changes status-related fields. This keeps the API focused — the bug body (description, reproduction) is written once and doesn't change.
- **Tags reflect state.** Tags are updated when status changes so that Obsidian graph queries can filter by `status/open`, `status/fixed`, etc.

## Tests

### tests/core/test_bugs.py (new file)

All tests use `tmp_path` with a pre-created `.mantle/bugs/` directory and `state.md`. Mock `state.resolve_git_identity()` to return a fixed email.

- **BugNote**: frozen (cannot assign to attributes)
- **BugNote**: default status is "open"
- **BugNote**: default tags include "type/bug" and "status/open"
- **BugNote**: related_issue defaults to None
- **BugNote**: related_files defaults to empty tuple
- **BugNote**: fixed_by defaults to None
- **create_bug**: writes file to `.mantle/bugs/` directory
- **create_bug**: filename matches `<date>-<slug>.md` pattern
- **create_bug**: correct frontmatter fields (date, author, summary, severity, status, related_issue, related_files, fixed_by, tags)
- **create_bug**: round-trip with `load_bug` preserves frontmatter
- **create_bug**: round-trip preserves body content (description, reproduction, expected, actual sections)
- **create_bug**: stamps author with git identity
- **create_bug**: tags include severity tag (e.g. `severity/medium`)
- **create_bug**: raises ValueError on invalid severity
- **create_bug**: raises BugExistsError when file already exists
- **create_bug**: slugifies summary (spaces to hyphens, lowercase)
- **create_bug**: truncates slug to 50 characters
- **create_bug**: related_issue and related_files are optional
- **load_bug**: reads saved bug correctly
- **load_bug**: raises FileNotFoundError when path doesn't exist
- **list_bugs**: returns empty list when no bugs
- **list_bugs**: returns sorted paths after multiple creates
- **list_bugs**: filters by status when status parameter provided
- **list_bugs**: returns all bugs when status is None
- **list_bugs**: returns empty list when directory doesn't exist
- **update_bug_status**: changes status from open to fixed
- **update_bug_status**: sets fixed_by field
- **update_bug_status**: updates tags to reflect new status
- **update_bug_status**: raises FileNotFoundError when bug doesn't exist
- **update_bug_status**: raises ValueError on invalid status
- **update_bug_status**: preserves other frontmatter fields (summary, severity, etc.)
- **update_bug_status**: changes status to wont-fix
- **_slugify**: converts spaces to hyphens
- **_slugify**: converts to lowercase
- **_slugify**: strips non-alphanumeric characters
- **_slugify**: truncates to 50 characters
