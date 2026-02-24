---
issue: 4
title: Core challenge module (core/challenge.py)
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Build the core challenge module that handles saving, reading, listing, and checking for challenge transcripts in `.mantle/challenges/`. Lean frontmatter — no enums, no verdict, no outcome. The transcript body speaks for itself.

### src/mantle/core/challenge.py

```python
"""Challenge session — stress-test an idea from multiple angles."""
```

#### Data model

```python
class ChallengeNote(pydantic.BaseModel, frozen=True):
    date: date
    author: str
    hypothesis_ref: str
    tags: tuple[str, ...] = ("type/challenge", "phase/challenge")
```

`hypothesis_ref` snapshots the idea at challenge time so the note is self-contained even if `idea.md` changes later.

#### Exception

```python
class IdeaNotFoundError(Exception):
    path: Path
```

Raised when `save_challenge` is called without `idea.md`. Stores the expected path.

#### Functions

- `save_challenge(project_dir, transcript) -> tuple[ChallengeNote, Path]` — Read `idea.md` to snapshot `hypothesis_ref`. Write transcript to `.mantle/challenges/<date>-challenge.md` with auto-increment on collision (-2, -3, ...). Update state.md Current Focus. Returns both the note and path (path is unpredictable due to auto-increment).

- `load_challenge(path) -> tuple[ChallengeNote, str]` — Read a challenge file by absolute path. Composable with `list_challenges()`: `note, body = challenge.load_challenge(paths[-1])`.

- `list_challenges(project_dir) -> list[Path]` — All challenge paths, sorted oldest-first. Empty list if none. Returns paths, not models (Unix philosophy).

- `challenge_exists(project_dir) -> bool` — True if at least one challenge transcript exists.

#### Internal helpers

- `_resolve_challenge_path(project_dir) -> Path` — Compute non-colliding path with auto-increment. `<date>-challenge.md`, then `-2`, `-3` on collision.

- `_update_state_body(project_dir, identity) -> None` — Overwrite Current Focus section content using regex (not fragile placeholder search). Refresh `updated`/`updated_by` timestamps. Status stays unchanged (no state transition).

#### Design decisions

- `save_challenge` returns `tuple[ChallengeNote, Path]` — caller needs the path for confirmation message since auto-increment makes it unpredictable.
- `load_challenge(path)` not `load_challenge(project_dir, filename)` — composable with `list_challenges()`.
- `_update_state_body` uses regex to replace section content, avoiding the fragile placeholder search pattern from idea.py.
- No state machine transition — challenge is optional, only updates body text.
- Reuses `vault.read_note()`, `vault.write_note()`, `state.resolve_git_identity()`, `idea.load_idea()`.

### src/mantle/core/project.py (modify)

Add `"challenges"` to `SUBDIRS` tuple (alphabetically before `"decisions"`).

## Tests

All tests use `tmp_path` fixture with a pre-created `.mantle/` directory, `state.md`, and `idea.md`.

- **save_challenge**: correct frontmatter fields (date, author, hypothesis_ref)
- **save_challenge**: file at `.mantle/challenges/<date>-challenge.md`
- **save_challenge**: round-trip with `load_challenge` preserves frontmatter
- **save_challenge**: transcript in body
- **save_challenge**: raises `IdeaNotFoundError` when idea.md missing
- **save_challenge**: stamps author with git identity
- **save_challenge**: default tags `("type/challenge", "phase/challenge")`
- **save_challenge**: state.md Current Focus updated
- **save_challenge**: state.md timestamps refreshed
- **save_challenge**: state.md status unchanged
- **save_challenge**: auto-increments on same-day collision
- **load_challenge**: reads saved challenge correctly
- **load_challenge**: raises `FileNotFoundError` when missing
- **list_challenges**: empty list when no challenges
- **list_challenges**: sorted paths after saves
- **challenge_exists**: False before, True after saving
- **ChallengeNote**: frozen (cannot assign to attributes)
