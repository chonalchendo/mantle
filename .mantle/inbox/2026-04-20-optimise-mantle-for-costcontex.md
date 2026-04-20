---
date: '2026-04-20'
author: 110059232+chonalchendo@users.noreply.github.com
title: 'Optimise Mantle for cost/context: model routing, context budgeting, fit heavy
  commands in 200k'
source: user
status: promoted
tags:
- type/inbox
- status/promoted
---

Work has moved to API per-usage billing, so Sonnet 4.6 (200k) will be the default and heavy commands like /mantle:build must fit within that window. Three threads: (1) model routing — Opus only for heavy reasoning/thinking, Sonnet for everything else; (2) context management — streamline prompts, skills, and compiled payloads so large tasks complete without overflow; (3) cost optimisation with minimal performance degradation. Personal-side benefit too: Opus 5hr rate limits get hit fast when juggling multiple projects, so efficiency gains help there.