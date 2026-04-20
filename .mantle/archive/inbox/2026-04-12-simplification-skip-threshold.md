---
date: '2026-04-12'
author: 110059232+chonalchendo@users.noreply.github.com
title: Simplification skip threshold counts mechanical edits as logic changes
source: ai
status: promoted
tags:
- type/inbox
- status/promoted
---

/mantle:build Step 7 skip condition is 'files<=3 AND lines_changed<=50'. Issue 48 added group=GROUPS[...] to 50 decorator calls (298 lines, 0 logic) — refactorer was spawned, reviewed nothing, changed nothing. Wasted ~1min and ~17k tokens per mechanical build. Options: (a) new CLI command that counts unique logical statements via AST diff, (b) shape-issue prompt marks an issue 'mechanical' to force-skip simplification downstream, (c) raise line threshold but keep file threshold (bandaid). Captured from /mantle:retrospective 48.