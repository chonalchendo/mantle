---
issue: 11
title: Core issues module — IssueNote, save, load, list, next number
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## Implementation

Create `src/mantle/core/issues.py` with the data model, CRUD operations, auto-increment numbering, and state body update. Also extend `core/state.py` with the `slices` field and `update_slices()` function so that project architectural layers are defined once and reused during planning. Follows the same module pattern as `core/shaping.py` and `core/session.py`.

### src/mantle/core/state.py (modify)

#### Add `slices` field to `ProjectState`

```python
class ProjectState(pydantic.BaseModel, frozen=True):
    ...
    slices: tuple[str, ...] = ()
    ...
```

Empty default means existing `state.md` files without the field parse without error — backward compatible. Slices represent the project's architectural layers as defined during system design (e.g., `ingestion`, `transformation`, `api`, `storage` for a data platform, or `frontend`, `backend`, `database` for a web app). They're project-specific, not hardcoded.

#### New function

- `update_slices(project_dir, slices) -> ProjectState` — Set the project's architectural slices. Follows the same read → update → write pattern as `update_tracking()`. Updates `slices`, `updated`, and `updated_by` fields. Returns the updated state.

```python
def update_slices(
    project_dir: Path,
    slices: tuple[str, ...],
) -> ProjectState:
    path = project_dir / ".mantle" / "state.md"
    note = vault.read_note(path, ProjectState)
    identity = resolve_git_identity()
    updated = note.frontmatter.model_copy(
        update={
            "slices": slices,
            "updated": date.today(),
            "updated_by": identity,
        },
    )
    vault.write_note(path, updated, note.body)
    return updated
```

#### Design decisions

- **On `ProjectState`, not a separate file.** Slices are core project metadata — same level of concern as `skills_required`. Putting them on state.md means they're automatically available to every compiled command and every core function that loads state.
- **Empty default for backward compat.** Existing projects get `slices: ()`. The plan-issues command prompt handles the "no slices defined yet" case by interactively proposing them.
- **`update_slices` mirrors `update_tracking`.** Same read → copy → write pattern. Keeps the state.py API consistent.

### src/mantle/core/issues.py (new file)

```python
"""Issue planning — vertical slice issues with acceptance criteria."""
```

#### Data model

```python
class IssueNote(pydantic.BaseModel, frozen=True):
    title: str
    status: str = "planned"
    slice: tuple[str, ...]
    story_count: int = 0
    verification: str | None = None
    blocked_by: tuple[int, ...] = ()
    tags: tuple[str, ...] = ("type/issue", "status/planned")
```

Fields match the schema used by existing issues in `.mantle/issues/`. The `blocked_by` field stores issue numbers this issue depends on. `story_count` starts at 0 (updated by `plan-stories` later). `verification` is an optional per-issue override string.

#### Exception

```python
class IssueExistsError(Exception):
    """Raised when an issue file already exists at the target path."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Issue already exists at {path}")
```

#### Functions

- `save_issue(project_dir, content, *, title, slice, blocked_by=(), verification=None, overwrite=False) -> tuple[IssueNote, Path]` — Save issue to `.mantle/issues/issue-<NN>.md`. Auto-assigns the next issue number via `next_issue_number()`. Raises `IssueExistsError` if a numbered issue file already exists at that path and `overwrite` is `False`. When `overwrite` is True, allows rewriting an existing issue file (for corrections during the planning session). Updates state.md Current Focus after saving. Transitions state to `PLANNING` if not already there.

  The `overwrite` path requires the caller to supply an explicit issue number. Add an `issue` keyword argument (`int | None = None`): when provided, write to that number; when `None`, use `next_issue_number()`.

- `load_issue(path) -> tuple[IssueNote, str]` — Read an issue file via `vault.read_note()`. Returns `(IssueNote, body)`.

- `list_issues(project_dir) -> list[Path]` — All issue paths in `.mantle/issues/`, sorted by filename (oldest-first). Returns empty list if directory has no matching files.

- `next_issue_number(project_dir) -> int` — Scan `.mantle/issues/` for the highest `issue-NN.md` number and return NN+1. If no issues exist, returns 1. Extracts numbers from filenames using regex `r"issue-(\d+)\.md"`.

- `issue_exists(project_dir, issue) -> bool` — True if `issue-<NN>.md` exists.

- `count_issues(project_dir) -> int` — Number of issue files. Convenience for `len(list_issues(...))`.

#### Internal helpers

- `_issue_path(project_dir, issue) -> Path` — Compute issue file path: `.mantle/issues/issue-{issue:02d}.md`.

- `_update_state_body(project_dir, identity, issue) -> None` — Update state.md Current Focus section after saving an issue. Pattern matches `core/shaping.py`'s `_update_state_body`. Sets focus to: `"Issue {issue} planned — run /mantle:plan-issues for next issue or /mantle:shape-issue to start shaping."`. Also transitions state to PLANNING if currently in `system-design` or `adopted` (the valid predecessors).

#### Imports

```python
from mantle.core import state, vault
```

#### Design decisions

- **Auto-numbering by filename scan.** Rather than storing a counter in state.md, scan existing files. This is idempotent and works correctly even if files are manually deleted or renumbered. Matches how `_resolve_session_path` works in `core/session.py`.
- **Frozen Pydantic model.** Consistent with all other `*Note` models in the codebase (`ShapedIssueNote`, `SessionNote`, `ProjectState`).
- **State transition in save.** The first call to `save_issue` transitions the project from `system-design`/`adopted` to `planning`. Subsequent calls stay in `planning`. This matches the product design: "Project state transitions to planning."
- **Optional issue number parameter.** Normally auto-assigned, but `overwrite=True` requires specifying which issue to overwrite. This lets the command prompt correct a just-approved issue.
- **blocked_by as tuple of ints.** Stores issue numbers, not paths. The command prompt renders these as references. Keeps the data model simple and portable.

## Tests

### tests/core/test_state.py (modify)

Add tests for the new `slices` field and `update_slices()` function alongside existing state tests.

- **ProjectState**: slices defaults to empty tuple
- **ProjectState**: slices accepts tuple of strings
- **update_slices**: sets slices on state.md
- **update_slices**: round-trip preserves slices
- **update_slices**: updates `updated` and `updated_by` fields
- **update_slices**: preserves existing state fields (status, project, etc.)
- **update_slices**: overwrites previous slices value

### tests/core/test_issues.py (new file)

All tests use `tmp_path` with a pre-created `.mantle/issues/` directory and `state.md` at `system-design` or `planning` status. Mock `state.resolve_git_identity()` to return a fixed email.

- **IssueNote**: frozen (cannot assign to attributes)
- **IssueNote**: default status is "planned"
- **IssueNote**: default story_count is 0
- **IssueNote**: default tags are ("type/issue", "status/planned")
- **IssueNote**: blocked_by defaults to empty tuple
- **IssueNote**: verification defaults to None
- **save_issue**: writes file to `.mantle/issues/` directory
- **save_issue**: filename matches `issue-NN.md` pattern with zero-padded number
- **save_issue**: auto-assigns next issue number when issue not specified
- **save_issue**: first issue gets number 01
- **save_issue**: second issue gets number 02 after first exists
- **save_issue**: correct frontmatter fields (title, status, slice, story_count, blocked_by, tags)
- **save_issue**: round-trip with `load_issue` preserves frontmatter
- **save_issue**: round-trip preserves body content
- **save_issue**: raises IssueExistsError when issue exists and overwrite is False
- **save_issue**: overwrites existing issue when overwrite is True and issue number specified
- **save_issue**: transitions state to PLANNING from system-design
- **save_issue**: transitions state to PLANNING from adopted
- **save_issue**: stays in PLANNING when already planning
- **save_issue**: updates state.md Current Focus section
- **load_issue**: reads saved issue correctly
- **load_issue**: raises FileNotFoundError when path doesn't exist
- **list_issues**: returns empty list when no issues
- **list_issues**: returns sorted paths
- **list_issues**: sorts by filename (issue-01 before issue-02)
- **next_issue_number**: returns 1 when no issues exist
- **next_issue_number**: returns N+1 when issues exist
- **next_issue_number**: handles gaps (e.g., issue-01 and issue-03 exist → returns 4)
- **issue_exists**: returns False when no issues
- **issue_exists**: returns True after saving an issue
- **count_issues**: returns 0 when no issues
- **count_issues**: returns correct count after saving
