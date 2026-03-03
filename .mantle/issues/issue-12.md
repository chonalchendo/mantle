---
title: Story planning (/mantle:plan-stories)
status: planned
slice: [core, claude-code, vault, tests]
story_count: 3
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:plan-stories` Claude Code command that decomposes each issue into implementable stories sized for a single Claude Code session. Each story includes both implementation tasks and test expectations (TDD approach — tests are a natural extension of story functionality).

This includes:
- `claude/commands/mantle/plan-stories.md` — static command prompt guiding story decomposition with TDD test specs
- `vault-templates/story.md` — Obsidian note template for stories
- Integration with `core/vault.py` for story file creation
- Story schema: issue reference, title, status, implementation description, test specifications, failure_log field

## Acceptance criteria

- [ ] `/mantle:plan-stories` is available in Claude Code and decomposes an issue into stories
- [ ] Each story includes both implementation tasks (## Implementation) and test expectations (## Tests)
- [ ] Stories are sized for a single Claude Code session (one context window)
- [ ] Stories are saved to `.mantle/stories/issue-<nn>-story-<nn>.md` with YAML frontmatter
- [ ] Story frontmatter includes issue reference, title, status (planned), and tags
- [ ] Story frontmatter includes a `failure_log: null` field for tracking blocked stories
- [ ] Tests verify story file format, frontmatter structure, and naming convention

## Blocked by

- Blocked by issue-11 (needs issues to decompose into stories)

## User stories addressed

- User story 20: Stories include both implementation tasks and test expectations (TDD)
- User story 21: Stories sized for a single Claude Code session
