---
title: Session logging
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

Automatic session logging that captures structured records of what was done, decisions made, and what's next at the end of every Claude Code session. Logs are written to `.mantle/sessions/` with git identity tagging and capped at ~200 words.

This includes:
- `src/mantle/core/session.py` — read/write session logs, format enforcement (~200 word cap), author tagging via git identity
- `vault-templates/session-log.md` — Obsidian note template for session logs
- Session logging instructions embedded in each `/mantle:*` command's closing instructions
- A `.claude/rules/session-logging.md` standing rule for sessions where `/mantle:*` commands aren't used
- Session log format: summary, what was done, decisions made, what's next, open questions

## Acceptance criteria

- [ ] Session logs are written to `.mantle/sessions/<date>-<HHMM>.md` with YAML frontmatter
- [ ] Frontmatter includes project, author (git identity), date, commands_used, and tags
- [ ] Log body follows structured format: summary, what was done, decisions made, what's next, open questions
- [ ] Logs are capped at ~200 words
- [ ] A standing rule in `.claude/rules/` instructs session logging for non-command sessions
- [ ] `core/session.py` provides read/write interface for session logs
- [ ] Tests verify session log format, frontmatter structure, word cap, and read/write operations

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory)

## User stories addressed

- User story 37: Session logs written automatically at the end of every session
- User story 38: Session logs capped at ~200 words
- User story 44: Every note stamped with git identity
