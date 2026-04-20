---
date: '2026-04-09'
author: 110059232+chonalchendo@users.noreply.github.com
title: archive_issue shaped-doc glob misses slug-less filenames
source: ai
status: promoted
tags:
- type/inbox
- status/promoted
---

core/archive.py:46 globs 'issue-{NN:02d}-*-shaped.md' which requires at least one character between the issue number and '-shaped.md'. Files like 'issue-24-shaped.md' (no slug) are missed. Surfaced during batch archive of issues 01-40. Fix: change pattern to 'issue-{NN:02d}*-shaped.md' or add a second glob for the slug-less case.