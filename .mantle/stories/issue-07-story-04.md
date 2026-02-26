---
issue: 7
title: Claude Code commands (revise-product.md + revise-system.md)
status: pending
failure_log: null
tags:
  - type/story
  - status/pending
---

## Implementation

Create the static Claude Code command prompts for `/mantle:revise-product` and `/mantle:revise-system`. Each guides Claude through reading the current design, running an interactive revision session, and saving via the CLI commands from story 03.

### claude/commands/mantle/revise-product.md

Static prompt guiding Claude through the `/mantle:revise-product` workflow:

1. **Check prerequisites** — Verify `.mantle/` exists and `product-design.md` exists. If missing, tell user to run `/mantle:design-product` first and stop.
2. **Load context** — Read `.mantle/product-design.md` in full. Display a summary of the current design to the user (vision, principles, building blocks).
3. **Interactive revision session** — Ask the user what they want to change and why. Discuss the implications. Iterate until the user is satisfied with the revisions.
4. **Vision section enforcement** — After finalising revisions, check whether the `## Vision` section still accurately reflects the revised design. If not, propose an updated vision and get user approval.
5. **Confirm and save** — Show a before/after summary of what changed. Ask user to confirm. Run `mantle save-revised-product-design` with all updated fields plus `--change-topic`, `--change-summary`, and `--change-rationale`.
6. **Confirmation** — Show the decision log entry path and suggest reviewing the updated document.

### claude/commands/mantle/revise-system.md

Static prompt guiding Claude through the `/mantle:revise-system` workflow:

1. **Check prerequisites** — Verify `.mantle/` exists and `system-design.md` exists. If missing, tell user to run `/mantle:design-system` first and stop.
2. **Load context** — Read `.mantle/system-design.md` in full. Also read `.mantle/product-design.md` for alignment context. Display a summary of the current system design to the user.
3. **Interactive revision session** — Ask the user what they want to change and why. Discuss technical tradeoffs. Iterate until satisfied.
4. **Vision section enforcement** — After finalising revisions, check whether the `## Vision` section at the top of the system design still accurately reflects the changes. If not, propose an updated vision and get user approval.
5. **Confirm and save** — Show a before/after summary. Ask user to confirm. Run `mantle save-revised-system-design` with `--content` (the full revised document body) plus `--change-topic`, `--change-summary`, and `--change-rationale`.
6. **Confirmation** — Show the decision log entry path and suggest reviewing the updated document.

### Key prompt instructions (both commands)

- The revision session should be conversational, not a form fill.
- Vision section check happens after the main revision, as a final step before saving.
- The before/after summary should be concise (3-5 bullet points of what changed, not a full diff).
- `change_topic` should be a short slug describing the revision (e.g., "simplify-architecture", "add-caching-layer").
- `change_summary` is 1-2 sentences of what changed.
- `change_rationale` is 1-2 sentences of why it changed.

## Tests

No tests — static markdown files only.
