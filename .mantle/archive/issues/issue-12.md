---
title: Story planning (/mantle:plan-stories)
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
- status/planned
acceptance_criteria:
- id: ac-01
  text: '`/mantle:plan-stories` is available in Claude Code and decomposes an issue
    into stories'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Each story includes both implementation tasks (## Implementation) and test
    expectations (## Tests)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Stories are sized for a single Claude Code session (one context window)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Stories are saved to `.mantle/stories/issue-<nn>-story-<nn>.md` with YAML
    frontmatter
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Story frontmatter includes issue reference, title, status (planned), and tags
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: 'Story frontmatter includes a `failure_log: null` field for tracking blocked
    stories'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: Tests verify story file format, frontmatter structure, and naming convention
  passes: false
  waived: false
  waiver_reason: null
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

- [ ] ac-01: `/mantle:plan-stories` is available in Claude Code and decomposes an issue into stories
- [ ] ac-02: Each story includes both implementation tasks (## Implementation) and test expectations (## Tests)
- [ ] ac-03: Stories are sized for a single Claude Code session (one context window)
- [ ] ac-04: Stories are saved to `.mantle/stories/issue-<nn>-story-<nn>.md` with YAML frontmatter
- [ ] ac-05: Story frontmatter includes issue reference, title, status (planned), and tags
- [ ] ac-06: Story frontmatter includes a `failure_log: null` field for tracking blocked stories
- [ ] ac-07: Tests verify story file format, frontmatter structure, and naming convention

## Blocked by

- Blocked by issue-11 (needs issues to decompose into stories)

## User stories addressed

- User story 20: Stories include both implementation tasks and test expectations (TDD)
- User story 21: Stories sized for a single Claude Code session
