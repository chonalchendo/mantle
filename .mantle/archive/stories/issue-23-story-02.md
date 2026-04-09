---
issue: 23
title: CLI save-learning command and main.py registration
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Add the `mantle save-learning` CLI command. Follows the same pattern as `save-shaped-issue` and `save-skill`. Create the CLI wrapper module and register the command in `main.py`.

### `src/mantle/cli/learning.py` (new file)

#### Function

- `run_save_learning(*, issue, title, confidence_delta, content, overwrite=False, project_dir=None) -> None` — Resolve `project_dir` (default to `Path.cwd()`), call `learning.save_learning()`, print confirmation with Rich formatting.

Output format matches existing CLI commands:

```
Learning saved to issue-21.md

  Issue:            21
  Title:            Shaping phase implementation
  Confidence delta: +2
  Author:           user@example.com

  Learnings auto-surface in future /mantle:shape-issue sessions
```

#### Error handling

- Catch `LearningExistsError` and print a user-friendly message suggesting `--overwrite`. Exit with code 1.
- Catch `ValueError` (invalid confidence_delta) and print the error message. Exit with code 1.

#### Imports

```python
from mantle.core import learning
```

### `src/mantle/cli/main.py` (modify)

#### Imports

Add `learning` to the CLI imports:

```python
from mantle.cli import (
    ...
    learning,
    ...
)
```

#### New command

Register `save-learning` command:

```python
@app.command(name="save-learning")
def save_learning_command(
    issue: Annotated[int, Parameter(name="--issue", help="Issue number this learning relates to.")],
    title: Annotated[str, Parameter(name="--title", help="Short title for the learning.")],
    confidence_delta: Annotated[str, Parameter(name="--confidence-delta", help="Confidence change (e.g. '+2', '-1').")],
    content: Annotated[str, Parameter(name="--content", help="Structured reflection body.")],
    overwrite: Annotated[bool, Parameter(name="--overwrite", help="Replace existing learning.")] = False,
    path: Annotated[Path | None, Parameter(name="--path", help="Project directory.")] = None,
) -> None:
    """Save a learning note to .mantle/learnings/."""
    learning.run_save_learning(
        issue=issue,
        title=title,
        confidence_delta=confidence_delta,
        content=content,
        overwrite=overwrite,
        project_dir=path,
    )
```

### Design decisions

- **Fewer parameters than save-shaped-issue.** Learnings are simpler — no approaches, no appetite, no open questions. Just issue, title, confidence delta, and content.
- **Two error types caught.** Both `LearningExistsError` and `ValueError` (from confidence_delta validation) exit with code 1 and print user-friendly messages.
- **Next-step message in output.** The confirmation message tells the user that learnings auto-surface in future shaping sessions, reinforcing the feedback loop.

## Tests

No dedicated CLI tests for this story. The CLI wrapper is a thin delegation to `core/learning.py` which has comprehensive tests in story 1. Verified by:
- The `save-learning` command is registered in `main.py`
- Running `mantle save-learning --help` shows all parameters
- The retrospective command prompt in story 3 invokes `mantle save-learning` successfully
