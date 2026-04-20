---
date: '2026-04-20'
author: 110059232+chonalchendo@users.noreply.github.com
title: Use Claude Code hooks to set MANTLE_DIR env var instead of 'mantle where'
source: user
status: promoted
tags:
- type/inbox
- status/promoted
---

Add hooks for common setup tasks — e.g. a SessionStart bash hook that resolves the mantle directory once and exports MANTLE_DIR, so commands and prompts reference $MANTLE_DIR directly instead of asking the LLM to run 'mantle where' each time. Cheaper, more reliable, fewer tool calls.