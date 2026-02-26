---
issue: 7
title: Core product design update function with decision logging
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Add `update_product_design()` to `core/product_design.py` that overwrites the existing product design document with revised content and auto-creates a decision log entry capturing what changed and why. No state transition — the project stays at the same status during revisions.

### src/mantle/core/product_design.py (modify)

#### New function

- `update_product_design(project_dir, *, vision, principles, building_blocks, prior_art, composition, target_users, success_metrics, change_topic, change_summary, change_rationale) -> tuple[ProductDesignNote, Path]` — Load current product design (raise `FileNotFoundError` if missing). Overwrite `.mantle/product-design.md` with the new fields. Preserve the original `author` and `created` from the existing note. Stamp `updated`/`updated_by` with current git identity and today's date. Call `decisions.save_decision()` to create a decision log entry. Return the updated note and the decision log entry path.

#### Decision log entry construction

The decision log entry is created by calling `decisions.save_decision()` with:
- `topic`: `change_topic` (caller provides, e.g. "reframe-product-vision")
- `decision`: `change_summary` (what changed)
- `alternatives`: `["Keep current design"]`
- `rationale`: `change_rationale` (why it changed)
- `reversal_trigger`: `"Revert if change no longer serves product goals."`
- `confidence`: `"7/10"`
- `reversible`: `"high"`
- `scope`: `"product-design"`

#### Import change

Add `from mantle.core import decisions` alongside the existing `state` and `vault` imports (inside the `if TYPE_CHECKING` block is not needed since `decisions` is called at runtime — add it to the top-level imports).

#### Design decisions

- **Preserves `author` and `created`**: The original creator is remembered. Only `updated`/`updated_by` change.
- **No state transition**: Revisions don't change the project lifecycle status. The project can be in `system-design`, `planning`, or any later phase when revising product design.
- **Decision log is mandatory**: Every revision creates a decision entry. There's no opt-out — traceability is the whole point.
- **Caller provides change metadata**: The Claude command prompt guides the AI to summarise what changed and why, then passes those strings to the CLI.
- **Returns `tuple[ProductDesignNote, Path]`**: Note for confirmation output, path for the decision log entry location (unpredictable due to auto-increment).

## Tests

Test fixture creates `.mantle/` with `state.md` at `Status.SYSTEM_DESIGN` and an existing `product-design.md` (via `create_product_design`).

- **update_product_design**: updated note has revised vision
- **update_product_design**: updated note has revised principles
- **update_product_design**: updated note has revised building_blocks
- **update_product_design**: updated note preserves original `author` and `created`
- **update_product_design**: stamps `updated`/`updated_by` with git identity
- **update_product_design**: round-trip with `load_product_design` returns updated fields
- **update_product_design**: creates decision log entry in `.mantle/decisions/`
- **update_product_design**: decision entry has correct topic, scope "product-design"
- **update_product_design**: decision entry body contains change summary and rationale
- **update_product_design**: raises `FileNotFoundError` when product-design.md missing
- **update_product_design**: does not change project state status
- **update_product_design**: second revision creates a second decision log entry
