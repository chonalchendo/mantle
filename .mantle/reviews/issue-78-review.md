---
issue: 78
title: Mechanical enforcement of core/ → cli/ import-direction invariant
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-20'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 78

**Mechanical enforcement of core/ → cli/ import-direction invariant**

## Criteria

- ✓ **just check runs mechanical import-direction check and fails on mantle.cli/mantle.api imports from core/** [approved] — passed: true
- ✓ **Failure message names file, forbidden import, and remediation for agent context** [approved] — passed: true
- ✓ **Test introduces violating import into fixture and asserts check catches it** [approved] — passed: true
- ✓ **Rule is data-driven (import-linter contracts) for future invariants** [approved] — passed: true
- ✓ **CONTRIBUTING/CLAUDE docs the rule, points to config, explains extension** [approved] — passed: true
- ✓ **just check passes in clean tree** [approved] — passed: true
