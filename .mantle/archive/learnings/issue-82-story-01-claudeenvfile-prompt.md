---
issue: 82
title: 'story-01: CLAUDE_ENV_FILE + prompt-sweep accepts'
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-21'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

When editing the resolve prelude in claude/commands/mantle/*.md, tests/prompts/test_prompt_sweep.py literal-matches the exact string `MANTLE_DIR=$(mantle where)` across every prompt file. Adding a new variant (e.g. the hook-aware `MANTLE_DIR="${MANTLE_DIR:-$(mantle where)}"`) requires widening the `accepted` tuple in `_assert_includes_resolve_prelude` in the same commit — otherwise the sweep fails. Future prelude variants should follow the same widening pattern rather than replacing the guard.