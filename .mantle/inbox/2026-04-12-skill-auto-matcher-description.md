---
date: '2026-04-12'
author: 110059232+chonalchendo@users.noreply.github.com
title: 'Skill auto-matcher: description-overlap rule produces false positives'
source: ai
status: open
tags:
- type/inbox
- status/open
---

mantle update-skills --issue 48 (CLI-grouping issue) matched 'Nick Sleep Investment Philosophy' because the description-word-overlap rule in src/mantle/core/skills.py:776-778 hits 3 common tokens (scale/lens/etc). Recurring noise — adds stale entries to skills_required and downstream compile output. Options: raise threshold from 3 to 5-6 (risks losing true positives), weight tokens by IDF (scope creep), drop the description-overlap rule entirely and rely on name+slug+tag matching only (safest — test across existing issues first). Needs evaluation across 10+ real issues before choosing. Captured from /mantle:retrospective 48.