---
title: Session logging
status: done
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
- status/done
acceptance_criteria:
- id: ac-01
  text: Session logs are written to `.mantle/sessions/<date>-<HHMM>.md` with YAML
    frontmatter
  passes: true
  waived: false
  waiver_reason: null
- id: ac-02
  text: Frontmatter includes project, author (git identity), date, commands_used,
    and tags
  passes: true
  waived: false
  waiver_reason: null
- id: ac-03
  text: 'Log body follows structured format: summary, what was done, decisions made,
    what''s next, open questions'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-04
  text: Logs are capped at ~200 words
  passes: true
  waived: false
  waiver_reason: null
- id: ac-05
  text: A standing rule in `.claude/rules/` instructs session logging for non-command
    sessions
  passes: true
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`core/session.py` provides read/write interface for session logs'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-07
  text: Tests verify session log format, frontmatter structure, word cap, and read/write
    operations
  passes: true
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## What to build

Automatic session logging that captures structured records of what was done, decisions made, and what's next at the end of every Claude Code session. Logs are written to `.mantle/sessions/` with git identity tagging and capped at ~200 words.

This includes:
- `src/mantle/core/session.py` — read/write session logs, format enforcement (~200 word cap), author tagging via git identity
- `vault-templates/session-log.md` — Obsidian note template for session logs
- Session logging instructions embedded in each `/mantle:*` command's closing instructions
- A `.claude/rules/session-logging.md` standing rule for sessions where `/mantle:*` commands aren't used
- Session log format: summary, what was done, decisions made, what's next, open questions

## Acceptance criteria

- [x] ac-01: Session logs are written to `.mantle/sessions/<date>-<HHMM>.md` with YAML frontmatter
- [x] ac-02: Frontmatter includes project, author (git identity), date, commands_used, and tags
- [x] ac-03: Log body follows structured format: summary, what was done, decisions made, what's next, open questions
- [x] ac-04: Logs are capped at ~200 words
- [x] ac-05: A standing rule in `.claude/rules/` instructs session logging for non-command sessions
- [x] ac-06: `core/session.py` provides read/write interface for session logs
- [x] ac-07: Tests verify session log format, frontmatter structure, word cap, and read/write operations

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory)

## User stories addressed

- User story 37: Session logs written automatically at the end of every session
- User story 38: Session logs capped at ~200 words
- User story 44: Every note stamped with git identity
