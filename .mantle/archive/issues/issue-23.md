---
title: Retrospective (/mantle:retrospective)
status: completed
slice:
- core
- cli
- claude-code
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
  text: '`/mantle:retrospective` is available in Claude Code and starts an interactive
    retrospective session'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: The command loads shaped issue context and past learnings for pattern recognition
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: 'Guided reflection covers four areas: what went well, harder than expected,
    wrong assumptions, and recommendations'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Confidence delta is captured with validated format (`+N` or `-N`, 1-2 digits)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Learnings are saved to `.mantle/learnings/issue-<NN>.md` with YAML frontmatter
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Frontmatter includes issue number, title, author, date, confidence_delta,
    and tags
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: '`LearningExistsError` raised when saving to an existing file without `--overwrite`'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: Overwrite mode replaces the existing learning file
  passes: false
  waived: false
  waiver_reason: null
- id: ac-09
  text: State.md Current Focus is updated after saving to suggest reviewing past learnings
  passes: false
  waived: false
  waiver_reason: null
- id: ac-10
  text: '`mantle save-learning` CLI command accepts all required parameters (--issue,
    --title, --confidence-delta, --content, --overwrite)'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-11
  text: Tests verify save/load round-trip, overwrite behaviour, confidence_delta validation,
    state updates, listing, and existence checks
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:retrospective` command that guides the user through a structured reflection after completing an issue, capturing implementation learnings with a confidence delta. Learnings are saved to `.mantle/learnings/` and automatically surface in future `/mantle:shape-issue` sessions, creating a compounding feedback loop.

This includes:

- `src/mantle/core/learning.py` — Data model (`LearningNote`), save/load/list/exists operations for learning artifacts, confidence_delta validation, state.md body updates after saving
- `src/mantle/cli/learning.py` — CLI wrapper for `save-learning` with Rich output
- `cli/main.py` registration — `save-learning` subcommand wired up with all parameters
- `claude/commands/mantle/retrospective.md` — Static command prompt guiding the interactive retrospective session (what went well, harder than expected, wrong assumptions, recommendations, confidence delta)
- State.md Current Focus updated after retrospective to guide the user to review past learnings before the next planning cycle

## Acceptance criteria

- [ ] ac-01: `/mantle:retrospective` is available in Claude Code and starts an interactive retrospective session
- [ ] ac-02: The command loads shaped issue context and past learnings for pattern recognition
- [ ] ac-03: Guided reflection covers four areas: what went well, harder than expected, wrong assumptions, and recommendations
- [ ] ac-04: Confidence delta is captured with validated format (`+N` or `-N`, 1-2 digits)
- [ ] ac-05: Learnings are saved to `.mantle/learnings/issue-<NN>.md` with YAML frontmatter
- [ ] ac-06: Frontmatter includes issue number, title, author, date, confidence_delta, and tags
- [ ] ac-07: `LearningExistsError` raised when saving to an existing file without `--overwrite`
- [ ] ac-08: Overwrite mode replaces the existing learning file
- [ ] ac-09: State.md Current Focus is updated after saving to suggest reviewing past learnings
- [ ] ac-10: `mantle save-learning` CLI command accepts all required parameters (--issue, --title, --confidence-delta, --content, --overwrite)
- [ ] ac-11: Tests verify save/load round-trip, overwrite behaviour, confidence_delta validation, state updates, listing, and existence checks

## Blocked by

- Blocked by issue-22 (retrospective references shaped issue artifacts; depends on shaping infrastructure)

## User stories addressed

- User story 59: Guided structured reflection after completing an issue
- User story 60: Learnings include a confidence delta tracking project confidence changes
- User story 61: Learnings automatically surfaced in future `/mantle:shape-issue` sessions
