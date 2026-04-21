---
issue: 82
title: Export MANTLE_DIR via Claude Code SessionStart hook instead of per-command
  'mantle where'
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-21'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 82

**Export MANTLE_DIR via Claude Code SessionStart hook instead of per-command 'mantle where'**

## Criteria

- ✓ **ac-01: SessionStart hook exists that exports MANTLE_DIR for the current session** [approved] — passed: true
- ✓ **ac-02: Highest-frequency command uses $MANTLE_DIR and no longer asks the LLM to run mantle where when the env var is set** [approved] — passed: true
- ✓ **ac-03: When MANTLE_DIR is not set, commands still function (fallback to the prior path)** [approved] — passed: true
- ✓ **ac-04: A test covers the hook generation / installation path** [approved] — passed: true
- ✓ **ac-05: just check passes** [approved] — passed: true
