---
issue: 44
title: Fix hardcoded .mantle/ path reads in Claude Code prompts
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-09'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 44

**Fix hardcoded .mantle/ path reads in Claude Code prompts**

## Criteria

- ✓ **CLI command exists that prints resolved .mantle/ absolute path** [approved] — passed: true
- ✓ **All 25 claude/commands/mantle/*.md prompts swept to use $MANTLE_DIR** [approved] — passed: true
- ✓ **/mantle:adopt works end-to-end in global storage mode** [approved] — passed: true
- ✓ **Grep audit confirms no remaining hardcoded .mantle/ path reads** [approved] — passed: true
- ✓ **Unit test covering the new CLI command** [approved] — passed: true
- ✓ **Integration test simulating a global-mode prompt workflow** [approved] — passed: true
