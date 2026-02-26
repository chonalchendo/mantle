---
issue: 19
title: Core adoption module — artifact generation and state transition
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Create `src/mantle/core/adopt.py` that writes reverse-engineered product design and system design documents, then transitions the project to ADOPTED status. This module writes the same file formats as `product_design.py` and `system_design.py` but follows the adoption state path instead of the normal design flow.

### src/mantle/core/adopt.py

```python
"""Project adoption — reverse-engineer design artifacts from existing codebases."""
```

#### Exception

```python
class AdoptionExistsError(Exception):
    """Raised when design docs already exist and overwrite is False."""
    path: Path
```

Raised when either `product-design.md` or `system-design.md` already exists and `overwrite` is False. The `path` attribute points to the first conflicting file found.

#### Functions

- `save_adoption(project_dir, *, vision, principles, building_blocks, prior_art, composition, target_users, success_metrics, system_design_content, overwrite=False) -> tuple[ProductDesignNote, SystemDesignNote]` — Write both design documents and transition to ADOPTED. Checks for existing docs first (raises `AdoptionExistsError`). Writes product-design.md using `ProductDesignNote` schema and `_build_product_design_body` from `product_design.py`. Writes system-design.md using `SystemDesignNote` schema. Transitions state to `Status.ADOPTED`. Updates state.md Current Focus section. Returns both notes.

- `adoption_exists(project_dir) -> bool` — True if either `product-design.md` or `system-design.md` exists.

#### Internal helpers

- `_update_state_body(project_dir, identity) -> None` — Overwrite state.md Current Focus with: "Adoption complete — run /mantle:plan-issues next." Refresh `updated`/`updated_by` timestamps. Same regex pattern as `product_design._update_state_body`.

#### Function details for `save_adoption`

1. Check `product-design.md` and `system-design.md` — raise `AdoptionExistsError` with the first found path if either exists and `overwrite` is False.
2. Transition state to `Status.ADOPTED` (fail fast — validates IDEA → ADOPTED before writing files).
3. Resolve git identity and today's date.
4. Build `ProductDesignNote` from provided fields. Write to `.mantle/product-design.md` using `vault.write_note` and `product_design._build_product_design_body`.
5. Build `SystemDesignNote` with identity/dates. Write to `.mantle/system-design.md` using `vault.write_note`.
6. Update state body with next step.
7. Return `(product_note, system_note)`.

#### Imports

```python
from mantle.core import product_design, state, vault
from mantle.core.product_design import ProductDesignNote
from mantle.core.system_design import SystemDesignNote
```

Note: imports `ProductDesignNote` and `SystemDesignNote` classes directly since they're used as constructors, not just type hints. Imports `product_design` module to access `_build_product_design_body`.

#### Design decisions

- **Fail-fast state transition.** Transition to ADOPTED before writing any files. If the current state doesn't allow adoption (not at IDEA), the error is raised before any filesystem changes.
- **Direct vault writes, not delegating to create_product_design/save_system_design.** Those functions have their own state transition logic (to PRODUCT_DESIGN and SYSTEM_DESIGN respectively). Adoption needs to go directly to ADOPTED.
- **Reuses existing schemas and body builders.** The artifacts are identical in format — only the state transition path differs.
- **Decisions are not part of this module.** The Claude command saves decisions during the interactive session using existing `mantle save-decision` commands, just like `/mantle:design-system` does.

## Tests

### tests/core/test_adopt.py

All tests use `tmp_path` fixture with a pre-created `.mantle/` directory and `state.md` at `Status.IDEA`. Mock `state.resolve_git_identity()` to return a fixed email.

- **save_adoption**: writes product-design.md with correct frontmatter fields
- **save_adoption**: writes system-design.md with correct frontmatter fields
- **save_adoption**: product-design.md round-trips with `product_design.load_product_design`
- **save_adoption**: system-design.md round-trips with `system_design.load_system_design`
- **save_adoption**: transitions state to ADOPTED
- **save_adoption**: state body contains "Adoption complete"
- **save_adoption**: state body contains "/mantle:plan-issues"
- **save_adoption**: state timestamps refreshed
- **save_adoption**: stamps author/updated_by with git identity
- **save_adoption**: raises `AdoptionExistsError` when product-design.md exists
- **save_adoption**: raises `AdoptionExistsError` when system-design.md exists
- **save_adoption**: `overwrite=True` succeeds when docs exist
- **save_adoption**: raises `InvalidTransitionError` when state is not IDEA
- **adoption_exists**: False when no design docs
- **adoption_exists**: True when product-design.md exists
- **adoption_exists**: True when system-design.md exists
