---
title: Idea capture (/mantle:idea)
status: completed
slice:
- core
- claude-code
- vault
- tests
story_count: 3
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/completed
acceptance_criteria:
- id: ac-01
  text: '`/mantle:idea` is available in Claude Code and starts an interactive idea
    capture session'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-02
  text: The session captures hypothesis, target user, and success criteria through
    guided conversation
  passes: true
  waived: false
  waiver_reason: null
- id: ac-03
  text: Idea is saved as `.mantle/idea.md` with YAML frontmatter (hypothesis, target_user,
    success_criteria, author, date, tags)
  passes: true
  waived: false
  waiver_reason: null
- id: ac-04
  text: Project state in state.md is updated to reflect idea capture
  passes: true
  waived: false
  waiver_reason: null
- id: ac-05
  text: The idea note is stamped with `git config user.email`
  passes: true
  waived: false
  waiver_reason: null
- id: ac-06
  text: Running `/mantle:idea` when an idea already exists warns the user and asks
    for confirmation before overwriting
  passes: true
  waived: false
  waiver_reason: null
- id: ac-07
  text: Tests verify idea note format, frontmatter structure, and state update
  passes: true
  waived: false
  waiver_reason: null
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

- [x] ac-01: `/mantle:idea` is available in Claude Code and starts an interactive idea capture session
- [x] ac-02: The session captures hypothesis, target user, and success criteria through guided conversation
- [x] ac-03: Idea is saved as `.mantle/idea.md` with YAML frontmatter (hypothesis, target_user, success_criteria, author, date, tags)
- [x] ac-04: Project state in state.md is updated to reflect idea capture
- [x] ac-05: The idea note is stamped with `git config user.email`
- [x] ac-06: Running `/mantle:idea` when an idea already exists warns the user and asks for confirmation before overwriting
- [x] ac-07: Tests verify idea note format, frontmatter structure, and state update

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and vault.py)

## User stories addressed

- User story 7: Interactive session captures idea with structured metadata
- User story 8: Ideas saved as markdown files with YAML frontmatter, versioned in git
