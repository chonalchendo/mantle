---
date: '2026-04-24'
author: 110059232+chonalchendo@users.noreply.github.com
title: Auto-migrate structured ACs in /mantle:verify (and /mantle:review fallback)
source: ai
status: open
tags:
- type/inbox
- status/open
---

Issue 91 review hit empty structured ACs because the issue predated mantle migrate-acs. Had to run the migration mid-flow. migrate-acs is idempotent and fast — call it at the top of /mantle:verify (and as a safety-net in /mantle:review) so legacy issues surface their ACs without manual intervention. Source: issue 91 retrospective (learnings/issue-91-...).