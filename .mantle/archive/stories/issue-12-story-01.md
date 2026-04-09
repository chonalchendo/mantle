---
issue: 12
title: Core stories module — StoryNote, save, load, list, next number
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## User Story

As a developer, I want stories saved to `.mantle/stories/` with structured YAML frontmatter so that the implementation orchestrator can iterate over them, compile context per story, and track which stories are completed, in-progress, or blocked.

## Approach

Create `core/stories.py` following the same module pattern as `core/issues.py` and `core/shaping.py` — a frozen Pydantic model for frontmatter, CRUD functions using `vault.read_note`/`write_note`, and auto-increment numbering scoped per issue. This is story 1 of 3: it builds the data layer that the CLI (story 2) and command prompt (story 3) depend on.

## Implementation

Create `src/mantle/core/stories.py` with the data model, CRUD operations, auto-increment numbering per issue, and issue `story_count` update. Follows the same module pattern as `core/issues.py` and `core/shaping.py`.

### src/mantle/core/stories.py (new file)

```python
"""Story planning — implementable stories with test specifications."""
```

#### Data model

```python
class StoryNote(pydantic.BaseModel, frozen=True):
    issue: int
    title: str
    status: str = "planned"
    failure_log: str | None = None
    tags: tuple[str, ...] = ("type/story", "status/planned")
```

Fields match the schema used by existing stories in `.mantle/stories/`. The `failure_log` field starts as `None` and is populated by the orchestrator (issue 13) when a story gets blocked during implementation. Status values: `planned`, `in-progress`, `completed`, `blocked`.

#### Exception

```python
class StoryExistsError(Exception):
    """Raised when a story file already exists at the target path."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"Story already exists at {path}")
```

#### Functions

- `save_story(project_dir, content, *, issue, title, overwrite=False, story=None) -> tuple[StoryNote, Path]` — Save story to `.mantle/stories/issue-<NN>-story-<NN>.md`. Auto-assigns the next story number for that issue via `next_story_number()` unless `story` is provided. Raises `StoryExistsError` if file exists and `overwrite` is `False`. After saving, updates the parent issue's `story_count` field via `_update_issue_story_count()`. Updates state.md Current Focus after saving.

  The `story` keyword argument (`int | None = None`): when provided, write to that number (for overwrites); when `None`, use `next_story_number()`.

- `load_story(path) -> tuple[StoryNote, str]` — Read a story file via `vault.read_note()`. Returns `(StoryNote, body)`.

- `list_stories(project_dir, *, issue) -> list[Path]` — All story paths for a given issue, sorted by filename (oldest-first). Matches files with pattern `issue-<NN>-story-*.md` where NN is zero-padded. Returns empty list if no matching files exist.

- `next_story_number(project_dir, *, issue) -> int` — Scan `.mantle/stories/` for the highest story number for the given issue and return N+1. If no stories exist for that issue, returns 1. Extracts numbers from filenames using regex `r"issue-\d+-story-(\d+)\.md"`.

- `story_exists(project_dir, *, issue, story) -> bool` — True if the story file exists.

- `count_stories(project_dir, *, issue) -> int` — Number of stories for the given issue. Convenience for `len(list_stories(...))`.

#### Internal helpers

- `_story_path(project_dir, issue, story) -> Path` — Compute story file path: `.mantle/stories/issue-{issue:02d}-story-{story:02d}.md`.

- `_update_issue_story_count(project_dir, issue) -> None` — Read the parent issue file via `issues.load_issue()`, update `story_count` to `count_stories()` for that issue, then write back via `vault.write_note()`. Uses `issues._issue_path()` to locate the issue file.

- `_update_state_body(project_dir, identity, issue, story_count) -> None` — Update state.md Current Focus section after saving stories. Pattern matches `core/shaping.py`'s `_update_state_body`. Sets focus to: `"Issue {issue} — {story_count} stories planned. Run /mantle:plan-stories for more or /mantle:implement to start building."`. Does not transition state — stays in PLANNING.

#### Imports

```python
from mantle.core import issues, state, vault
```

#### Design decisions

- **Auto-numbering by filename scan per issue.** Same pattern as `issues.next_issue_number()` but scoped to a specific issue. Story numbers are issue-local (issue-01-story-01, issue-01-story-02, issue-02-story-01).
- **Frozen Pydantic model.** Consistent with `IssueNote`, `ShapedIssueNote`, `SessionNote`, `ProjectState`.
- **Updates parent issue story_count.** After saving a story, the parent issue's `story_count` frontmatter is updated to reflect the actual count. This keeps the issue metadata accurate without requiring the caller to manage it.
- **No state transition.** Story planning happens within the PLANNING state. The transition to IMPLEMENTING happens when the orchestrator (issue 13) starts. This matches the state machine: `PLANNING -> IMPLEMENTING`.
- **story parameter for overwrites.** Same pattern as `issues.save_issue()` — normally auto-assigned, but `overwrite=True` requires specifying which story to overwrite.
- **failure_log on StoryNote.** Starts as `None`. The orchestrator populates it with error details when a story fails implementation. The field exists from creation so the schema is stable.

## Tests

### tests/core/test_stories.py (new file)

All tests use `tmp_path` with a pre-created `.mantle/stories/` directory, `.mantle/issues/` with at least one issue file, and `state.md` at `planning` status. Mock `state.resolve_git_identity()` to return a fixed email.

- **StoryNote**: frozen (cannot assign to attributes)
- **StoryNote**: default status is "planned"
- **StoryNote**: default failure_log is None
- **StoryNote**: default tags are ("type/story", "status/planned")
- **save_story**: writes file to `.mantle/stories/` directory
- **save_story**: filename matches `issue-NN-story-NN.md` pattern with zero-padded numbers
- **save_story**: auto-assigns next story number when story not specified
- **save_story**: first story for an issue gets number 01
- **save_story**: second story gets number 02 after first exists
- **save_story**: correct frontmatter fields (issue, title, status, failure_log, tags)
- **save_story**: round-trip with `load_story` preserves frontmatter
- **save_story**: round-trip preserves body content (## Implementation and ## Tests sections)
- **save_story**: raises StoryExistsError when story exists and overwrite is False
- **save_story**: overwrites existing story when overwrite is True and story number specified
- **save_story**: updates parent issue story_count after saving
- **save_story**: story_count reflects actual count (save 3 stories → story_count is 3)
- **save_story**: updates state.md Current Focus section
- **load_story**: reads saved story correctly
- **load_story**: raises FileNotFoundError when path doesn't exist
- **list_stories**: returns empty list when no stories for issue
- **list_stories**: returns sorted paths for the specified issue
- **list_stories**: does not include stories from other issues
- **next_story_number**: returns 1 when no stories exist for issue
- **next_story_number**: returns N+1 when stories exist
- **next_story_number**: handles gaps (e.g., story-01 and story-03 exist → returns 4)
- **story_exists**: returns False when no stories
- **story_exists**: returns True after saving a story
- **count_stories**: returns 0 when no stories
- **count_stories**: returns correct count after saving
