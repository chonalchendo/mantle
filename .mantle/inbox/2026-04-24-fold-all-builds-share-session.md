---
date: '2026-04-24'
author: 110059232+chonalchendo@users.noreply.github.com
title: Fold all-builds-share-session-UUID canary into issue 89 shape
source: ai
status: open
tags:
- type/inbox
- status/open
---

The build-telemetry rot that drove issue 91 sat silently for 8 days across 15 build files because nothing flagged 'same session UUID across N consecutive builds'. When issue 89 (A/B harness) is shaped, include a data-health guard that warns when all recent builds share one session_id — would have caught 91's regression class in ~1 build instead of 15. Cheap at shape time. Source: issue 91 retrospective.