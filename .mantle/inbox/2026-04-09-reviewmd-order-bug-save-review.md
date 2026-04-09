---
date: '2026-04-09'
author: 110059232+chonalchendo@users.noreply.github.com
title: 'review.md order bug: save-review-result after transition-to-approved fails'
source: ai
status: open
tags:
- type/inbox
- status/open
---

After issue 46 moved archival to transition-to-approved, the save-review-result step in claude/commands/mantle/review.md (which runs AFTER the transition) can no longer find the issue file — it was just archived. find_issue_path only looks in .mantle/issues/, not .mantle/archive/issues/. Two fixes: (1) flip review.md order so save-review-result runs BEFORE transition-to-approved, (2) teach find_issue_path to fall back to .mantle/archive/issues/. Option (1) is simpler. Reproduced live on /mantle:review 46 on 2026-04-09.