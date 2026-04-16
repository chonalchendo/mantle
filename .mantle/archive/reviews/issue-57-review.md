---
issue: 57
title: save-learning silently writes after issue archived
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-15'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 57

**save-learning silently writes after issue archived**

## Criteria

- ✓ **mantle save-learning --issue NN exits non-zero and prints a clear error when issue NN is not found in .mantle/issues/** [approved] — passed: true
- ✓ **tests/test_staleness_regressions.py::TestArchiveSideEffects::test_save_learning_after_archive_fails_clearly flips from xfail to a real pass** [approved] — passed: true
- ✓ **Existing learning tests still pass** [approved] — passed: true
- ✓ **just check passes** [approved] — passed: true
