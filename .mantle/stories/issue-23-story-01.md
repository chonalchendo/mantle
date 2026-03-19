---
issue: 23
title: Core learning module — LearningNote, save, load, list
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Create `src/mantle/core/learning.py` with the data model, CRUD operations, confidence_delta validation, per-issue overwrite support, and state body update. Follows the same module pattern as `core/shaping.py` and `core/challenge.py`.

### `src/mantle/core/learning.py` (new file)

#### Data model

```python
class LearningNote(pydantic.BaseModel, frozen=True):
    issue: int
    title: str
    author: str
    date: date
    confidence_delta: str
    tags: tuple[str, ...] = ("type/learning", "phase/reviewing")
```

Simpler than `ShapedIssueNote` — a learning captures a single reflection per issue with a confidence delta. Default tags match the system design taxonomy.

#### Exception

```python
class LearningExistsError(Exception):
    """Raised when a learning already exists for this issue number."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Learning already exists at {path}")
```

#### Functions

- `save_learning(project_dir, content, *, issue, title, confidence_delta, overwrite=False) -> tuple[LearningNote, Path]` — Save learning to `.mantle/learnings/issue-NN.md`. One file per issue. Validates confidence_delta format before saving. Raises `LearningExistsError` if file exists and `overwrite` is False. Updates state.md Current Focus after saving. Stamps `author` from `state.resolve_git_identity()`.

- `load_learning(path) -> tuple[LearningNote, str]` — Read a learning file via `vault.read_note()`. Returns (frontmatter, body). Raises `FileNotFoundError` if path doesn't exist.

- `list_learnings(project_dir) -> list[Path]` — All learning paths in `.mantle/learnings/`, sorted oldest-first by filename. Returns empty list if directory has no matching files.

- `learning_exists(project_dir, issue) -> bool` — True if `issue-<NN>.md` exists.

#### Internal helpers

- `_validate_confidence_delta(confidence_delta) -> None` — Validates format matches `[+-]\d{1,2}`. Raises `ValueError` with descriptive message on invalid input.

- `_learning_path(project_dir, issue) -> Path` — Compute file path: `.mantle/learnings/issue-{issue:02d}.md`.

- `_update_state_body(project_dir, identity, issue) -> None` — Regex-replace the `## Current Focus` section in state.md with `"Learning captured for issue {issue} — review past learnings before next planning cycle."`. Does not transition state.

#### Imports

```python
from mantle.core import state, vault
```

### Design decisions

- **One file per issue, not append.** Each issue gets its own learning. Matches the one-file-per-issue pattern in `.mantle/issues/` and `.mantle/shaped/`.
- **Confidence delta as string, not int.** The sign is semantically meaningful (`+2` vs `2`). String format preserves the sign explicitly and matches the YAML frontmatter representation.
- **Validation via regex.** `[+-]\d{1,2}` ensures a sign prefix and 1-2 digits. Rejects unsigned values, three-digit values, and non-numeric input.
- **State body update, not state transition.** Retrospective happens within the reviewing phase. It updates Current Focus but doesn't change project status.
- **Frozen Pydantic model.** Consistent with all other `*Note` models in the codebase.

## Tests

### tests/core/test_learning.py (new file)

All tests use `tmp_path` with a pre-created `.mantle/learnings/` directory and `state.md` at REVIEWING status. Mock `state.resolve_git_identity()` to return a fixed email.

- **LearningNote**: frozen (cannot assign to attributes)
- **save_learning**: correct frontmatter fields (issue, title, confidence_delta, date, tags)
- **save_learning**: file at expected path `.mantle/learnings/issue-NN.md`
- **save_learning**: zero-padded issue number in filename
- **save_learning**: round-trip with `load_learning` preserves frontmatter
- **save_learning**: round-trip preserves body content
- **save_learning**: raises `LearningExistsError` when file exists and overwrite is False
- **save_learning**: overwrites replace file when overwrite is True
- **save_learning**: stamps author from git identity
- **save_learning**: default tags are `("type/learning", "phase/reviewing")`
- **save_learning**: updates state.md Current Focus with issue number
- **save_learning**: refreshes state.md `updated` and `updated_by` timestamps
- **save_learning**: does not change state.md status (stays REVIEWING)
- **save_learning**: raises `ValueError` for invalid confidence_delta (no sign, unsigned, three digits)
- **save_learning**: accepts valid positive delta (`+5`)
- **save_learning**: accepts valid negative delta (`-3`)
- **save_learning**: accepts valid two-digit delta (`+10`)
- **load_learning**: reads saved learning correctly
- **load_learning**: raises `FileNotFoundError` for nonexistent path
- **list_learnings**: returns empty list when no learnings
- **list_learnings**: returns sorted paths
- **learning_exists**: returns False before saving
- **learning_exists**: returns True after saving
- **learning_exists**: returns False for different issue number
