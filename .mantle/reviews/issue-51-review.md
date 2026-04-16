---
issue: 51
title: Contextual CLI errors with recovery suggestions
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-16'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 51

**Contextual CLI errors with recovery suggestions**

## Criteria

- ✓ **A shared error formatting utility exists in src/mantle/cli/ that outputs errors to stderr with Rich [red]Error:[/] prefix and a dim-styled recovery suggestion** [approved] — passed: true
- ✓ **All existing CLI error paths use the shared utility (no raw print or sys.exit for errors)** [approved] — passed: true
- ✓ **Every error includes a recovery suggestion (e.g., "Run mantle init to create a project", "Check the issue number with mantle --help")** [approved] — passed: true
- ✓ **A test verifies error output goes to stderr and includes the recovery hint format** [approved] — passed: true
- ✓ **just check passes** [approved] — passed: true
