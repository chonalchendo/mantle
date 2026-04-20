---
date: '2026-04-20'
author: 110059232+chonalchendo@users.noreply.github.com
title: 'Tighten verification-strategy handoff: make introspect-project a last-resort
  fallback, not a skip-friendly option'
source: user
status: promoted
tags:
- type/inbox
- status/promoted
---

Subagent handoff currently says 'if no verification strategy is configured, run mantle introspect-project...' which agents interpret loosely and sometimes skip entirely. Reword so it's explicit: check config.md for a verification_strategy field with a value first; only fall back to introspect-project if that field is missing or empty. Make the precedence and the last-resort nature unambiguous.