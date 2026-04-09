---
issue: 19
title: State machine update — add ADOPTED status and transitions
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Add the `ADOPTED` status to the state machine as an alternative onboarding path that bypasses the normal `IDEA → CHALLENGE → RESEARCH → PRODUCT_DESIGN → SYSTEM_DESIGN` flow. After adoption, the project has the same artifacts as a fully-designed project and can proceed directly to planning.

### src/mantle/core/state.py (modify)

#### Status enum

Add `ADOPTED = "adopted"` between `SYSTEM_DESIGN` and `PLANNING`:

```python
SYSTEM_DESIGN = "system-design"
ADOPTED = "adopted"
PLANNING = "planning"
```

#### Transition map

Add `Status.ADOPTED` to IDEA's target set, and add an ADOPTED entry with the same targets as SYSTEM_DESIGN:

```python
Status.IDEA: frozenset(
    {Status.CHALLENGE, Status.RESEARCH, Status.PRODUCT_DESIGN, Status.ADOPTED}
),
# ... existing entries unchanged ...
Status.ADOPTED: frozenset({Status.PLANNING}),
```

### src/mantle/core/project.py (modify)

Update `TAGS_BODY` to add `phase/adopted` to the Phase section (after `phase/design`):

```
- `phase/adopted`
```

### Design decisions

- **ADOPTED is a peer of SYSTEM_DESIGN, not a replacement.** Both lead to PLANNING. The normal design flow still works unchanged.
- **Only IDEA can transition to ADOPTED.** Adoption happens right after `mantle init` creates the project at IDEA status. It doesn't make sense to adopt after you've already started the design flow.
- **ADOPTED has the same exits as SYSTEM_DESIGN.** Both represent "design artifacts exist, ready to plan." The only difference is how the artifacts were created.

## Tests

### tests/core/test_state.py (modify)

Update existing tests:

- Status count: 10 -> 11
- Status values: add "adopted"
- IDEA valid targets: add ADOPTED
- New: IDEA -> ADOPTED valid
- New: ADOPTED -> PLANNING valid
- New: ADOPTED -> IMPLEMENTING invalid (can't skip planning)
- New: CHALLENGE -> ADOPTED invalid (must go through IDEA)
- New: PRODUCT_DESIGN -> ADOPTED invalid
- New: ADOPTED -> COMPLETED invalid (terminal only from REVIEWING)
