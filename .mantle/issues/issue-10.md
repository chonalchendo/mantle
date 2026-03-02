---
title: Auto-briefing on session start (/mantle:resume)
status: planned
slice: [core, claude-code, tests]
story_count: 3
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

The auto-briefing system that compiles and displays a project briefing when a Claude Code session starts in a Mantle project. The briefing includes project state, last session log, open blockers, and next actions. Also provides `/mantle:resume` as a manual mid-session refresh.

This includes:
- `src/mantle/core/session.py` — briefing compilation (extends session.py from issue-09): load state, find latest session log for current user (filtered by git identity), compose briefing
- `claude/commands/mantle/resume.md.j2` — Jinja2 template for the compiled briefing
- `claude/hooks/session-start.sh` — SessionStart hook that runs `mantle compile --if-stale` then auto-displays the compiled briefing
- Integration with the compilation engine from issue-08 to render resume.md.j2

## Acceptance criteria

- [ ] A SessionStart hook runs `mantle compile --if-stale` and auto-displays the compiled briefing
- [ ] The briefing includes: project state, last session log (filtered to current user), open blockers, next actions
- [ ] Session log filtering uses `git config user.email` to show only the current user's latest session
- [ ] `/mantle:resume` is available as a manual command for mid-session context refresh
- [ ] The briefing fits within ~3K token budget
- [ ] The hook is installed to `~/.claude/` by `mantle install --global`
- [ ] Auto-briefing only displays when in a directory with `.mantle/` (no-op otherwise)
- [ ] Tests verify briefing compilation, author filtering, and hook behaviour

## Blocked by

- Blocked by issue-08 (needs compilation engine)
- Blocked by issue-09 (needs session logging for briefing content)

## User stories addressed

- User story 34: Compiled briefing auto-displays on session start
- User story 35: Briefing includes state, last session, blockers, next actions
- User story 36: `/mantle:resume` available for mid-session refresh
- User story 45: Resume filters session logs to current user's sessions
