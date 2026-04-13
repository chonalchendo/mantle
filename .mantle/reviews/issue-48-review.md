---
issue: 48
title: Group mantle CLI commands in --help with Cyclopts help panels
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-12'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 48

**Group mantle CLI commands in --help with Cyclopts help panels**

## Criteria

- ✓ **groups.py exists with GROUPS dict and explicit sort_key** [approved] — passed: true
- ✓ **every top-level command registered with group=GROUPS[...]** [approved] — passed: true
- ✓ **mantle --help renders 8 distinct labelled panels in declared order** [approved] — passed: true
- ✓ **no command in more than one panel and no command missing** [approved] — passed: true
- ✓ **regression test parses --help and asserts each command's group** [approved] — passed: true
- ✓ **every mantle <command> invocation including prompts continues to work unchanged** [approved] — passed: true
- ✓ **uv run pytest and just check both pass** [approved] — passed: true
