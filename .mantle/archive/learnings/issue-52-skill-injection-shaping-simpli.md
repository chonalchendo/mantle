---
issue: 52
title: skill-injection-shaping-simplification
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-11'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **First-principles scope reduction worked** — original issue had 5 ACs including per-story skill tagging and native trigger loading. Shaping challenged the scope: skills only need to load at shaping (where design decisions happen), downstream stages consume shaped output. Reduced from 3-4 stories to 2, both completed first try.
- **Agent-curated selection approach held up exactly as shaped** — SkillSummary model + enriched list-skills CLI, then prompt changes. No rabbit holes, no scope creep.
- **Model selection was correct** — opus for story 1 (multi-file Python + tests), inline implementation for story 2 (prompt-only changes, no agent needed).
- **Prompt-only stories don't need agent spawn** — story 2 was two text replacements. Implementing inline saved an agent round-trip with no quality loss.

## Harder than expected

- **Code reviewer false positive on Python 3.14 syntax** — reviewer flagged `except A, B:` (comma without parens) as a critical SyntaxError, claiming it was Python 2 syntax. This is valid in Python 3.14 (PEP 758). Wasted a review cycle. The simplification agent also tried to 'fix' it, but ruff reformatted it back to the project's convention.

## Wrong assumptions

- **Reviewer agent doesn't know Python 3.14 features** — confidently claimed SyntaxError despite all 1064 tests passing. Training data gap. A Python 3.14 skill would prevent this.

## Recommendations

1. **Add a Python 3.14 features skill** — PEP 758 (bare except commas), PEP 695 (type parameter syntax), and other 3.14 changes that agents may not know about. This prevents false positives in review and simplification steps.
2. **Replace code reviewer step with improved simplification** — the code reviewer added a round-trip for mostly false positives. An improved simplification step does the same quality checks plus actually fixes things. User is planning this change to implement.md.
3. **Prompt-only stories can be implemented inline** — when a story changes only markdown prompt files (no Python), the build orchestrator can make the edits directly instead of spawning an agent. Saves context and time.