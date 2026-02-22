---
title: Product design (/mantle:design-product)
status: planned
slice: [core, claude-code, vault, tests]
story_count: 0
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:design-product` Claude Code command that runs an interactive session defining the "what and why" of the product — features, target users, success metrics, and genuine edge. The session produces `.mantle/product-design.md` as a structured document and updates project state.

This includes:
- `claude/commands/mantle/design-product.md` — static command prompt guiding structured product design
- `vault-templates/product-design.md` — Obsidian note template for product design
- Integration with `core/vault.py` for document creation and `core/state.py` for state transition to "product-design"

## Acceptance criteria

- [ ] `/mantle:design-product` is available in Claude Code and starts an interactive product design session
- [ ] The session guides the user through features, target users, success metrics, and genuine edge
- [ ] Product design is saved as `.mantle/product-design.md` with YAML frontmatter
- [ ] Project state transitions to "product-design"
- [ ] The note is stamped with git identity and timestamps
- [ ] Tests verify document structure, frontmatter, and state transition

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and vault.py)

## User stories addressed

- User story 12: Interactive session produces structured product design document
