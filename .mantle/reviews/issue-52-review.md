---
issue: 52
title: Inject skills as agent-selected context into shaping and story planning
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-11'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 52

**Inject skills as agent-selected context into shaping and story planning**

## Criteria

- ✓ **shape-issue and plan-stories prompts instruct the agent to discover relevant skills via mantle list-skills** [approved] — passed: true
- ✓ **Agent selects applicable skills and can create missing ones via /mantle:add-skill during the session** [approved] — passed: true
- ✓ **Selected skill content is recorded in each story's metadata via a skills field** [approved] — passed: true
  > descoped during shaping - skills load at shaping only
- ✓ **A story implemented with skill references naturally triggers those skills via Claude Code's native loading** [approved] — passed: true
  > descoped during shaping - depends on criterion 3
- ✓ **just check passes** [approved] — passed: true
