---
issue: 12
title: CLI save-story command and main.py registration
status: planned
failure_log: null
tags:
  - type/story
  - status/planned
---

## User Story

As a developer using `/mantle:plan-stories`, I want each approved story persisted via a CLI command so that the interactive command prompt can save stories to disk without calling core Python directly.

## Approach

Add `mantle save-story` following the same CLI wrapper pattern as `save-issue` and `save-shaped-issue` — a thin function in `cli/stories.py` that calls `core/stories.py` from story 1, with Rich-formatted confirmation output. Register the command in `main.py`. This is story 2 of 3: it bridges core (story 1) and the command prompt (story 3).

## Implementation

Add the `mantle save-story` CLI command. `save-story` follows the same pattern as `save-shaped-issue` and `save-issue`. Create the CLI wrapper module and register the command in `main.py`.

### src/mantle/cli/stories.py (new file)

```python
"""CLI wrapper for story planning operations."""
```

#### Function

- `run_save_story(*, issue, title, content, story=None, overwrite=False, project_dir=None) -> None` — Resolve `project_dir` (default to `Path.cwd()`), call `stories.save_story()`, print confirmation with Rich formatting.

Output format matches existing CLI commands:

```
Saved issue-11-story-03.md to .mantle/stories/
  Issue: 11
  Title: Plan-issues command prompt and vault template
  Stories for issue 11: 3
  Next: run /mantle:plan-stories for more or /mantle:implement to start building
```

#### Error handling

Catch `StoryExistsError` and print a user-friendly message suggesting `--overwrite`. This matches the pattern in `cli/issues.py`.

#### Imports

```python
from mantle.core import stories
```

### src/mantle/cli/main.py (modify)

#### Imports

Add `stories` to the CLI imports:

```python
from mantle.cli import (
    ...
    stories,
    ...
)
```

#### New command

Register `save-story` command following the pattern of `save-issue` and `save-shaped-issue`:

```python
@app.command(name="save-story")
def save_story_command(
    issue: Annotated[int, Parameter(name="--issue", help="Parent issue number.")],
    title: Annotated[str, Parameter(name="--title", help="Story title.")],
    content: Annotated[str, Parameter(name="--content", help="Full story body (markdown).")],
    story: Annotated[int | None, Parameter(name="--story", help="Explicit story number (for overwrites).")] = None,
    overwrite: Annotated[bool, Parameter(name="--overwrite", help="Replace existing story.")] = False,
    path: Annotated[Path | None, Parameter(name="--path", help="Project directory. Defaults to cwd.")] = None,
) -> None:
    """Save a planned story to .mantle/stories/."""
    stories.run_save_story(
        issue=issue,
        title=title,
        content=content,
        story=story,
        overwrite=overwrite,
        project_dir=path,
    )
```

#### Design decisions

- **Minimal parameters.** Stories have fewer frontmatter fields than issues (no `slice`, `blocked_by`, `verification`). The `issue` and `title` are the only required metadata — `status`, `failure_log`, and `tags` use defaults.
- **`--story` is optional.** When omitted, auto-assigns the next number for that issue. When provided (with `--overwrite`), targets a specific story for correction during the planning session.
- **`--content` contains both ## Implementation and ## Tests.** The command prompt composes the full story body including both sections. The CLI doesn't parse or validate the body structure — that's the prompt's responsibility.

## Tests

### tests/cli/test_stories.py (new file)

Tests use `tmp_path` with `.mantle/` structure including an issue file. Mock `state.resolve_git_identity()`.

- **run_save_story**: creates story file in `.mantle/stories/`
- **run_save_story**: prints confirmation with issue number, title, and story count
- **run_save_story**: defaults project_dir to cwd when None
- **run_save_story**: handles StoryExistsError with user-friendly message
- **save_story_command**: registered in app as "save-story"
