---
date: '2026-04-09'
author: 110059232+chonalchendo@users.noreply.github.com
title: save-learning auto-archive breaks build pipeline ordering
source: ai
status: promoted
tags:
- type/inbox
- status/promoted
---

implement.md Step 9 saves a learning which triggers archive.archive_issue(), moving issue/shaped/story files to .mantle/archive/ BEFORE build.md Steps 7 (simplify) and 8 (verify) have run. Observed during /mantle:build 45. Workaround: restore files, delete duplicate archives, re-run transition. Fix: either (a) defer learning save to after verify, (b) add a --no-archive flag, or (c) stop auto-archiving in save-learning entirely and make archiving an explicit step triggered by transition-issue-verified or similar.