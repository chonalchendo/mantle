---
issue: 64
title: Fix archive_issue shaped-doc glob to match slug-less filenames
status: approved
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-18'
tags:
- type/review
- phase/reviewing
---

# Review — Issue 64

**Fix archive_issue shaped-doc glob to match slug-less filenames**

## Criteria

- ✓ **archive_issue matches issue-NN-shaped.md (no slug) in addition to issue-NN-<slug>-shaped.md** [approved] — passed: true
- ✓ **Unit test covers both filename forms; regression test for the slug-less form passes** [approved] — passed: true
- ✓ **just check passes** [approved] — passed: true
