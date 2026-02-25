---
issue: 5
title: Claude Code command + vault template
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Create the static Claude Code command prompt and Obsidian vault template. No code tests.

### claude/commands/mantle/design-product.md

Static prompt guiding Claude through the `/mantle:design-product` workflow:

1. Check prerequisites — `.mantle/`, `idea.md`, existing `product-design.md`
2. Load context — idea.md and challenge findings
3. Interactive design session — five areas one at a time
4. Confirm and save — show summary, run `mantle save-product-design`
5. Next steps — suggest `/mantle:design-system`

### vault-templates/product-design.md

Template with frontmatter fields and placeholder body sections.

## Tests

No tests — static markdown files only.
