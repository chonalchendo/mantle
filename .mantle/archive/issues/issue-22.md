---
title: Shape issue (/mantle:shape-issue)
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

The `/mantle:shape-issue` command that guides the user through evaluating 2-3 approaches for an issue before decomposing it into stories, following Shape Up methodology. The user commits to a direction with understood tradeoffs and a fixed appetite. Shaped artifacts are saved to `.mantle/shaped/`.

This includes:

- `src/mantle/core/shaping.py` — Data model (`ShapedIssueNote`), save/load/list/exists operations for shaped issue artifacts, state.md body updates after shaping
- `src/mantle/cli/shaping.py` — CLI wrapper for `save-shaped-issue` with Rich output
- `cli/main.py` registration — `save-shaped-issue` subcommand wired up with all parameters
- `claude/commands/mantle/shape-issue.md` — Static command prompt guiding the interactive shaping session (approach exploration, comparison, commit)
- Past learnings loaded during shaping to inform approach evaluation
- State.md Current Focus updated after shaping to guide the user to `/mantle:plan-stories`

## Acceptance criteria

- [x] `/mantle:shape-issue` is available in Claude Code and starts an interactive shaping session
- [x] The command loads product design, system design, existing issues, and past learnings as context
- [x] 2-3 approaches are explored interactively with name, description, appetite, tradeoffs, rabbit holes, and no-gos
- [x] A side-by-side comparison is presented before the user commits to a direction
- [x] Shaped issues are saved to `.mantle/shaped/issue-<NN>-shaped.md` with YAML frontmatter
- [x] Frontmatter includes issue number, title, approaches, chosen approach, appetite, open questions, author, timestamps, and tags
- [x] `ShapedIssueExistsError` raised when saving to an existing file without `--overwrite`
- [x] Overwrite mode preserves original `created` date while updating `updated` fields
- [x] State.md Current Focus is updated after shaping to point to `/mantle:plan-stories`
- [x] `mantle save-shaped-issue` CLI command accepts all required parameters
- [x] Tests verify save/load round-trip, overwrite behaviour, state updates, listing, and existence checks

## Blocked by

- Blocked by issue-11 (needs issue planning infrastructure)

## User stories addressed

- User story 56: Evaluate 2-3 approaches before decomposing into stories
- User story 57: Shaped issues saved with YAML frontmatter capturing approaches, chosen approach, appetite, and open questions
- User story 58: Past learnings loaded during shaping sessions
