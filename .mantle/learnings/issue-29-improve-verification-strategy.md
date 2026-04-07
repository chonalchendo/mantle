---
issue: 29
title: Improve verification strategy — routine build, delayed review
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-07'
confidence_delta: '+0'
tags:
- type/learning
- phase/reviewing
---

## What Went Well

- **Minimal core helper approach was correct**: Shaping chose the smallest option (introspect_project() + prompt updates) over heavier alternatives. The dict-based introspection kept core/verify.py simple while giving prompts enough structure to propose good strategies.
- **3 stories covered 7 ACs cleanly**: Good story decomposition — core introspection, prompt updates, and build pipeline alignment each got their own story with clear boundaries.
- **Strategy evolution pattern works**: The "detect corrections, prompt to update" pattern in verify.md Step 7.5 is a reusable approach for any prompt that should learn from user feedback.

## Harder Than Expected

- Nothing — implementation was straightforward. The issue sat at verified status for several sessions before getting reviewed, but that was backlog management, not implementation difficulty.

## Wrong Assumptions

- None.

## Recommendations

1. **Don't let verified issues linger**: Issue 29 sat at verified for multiple sessions. Future builds should include a check for verified-but-unreviewed issues to prevent backlog drift.
2. **Strategy evolution is a reusable pattern**: The "detect user corrections → prompt to persist" approach from verify.md Step 7.5 could apply to other prompts that accumulate user preferences over time.
3. **Dict-based introspection is sufficient**: No need for pydantic models when the consumer is a prompt that formats the data as markdown. Keep introspection results as plain dicts.