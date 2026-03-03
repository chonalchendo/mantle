---
issue: 22
title: Core shaping module — ShapedIssueNote, save, load, list
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Create `src/mantle/core/shaping.py` with the data model, CRUD operations, per-issue overwrite support, and state body update. Follows the same module pattern as `core/session.py` and `core/challenge.py`.

### `src/mantle/core/shaping.py` (new file)

#### Data model

```python
class ShapedIssueNote(pydantic.BaseModel, frozen=True):
    issue: int
    title: str
    approaches: tuple[str, ...]
    chosen_approach: str
    appetite: str
    open_questions: tuple[str, ...] = ()
    author: str
    created: date
    updated: date
    updated_by: str
    tags: tuple[str, ...] = ("type/shaped", "phase/shaping")
```

Fields capture the full shaping artifact: which approaches were evaluated, which was chosen, the time budget, and any unresolved questions. Default tags match the system design taxonomy.

#### Exception

```python
class ShapedIssueExistsError(Exception):
    """Raised when a shaped issue already exists for this issue number."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Shaped issue already exists at {path}")
```

#### Functions

- `save_shaped_issue(project_dir, content, *, issue, title, approaches, chosen_approach, appetite, open_questions=(), overwrite=False) -> tuple[ShapedIssueNote, Path]` — Save shaped issue to `.mantle/shaped/issue-NN-shaped.md`. One file per issue. Raises `ShapedIssueExistsError` if file exists and `overwrite` is False. When overwriting, preserves original `created` date. Updates state.md Current Focus after saving. Stamps `author` and `updated_by` from `state.resolve_git_identity()`.

- `load_shaped_issue(path) -> tuple[ShapedIssueNote, str]` — Read a shaped issue file via `vault.read_note()`. Returns (frontmatter, body). Raises `FileNotFoundError` if path doesn't exist.

- `list_shaped_issues(project_dir) -> list[Path]` — All shaped issue paths in `.mantle/shaped/`, sorted oldest-first by filename. Returns empty list if directory has no matching files.

- `shaped_issue_exists(project_dir, issue) -> bool` — True if `issue-<NN>-shaped.md` exists.

#### Internal helpers

- `_shaped_issue_path(project_dir, issue) -> Path` — Compute file path: `.mantle/shaped/issue-{issue:02d}-shaped.md`.

- `_update_state_body(project_dir, identity, issue) -> None` — Regex-replace the `## Current Focus` section in state.md with `"Issue {issue} shaped — run /mantle:plan-stories next."`. Does not transition state (stays in PLANNING).

#### Imports

```python
from mantle.core import state, vault
```

### Design decisions

- **One file per issue, not append.** Each issue gets its own shaped artifact. This matches the one-file-per-issue pattern in `.mantle/issues/` and `.mantle/learnings/`. Overwrites replace the whole file (for reshaping after new information).
- **Per-issue overwrite, not auto-increment.** Unlike session logs which auto-increment, shaped issues should be one per issue number. Reshaping replaces the previous artifact. The `overwrite` flag makes this explicit.
- **State body update, not state transition.** Shaping happens within the PLANNING phase. It updates Current Focus to guide the user to the next command but doesn't change the project status.
- **Frozen Pydantic model.** Consistent with all other `*Note` models in the codebase.
- **Preserves original created date on overwrite.** When reshaping, the creation date of the original shaping is preserved. Only `updated` and `updated_by` change.

## Tests

### tests/core/test_shaping.py (new file)

All tests use `tmp_path` with a pre-created `.mantle/shaped/` directory and `state.md` at PLANNING status. Mock `state.resolve_git_identity()` to return a fixed email.

- **ShapedIssueNote**: frozen (cannot assign to attributes)
- **save_shaped_issue**: correct frontmatter fields (issue, title, approaches, chosen_approach, appetite, tags)
- **save_shaped_issue**: file at expected path `.mantle/shaped/issue-NN-shaped.md`
- **save_shaped_issue**: zero-padded issue number in filename
- **save_shaped_issue**: round-trip with `load_shaped_issue` preserves frontmatter
- **save_shaped_issue**: round-trip preserves body content
- **save_shaped_issue**: raises `ShapedIssueExistsError` when file exists and overwrite is False
- **save_shaped_issue**: overwrites replace file when overwrite is True
- **save_shaped_issue**: stamps author from git identity
- **save_shaped_issue**: default tags are `("type/shaped", "phase/shaping")`
- **save_shaped_issue**: updates state.md Current Focus with issue number and next step
- **save_shaped_issue**: refreshes state.md `updated` and `updated_by` timestamps
- **save_shaped_issue**: does not change state.md status (stays PLANNING)
- **load_shaped_issue**: reads saved shaped issue correctly
- **load_shaped_issue**: raises `FileNotFoundError` for nonexistent path
- **list_shaped_issues**: returns empty list when no shaped issues
- **list_shaped_issues**: returns sorted paths
- **shaped_issue_exists**: returns False before saving
- **shaped_issue_exists**: returns True after saving
- **shaped_issue_exists**: returns False for different issue number
