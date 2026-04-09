---
title: Retrospective (/mantle:retrospective)
status: completed
slice: [core, cli, claude-code, tests]
story_count: 3
verification: null
tags:
  - type/issue
  - status/completed
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

- [ ] `/mantle:retrospective` is available in Claude Code and starts an interactive retrospective session
- [ ] The command loads shaped issue context and past learnings for pattern recognition
- [ ] Guided reflection covers four areas: what went well, harder than expected, wrong assumptions, and recommendations
- [ ] Confidence delta is captured with validated format (`+N` or `-N`, 1-2 digits)
- [ ] Learnings are saved to `.mantle/learnings/issue-<NN>.md` with YAML frontmatter
- [ ] Frontmatter includes issue number, title, author, date, confidence_delta, and tags
- [ ] `LearningExistsError` raised when saving to an existing file without `--overwrite`
- [ ] Overwrite mode replaces the existing learning file
- [ ] State.md Current Focus is updated after saving to suggest reviewing past learnings
- [ ] `mantle save-learning` CLI command accepts all required parameters (--issue, --title, --confidence-delta, --content, --overwrite)
- [ ] Tests verify save/load round-trip, overwrite behaviour, confidence_delta validation, state updates, listing, and existence checks

## Blocked by

- Blocked by issue-22 (retrospective references shaped issue artifacts; depends on shaping infrastructure)

## User stories addressed

- User story 59: Guided structured reflection after completing an issue
- User story 60: Learnings include a confidence delta tracking project confidence changes
- User story 61: Learnings automatically surfaced in future `/mantle:shape-issue` sessions
