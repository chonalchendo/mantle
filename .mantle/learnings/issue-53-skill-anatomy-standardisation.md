---
issue: 53
title: skill-anatomy-standardisation
author: 110059232+chonalchendo@users.noreply.github.com
date: '2026-04-12'
confidence_delta: '+2'
tags:
- type/learning
- phase/reviewing
---

## What went well

- **Shaped approach held up exactly as planned** — Vault-native anatomy with marker-based split, medium appetite. No rabbit holes, no scope creep. The prior shaping session pre-solved all the hard decisions (what/why/when/how anatomy, process vs reference distinction, marker convention).
- **Wave-based parallel execution saved real time** — Story 1 (compiler) and Story 3 (prompt) ran simultaneously in Wave 1 since they had no overlapping files. Story 2 (migrations) in Wave 2 depended on Story 1.
- **Inline implementation for prompt-only story** — Story 3 was a markdown edit, done inline without spawning an agent. Second validation of the issue 52 pattern.
- **First-try success across all stories** — no test retries, no blockers, no review issues. Clean TDD: tests first, then implementation.
- **Backwards-compat design paid off** — marker-first-with-heuristic-fallback meant un-migrated skills compile unchanged. Zero migration risk.

## Harder than expected

Nothing. The scope was well-bounded and the shaping was thorough.

## Wrong assumptions

None — the shaped design mapped 1:1 to implementation.

## Recommendations

1. **Formalise the "prompt-only inline" pattern** — now validated across issues 52 and 53. The build pipeline orchestrator could detect prompt-only stories and skip agent spawn automatically, rather than relying on the orchestrator's judgment each time.
2. **Emphasise wave parallelism in planning** — when stories touch non-overlapping files, running them in parallel is a free win. Worth surfacing as a first-class concept in /mantle:plan-stories output.
3. **Thorough shaping pays compound interest** — this issue's smooth execution came from the prior shaping session nailing the anatomy, split strategy, and migration targets. When shaping is strong, implementation becomes mechanical.