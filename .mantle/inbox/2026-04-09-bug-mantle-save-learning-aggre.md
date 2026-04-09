---
date: '2026-04-09'
author: 110059232+chonalchendo@users.noreply.github.com
title: 'BUG: mantle save-learning aggressively archives mid-implementation issue files'
source: ai
status: open
tags:
- type/inbox
- status/open
---

When save-learning was called mid-implementation for issue 44 (after Story 1 of 5 completed), the command auto-archived the issue file, shaped doc, and ALL 5 story files (8 files total) to .mantle/archive/. This breaks any /mantle:build pipeline that uses save-learning between stories. Reproduction: run save-learning on an issue that has unfinished stories. Expected: only archive when ALL stories are complete or issue transitions to verified. Found during issue 44 build pipeline run on 2026-04-09; manually restored via mv to recover.