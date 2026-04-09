---
issue: 2
title: State management module (core/state.py)
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Build the project state management module with state machine validation, atomic operations, and git identity resolution.

### src/mantle/core/state.py

```python
"""Project state management with state machine validation."""
```

#### Data model

```python
class Status(enum.Enum):
    """Project lifecycle status."""
    IDEA = "idea"
    CHALLENGE = "challenge"
    PRODUCT_DESIGN = "product-design"
    SYSTEM_DESIGN = "system-design"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    VERIFYING = "verifying"
    REVIEWING = "reviewing"
    COMPLETED = "completed"

class ProjectState(pydantic.BaseModel, frozen=True):
    """State.md frontmatter schema."""
    project: str
    status: Status
    confidence: str = "0/10"
    created: date
    created_by: str
    updated: date
    updated_by: str
    current_issue: int | None = None
    current_story: int | None = None
    skills_required: tuple[str, ...] = ()
    tags: tuple[str, ...] = ("status/active",)
```

#### Transition map

```python
_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.IDEA: frozenset({Status.CHALLENGE, Status.PRODUCT_DESIGN}),
    Status.CHALLENGE: frozenset({Status.PRODUCT_DESIGN}),
    Status.PRODUCT_DESIGN: frozenset({Status.SYSTEM_DESIGN}),
    Status.SYSTEM_DESIGN: frozenset({Status.PLANNING}),
    Status.PLANNING: frozenset({Status.IMPLEMENTING}),
    Status.IMPLEMENTING: frozenset({Status.VERIFYING, Status.PLANNING}),
    Status.VERIFYING: frozenset({Status.REVIEWING, Status.IMPLEMENTING}),
    Status.REVIEWING: frozenset({Status.COMPLETED, Status.IMPLEMENTING}),
    Status.COMPLETED: frozenset(),
}
```

Note: revise commands (`/mantle:revise-product`, `/mantle:revise-system`) do NOT change status. Only forward progression and known backward steps (implementing→planning, verifying→implementing, reviewing→implementing).

#### Exception

```python
class InvalidTransition(Exception):
    """Raised when a state transition is not allowed."""
    def __init__(
        self,
        current: Status,
        target: Status,
        valid_targets: frozenset[Status],
    ) -> None: ...
```

Stores `current`, `target`, and `valid_targets` as attributes for programmatic access. The `__str__` method produces a human-readable message like "Cannot transition from 'idea' to 'implementing'. Valid targets: challenge, product-design".

#### Functions (all atomic: load → validate → save)

- `create_initial_state(project_dir: Path, project_name: str) -> ProjectState` — Create state.md at `project_dir/.mantle/state.md` with status=IDEA, today's date, git identity. Uses `vault.write_note()`. Returns the created state.

- `load_state(project_dir: Path) -> ProjectState` — Read state.md via `vault.read_note(path, ProjectState)`. Raises `FileNotFoundError` if state.md doesn't exist.

- `transition(project_dir: Path, target: Status) -> ProjectState` — Load current state, validate the transition against `_TRANSITIONS`, update status + updated date + updated_by, write back, return new state. Raises `InvalidTransition` if the transition is not allowed.

- `update_tracking(project_dir: Path, *, current_issue: int | None = None, current_story: int | None = None) -> ProjectState` — Load state, update the tracking fields, write back, return new state. Does not change status.

- `valid_transitions(status: Status) -> frozenset[Status]` — Pure function, returns the set of valid target statuses for a given status. No I/O.

- `resolve_git_identity() -> str` — Run `git config user.email` via `subprocess.run`, return the email string. Raises `RuntimeError` if git is not configured.

#### Internal details

- Each atomic function (create, transition, update_tracking) does its own load → validate → save cycle. No shared state, no "session" object.
- state.md body contains markdown sections: Summary, Current Focus, Blockers, Recent Decisions, Next Steps. Body is preserved across updates (only frontmatter changes).
- Initial state.md body is a template with placeholder sections.

## Tests

All tests use `tmp_path` for isolated file operations. Mock `subprocess.run` for `resolve_git_identity`.

- **create_initial_state**: creates state.md with status=IDEA, correct project name, today's date, git identity
- **create_initial_state**: state.md is readable by `load_state` (round-trip)
- **create_initial_state**: body contains expected markdown sections (Summary, Current Focus, etc.)
- **load_state**: reads state.md and returns ProjectState with correct fields
- **load_state**: raises FileNotFoundError if state.md doesn't exist
- **transition**: idea → challenge succeeds, returns updated state
- **transition**: idea → product-design succeeds (skip challenge is allowed)
- **transition**: idea → implementing raises InvalidTransition
- **transition**: implementing → planning succeeds (backward step allowed)
- **transition**: verifying → implementing succeeds (backward step allowed)
- **transition**: reviewing → implementing succeeds (backward step allowed)
- **transition**: completed → anything raises InvalidTransition (terminal state)
- **transition**: updates `updated` date and `updated_by` field
- **transition**: preserves body content across transition
- **update_tracking**: sets current_issue and current_story without changing status
- **update_tracking**: preserves all other state fields
- **valid_transitions**: returns correct targets for each status
- **valid_transitions**: completed returns empty frozenset
- **resolve_git_identity**: returns email from `git config user.email`
- **resolve_git_identity**: raises RuntimeError when git not configured (mocked)
- **InvalidTransition**: stores current, target, valid_targets attributes
- **InvalidTransition**: __str__ produces readable message
- **ProjectState**: is frozen (cannot assign to fields)
- **Status enum**: has exactly 9 values matching the design
