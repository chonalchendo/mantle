---
title: Challenge session (/mantle:challenge)
status: completed
slice:
- core
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
  text: '`/mantle:challenge` is available in Claude Code and starts a multi-angle
    challenge session'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-02
  text: The session weaves through devil's advocate, pre-mortem, and competitive analysis
    adaptively based on conversation flow
  passes: true
  waived: false
  waiver_reason: null
- id: ac-03
  text: The session does not follow a rigid checklist — it adapts questioning to what
    the user says
  passes: true
  waived: false
  waiver_reason: null
- id: ac-04
  text: Challenge transcript is saved to `.mantle/challenges/` with date-based naming
    and YAML frontmatter
  passes: true
  waived: false
  waiver_reason: null
- id: ac-05
  text: The challenge phase is optional — other commands work without it being run
  passes: true
  waived: false
  waiver_reason: null
- id: ac-06
  text: The challenger agent definition is installed to `~/.claude/agents/`
  passes: true
  waived: false
  waiver_reason: null
- id: ac-07
  text: Tests verify prompt construction, session structure, and transcript format
  passes: true
  waived: false
  waiver_reason: null
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

- [x] ac-01: `/mantle:challenge` is available in Claude Code and starts a multi-angle challenge session
- [x] ac-02: The session weaves through devil's advocate, pre-mortem, and competitive analysis adaptively based on conversation flow
- [x] ac-03: The session does not follow a rigid checklist — it adapts questioning to what the user says
- [x] ac-04: Challenge transcript is saved to `.mantle/challenges/` with date-based naming and YAML frontmatter
- [x] ac-05: The challenge phase is optional — other commands work without it being run
- [x] ac-06: The challenger agent definition is installed to `~/.claude/agents/`
- [x] ac-07: Tests verify prompt construction, session structure, and transcript format

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory)

## User stories addressed

- User story 9: AI challenges idea from multiple angles in a single interactive session
- User story 10: Challenge adapts based on conversation flow, not a rigid checklist
- User story 11: Challenge phase is optional
