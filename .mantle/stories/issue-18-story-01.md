---
issue: 18
title: Core research module + state machine + project init
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Build the core research module that handles saving, reading, listing, and checking for research notes in `.mantle/research/`. Follows the `core/challenge.py` pattern exactly, with the addition of focus angle and confidence rating in frontmatter.

### src/mantle/core/research.py

```python
"""Research notes — validate ideas with evidence from web research."""
```

#### Data model

```python
class ResearchNote(pydantic.BaseModel, frozen=True):
    date: date
    author: str
    focus: str          # validated against VALID_FOCUSES
    confidence: str     # "N/10" format
    idea_ref: str       # snapshot of idea's problem field
    tags: tuple[str, ...] = ("type/research", "phase/research")

VALID_FOCUSES: frozenset[str] = frozenset({
    "general", "feasibility", "competitive", "technology", "user-needs",
})
```

`idea_ref` snapshots the idea's problem at research time so the note is self-contained even if `idea.md` changes later.

#### Exception

```python
class IdeaNotFoundError(Exception):
    path: Path
```

Raised when `save_research` is called without `idea.md`. Own copy, same pattern as `challenge.IdeaNotFoundError`.

#### Functions

- `save_research(project_dir, content, *, focus, confidence) -> tuple[ResearchNote, Path]` — Validate focus against `VALID_FOCUSES` and confidence against `"N/10"` format. Read `idea.md` to snapshot `idea_ref` (problem field). Write to `.mantle/research/<date>-<focus>.md` with auto-increment on collision (-2, -3, ...). Update state.md Current Focus. Returns both the note and path.

- `load_research(path) -> tuple[ResearchNote, str]` — Read a research file by absolute path. Composable with `list_research()`.

- `list_research(project_dir) -> list[Path]` — All research paths, sorted oldest-first. Empty list if none.

- `research_exists(project_dir) -> bool` — True if at least one research note exists.

#### Internal helpers

- `_resolve_research_path(project_dir, focus) -> Path` — Compute non-colliding path with auto-increment. `<date>-<focus>.md`, then `-2`, `-3` on collision.

- `_update_state_body(project_dir, identity, focus) -> None` — Overwrite Current Focus section content using regex. Text: "Research ({focus}) completed — run /mantle:research for another angle or /mantle:design-product next." Refresh `updated`/`updated_by` timestamps. Status stays unchanged (no state transition).

#### Design decisions

- `save_research` returns `tuple[ResearchNote, Path]` — caller needs the path for confirmation message since auto-increment makes it unpredictable.
- `load_research(path)` not `load_research(project_dir, filename)` — composable with `list_research()`.
- Focus-specific filenames (`<date>-<focus>.md`) allow multiple focus angles on the same day without collision until same focus is repeated.
- Validation of focus and confidence happens early (ValueError) before any filesystem work.
- Reuses `vault.read_note()`, `vault.write_note()`, `state.resolve_git_identity()`, `idea.load_idea()`.

### src/mantle/core/state.py (modify)

Add `RESEARCH = "research"` to `Status` enum (between `CHALLENGE` and `PRODUCT_DESIGN`).

Update `_TRANSITIONS`:

```python
Status.IDEA: frozenset({Status.CHALLENGE, Status.RESEARCH, Status.PRODUCT_DESIGN}),
Status.CHALLENGE: frozenset({Status.RESEARCH, Status.PRODUCT_DESIGN}),
Status.RESEARCH: frozenset({Status.PRODUCT_DESIGN}),  # NEW
```

### src/mantle/core/project.py (modify)

Add `"research"` to `SUBDIRS` tuple (alphabetically: after `"issues"`, before `"sessions"`).

## Tests

### tests/core/test_research.py

All tests use `tmp_path` fixture with a pre-created `.mantle/` directory, `state.md`, and `idea.md`. Mock `state.resolve_git_identity()` to return a fixed email.

- **save_research**: correct frontmatter fields (date, author, focus, confidence, idea_ref)
- **save_research**: file at `.mantle/research/<date>-<focus>.md`
- **save_research**: round-trip with `load_research` preserves frontmatter
- **save_research**: content in body
- **save_research**: raises `IdeaNotFoundError` when idea.md missing
- **save_research**: stamps author with git identity
- **save_research**: default tags `("type/research", "phase/research")`
- **save_research**: state.md Current Focus updated with focus name
- **save_research**: state.md timestamps refreshed
- **save_research**: state.md status unchanged
- **save_research**: auto-increments on same-focus same-day collision
- **save_research**: different focus on same day does NOT collide
- **save_research**: raises `ValueError` on invalid focus
- **save_research**: raises `ValueError` on invalid confidence format
- **load_research**: reads saved research correctly
- **load_research**: raises `FileNotFoundError` when missing
- **list_research**: empty list when no research notes
- **list_research**: sorted paths after saves
- **research_exists**: False before, True after saving
- **ResearchNote**: frozen (cannot assign to attributes)

### tests/core/test_state.py (modify)

Update existing tests:

- Status count: 9 -> 10
- Status values: add "research"
- IDEA valid targets: add RESEARCH
- New: IDEA -> RESEARCH valid
- New: CHALLENGE -> RESEARCH valid
- New: RESEARCH -> PRODUCT_DESIGN valid
- New: RESEARCH -> IMPLEMENTING invalid
