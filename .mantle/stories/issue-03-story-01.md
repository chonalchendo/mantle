---
issue: 3
title: Core idea module (core/idea.py)
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Build the core idea module that handles creating, reading, updating, and checking for `.mantle/idea.md`. Mirrors the `state.py` API shape with 4 public functions and no state machine.

### src/mantle/core/idea.py

```python
"""Idea capture — structured hypothesis with success criteria."""
```

#### Data model

```python
class IdeaNote(pydantic.BaseModel, frozen=True):
    hypothesis: str
    target_user: str
    success_criteria: tuple[str, ...]
    author: str
    created: date
    updated: date
    updated_by: str
    tags: tuple[str, ...] = ("type/idea", "phase/idea")
```

Named `IdeaNote` (not `IdeaFrontmatter`) with `author` field (matches system design note schemas for decisions/sessions).

#### Exception

```python
class IdeaExistsError(Exception):
    path: Path
```

Raised when `idea.md` already exists and `overwrite=False`. Stores the path for CLI error messaging.

#### Functions

- `create_idea(project_dir, *, hypothesis, target_user, success_criteria, overwrite=False) -> IdeaNote` — Write `.mantle/idea.md` with frontmatter and body template. Update `state.md` body (replace Summary and Current Focus placeholders). Refresh state timestamps. Raise `IdeaExistsError` if exists and not overwriting.

- `load_idea(project_dir) -> IdeaNote` — Read `.mantle/idea.md` via `vault.read_note()`. Raise `FileNotFoundError` if missing.

- `update_idea(project_dir, *, hypothesis=None, target_user=None, success_criteria=None) -> IdeaNote` — Update provided fields, preserve unchanged ones, refresh timestamps. Raise `FileNotFoundError` if missing.

- `idea_exists(project_dir) -> bool` — Check `.mantle/idea.md` exists.

#### Internal helpers

- `_IDEA_BODY` — Template with `## Hypothesis`, `## Target User`, `## Success Criteria`, `## Open Questions` sections.

- `_update_state_body(project_dir, hypothesis, identity)` — Read state.md, replace `_Describe the project in one or two sentences._` with hypothesis, replace `_What are you working on right now?_` with "Idea captured — run /mantle:challenge next.", refresh `updated`/`updated_by` timestamps. Status stays IDEA (no state transition).

#### Design decisions

- Body is a fixed template. Core writes the template; the Claude Code command fills sections through conversation. All structured data lives in frontmatter.
- State update happens inside `create_idea()` — replaces placeholder text in state.md body and refreshes timestamps. No state machine transition.
- Reuses `vault.read_note()`, `vault.write_note()`, `state.resolve_git_identity()`, `state.ProjectState`.

## Tests

All tests use `tmp_path` fixture with a pre-created `.mantle/` directory and `state.md`.

- **create_idea**: correct frontmatter fields (hypothesis, target_user, success_criteria)
- **create_idea**: file created at `.mantle/idea.md`
- **create_idea**: round-trip with `load_idea` preserves all fields
- **create_idea**: body has template sections (Hypothesis, Target User, Success Criteria, Open Questions)
- **create_idea**: raises `IdeaExistsError` when idea.md already exists
- **create_idea**: `overwrite=True` replaces existing idea
- **create_idea**: stamps `author` and `updated_by` with git identity
- **create_idea**: default tags are `("type/idea", "phase/idea")`
- **create_idea**: state.md Summary updated with hypothesis
- **create_idea**: state.md Current Focus updated with "Idea captured" message
- **create_idea**: state.md status stays IDEA (no transition)
- **create_idea**: state.md timestamps refreshed
- **load_idea**: reads saved idea correctly
- **load_idea**: raises `FileNotFoundError` when missing
- **update_idea**: updates provided fields
- **update_idea**: preserves unchanged fields
- **update_idea**: refreshes timestamps
- **update_idea**: raises `FileNotFoundError` when missing
- **idea_exists**: returns False before creation
- **idea_exists**: returns True after creation
- **IdeaNote**: frozen (cannot assign to attributes)
