---
title: Idea capture (/mantle:idea)
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

The `/mantle:idea` Claude Code command that runs an interactive session to capture an idea with structured metadata (hypothesis, target user, success criteria) and saves it as `.mantle/idea.md` with YAML frontmatter. The command also updates project state to reflect the idea has been captured.

This includes:
- `claude/commands/mantle/idea.md` — static command prompt that guides the AI through structured idea capture
- `vault-templates/idea.md` — Obsidian note template for ideas
- Integration with `core/vault.py` for note creation and `core/state.py` for state update
- The idea note is saved with git identity, timestamps, and structured frontmatter

## Acceptance criteria

- [ ] `/mantle:idea` is available in Claude Code and starts an interactive idea capture session
- [ ] The session captures hypothesis, target user, and success criteria through guided conversation
- [ ] Idea is saved as `.mantle/idea.md` with YAML frontmatter (hypothesis, target_user, success_criteria, author, date, tags)
- [ ] Project state in state.md is updated to reflect idea capture
- [ ] The idea note is stamped with `git config user.email`
- [ ] Running `/mantle:idea` when an idea already exists warns the user and asks for confirmation before overwriting
- [ ] Tests verify idea note format, frontmatter structure, and state update

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and vault.py)

## User stories addressed

- User story 7: Interactive session captures idea with structured metadata
- User story 8: Ideas saved as markdown files with YAML frontmatter, versioned in git
