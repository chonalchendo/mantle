---
issue: 45
title: Fix issue numbering to include archive — prevent reused numbers
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-09'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 45

**Fix issue numbering to include archive — prevent reused numbers**

## Criteria

- ✓ **next_issue_number scans both active and archive dirs** [approved] — passed: true
- ✓ **save-issue returns globally-unique number higher than both active and archive max** [approved] — passed: true
- ✓ **test_scans_archive_when_computing_max exists and passes** [approved] — passed: true
- ✓ **test_returns_max_plus_1_when_only_archive_has_issues exists and passes** [approved] — passed: true
- ✓ **test_works_when_archive_dir_missing exists and passes** [approved] — passed: true
- ✓ **No regression in tests/core/test_issues.py (42 tests pass)** [approved] — passed: true
