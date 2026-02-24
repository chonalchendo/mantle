---
title: Challenge session (/mantle:challenge)
status: completed
slice: [core, claude-code, tests]
story_count: 3
verification: null
tags:
  - type/issue
  - status/completed
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:challenge` Claude Code command that runs a single interactive session challenging the user's idea from multiple angles — devil's advocate, pre-mortem, and competitive analysis — woven adaptively based on conversation flow rather than following a rigid checklist. The challenge phase is optional; it does not gate subsequent commands.

This includes:
- `claude/commands/mantle/challenge.md` — static command prompt with multi-angle challenge instructions
- `claude/agents/challenger.md` — contrarian subagent definition for idea validation
- `src/mantle/core/challenge.py` — challenge prompt construction and session logic
- Challenge transcript saved to `.mantle/challenges/<date>-challenge.md`

## Acceptance criteria

- [x] `/mantle:challenge` is available in Claude Code and starts a multi-angle challenge session
- [x] The session weaves through devil's advocate, pre-mortem, and competitive analysis adaptively based on conversation flow
- [x] The session does not follow a rigid checklist — it adapts questioning to what the user says
- [x] Challenge transcript is saved to `.mantle/challenges/` with date-based naming and YAML frontmatter
- [x] The challenge phase is optional — other commands work without it being run
- [x] The challenger agent definition is installed to `~/.claude/agents/`
- [x] Tests verify prompt construction, session structure, and transcript format

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory)

## User stories addressed

- User story 9: AI challenges idea from multiple angles in a single interactive session
- User story 10: Challenge adapts based on conversation flow, not a rigid checklist
- User story 11: Challenge phase is optional
