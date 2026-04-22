---
date: '2026-04-22'
author: 110059232+chonalchendo@users.noreply.github.com
title: audit-tokens Delta summary 'top-3 saved' uses after-rank instead of before-rank
source: ai
status: open
tags:
- type/inbox
- status/open
---

append_after_section computes top_3_saved and top_3_total over after_entries[:3], which is sorted by current (After) token count. When trims substantially re-rank files, top-3 in the summary can list files that were NOT in the original heaviest-3. Observed on issue 88's vault audit: skills top-3 showed 0 saved because the 3 trimmed skills dropped out of the top-3 after-ranking. Fix: compute top-3 using before_tokens descending so the summary reflects impact on the files that were originally heaviest.