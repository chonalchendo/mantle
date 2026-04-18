---
issue: 63
title: 'story-1: pathspec in git diff --shortstat returns empty match line'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-17'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

When git diff --shortstat is given a pathspec (-- src/ tests/) and all changes fall outside the pathspec, git prints nothing. The _SHORTSTAT_RE regex returns None and the existing `if match is None: return DiffStats(0, 0, 0, 0)` guard handles this without new code. Worth noting for future callers adding pathspecs.