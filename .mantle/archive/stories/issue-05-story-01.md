---
issue: 5
title: Core product design module (core/product_design.py)
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Build the core product design module that handles creating, reading, and checking for `.mantle/product-design.md`. Follows `core/idea.py` API shape. Key difference from idea/challenge: this is the first module to call `state.transition()`.

### src/mantle/core/product_design.py

```python
"""Product design — structured product definition with features, users, and edge."""
```

#### Data model

```python
class ProductDesignNote(pydantic.BaseModel, frozen=True):
    vision: str
    features: tuple[str, ...]
    target_users: str
    success_metrics: tuple[str, ...]
    genuine_edge: str
    author: str
    created: date
    updated: date
    updated_by: str
    tags: tuple[str, ...] = ("type/product-design", "phase/design")
```

#### Exception

```python
class ProductDesignExistsError(Exception):
    path: Path
```

Raised when `product-design.md` already exists and `overwrite=False`.

#### Functions

- `create_product_design(project_dir, *, vision, features, target_users, success_metrics, genuine_edge, overwrite=False) -> ProductDesignNote` — Write `.mantle/product-design.md` with frontmatter and populated body. Update `state.md` body (regex replace Current Focus). Call `state.transition(project_dir, Status.PRODUCT_DESIGN)`. Raise `ProductDesignExistsError` if exists and not overwriting.

- `load_product_design(project_dir) -> ProductDesignNote` — Read `.mantle/product-design.md` via `vault.read_note()`. Raise `FileNotFoundError` if missing.

- `product_design_exists(project_dir) -> bool` — Check `.mantle/product-design.md` exists.

#### Internal helpers

- `_build_product_design_body(note)` — Build markdown body with `## Vision`, `## Features` (bulleted list), `## Target Users`, `## Success Metrics` (bulleted list), `## Genuine Edge`, `## Open Questions` sections.

- `_update_state_body(project_dir, identity)` — Read state.md, `re.sub()` the Current Focus section to "Product design complete — run /mantle:design-system next.", refresh `updated`/`updated_by` timestamps. Uses the challenge.py regex pattern, not fragile placeholder replacement.

#### Design decisions

- **State transition ordering**: Update state body first, then call `state.transition()`. The transition overwrites frontmatter (status field) but preserves body. If we did it in the other order, our body update would read stale body.
- **No `update_product_design()`** yet — issue 7 (revise-product) will add this in v0.3.0.
- Reuses `vault.read_note()`, `vault.write_note()`, `state.resolve_git_identity()`, `state.transition()`.

## Tests

Test fixture creates `.mantle/` with `state.md` at `Status.CHALLENGE` (or `Status.IDEA` for optional-challenge path).

- **create_product_design**: correct frontmatter fields (vision, features, target_users, success_metrics, genuine_edge)
- **create_product_design**: file created at `.mantle/product-design.md`
- **create_product_design**: round-trip with `load_product_design` preserves all fields
- **create_product_design**: body has populated sections (Vision, Features, Target Users, Success Metrics, Genuine Edge, Open Questions)
- **create_product_design**: raises `ProductDesignExistsError` when file exists
- **create_product_design**: `overwrite=True` replaces existing
- **create_product_design**: stamps `author`/`updated_by` with git identity
- **create_product_design**: default tags are `("type/product-design", "phase/design")`
- **create_product_design**: state transitions to `PRODUCT_DESIGN`
- **create_product_design**: state.md Current Focus updated
- **create_product_design**: state.md timestamps refreshed
- **create_product_design**: works from `IDEA` status (challenge is optional)
- **load_product_design**: reads saved document correctly
- **load_product_design**: raises `FileNotFoundError` when missing
- **product_design_exists**: returns False before creation, True after
- **ProductDesignNote**: frozen (cannot assign to attributes)
