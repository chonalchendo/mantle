---
date: '2026-04-16'
author: 110059232+chonalchendo@users.noreply.github.com
title: awesome-claude-skills-post-triage
verdict: scrap
tags:
- type/brainstorm
---

## Brainstorm Summary

**Idea**: Investigate whether a survey post of community Claude skills (Matt Pocock, Anthropic, Superpowers, etc.) surfaces anything Mantle should adopt.
**Problem**: Open-ended scan of an external skill catalogue for missing Mantle capabilities.
**Vision alignment**: N/A for the batch (mixed) — triage-only exercise.

## Exploration

Mapped every skill in the post against Mantle's existing command surface. Most have a clear Mantle home:

- Grill Me / Brainstorming / Stochastic Consensus → `/mantle:challenge`, `/mantle:brainstorm`
- Write a PRD / PRD→Plan / PRD→Issues → `/mantle:design-product`, `/mantle:plan-issues`, `/mantle:plan-stories`, `/mantle:shape-issue`
- TDD / Code Review / QA / Systematic Debugging → `/mantle:plan-stories` (test specs), `/mantle:review`, `/mantle:verify`
- Triage Issue → `/mantle:bug`
- Simplification Cascade / Improve Architecture / Request Refactor → `/mantle:simplify`, `/mantle:refactor`
- Skill Creator / Write a Skill → `/mantle:add-skill`
- Obsidian Vault / session continuity → core Mantle
- Auto-commit / Git Guardrails / Pre-commit / Dependency Auditor → harness or project concerns, out of scope
- Marketing / design / media / document-format skills → out of scope (not software dev lifecycle)

Five threads are genuinely not covered by Mantle:

1. **Design-an-Interface (parallel divergent proposals)** — parallel sub-agents generate 3–5 radically different interface designs. `/mantle:shape-issue` does this sequentially in one agent and tends to produce variations-on-a-theme.
2. **Ubiquitous Language / project glossary** — DDD-style glossary persisted in vault, fed into future commands so domain terms are consistent.
3. **Skill Creator benchmark loop** — run skill-under-construction against 3–5 sample prompts, inspect failures, refine, then save. `/mantle:add-skill` saves on author intent alone.
4. **Skill discovery from marketplaces (SkillsMP / community repos)** — search before authoring. Mantle's skill graph is author-only today.
5. **Multi-agent debate for challenge** — opposing-framing parallel agents for high-stakes challenges.

## Challenges Explored

- **Rubber-stamp risk**: User's initial ask was "investigate all five." Pushed back — batch-brainstorming five distinct ideas produces shallow coverage and inflates an already-live backlog (#42, #51, #56 open).
- **Pain-driven test**: Asked for a concrete moment where (3) — vague `/mantle:add-skill` output — actually failed in practice. User declined to name one and pivoted to "park in inbox."
- **Opportunity cost**: Three live issues in backlog already. None of the five threads passed a pain-driven test. Spinning up 5 brainstorms now = pure speculation.

## Approaches Considered

Not reached — exploration stopped at the pain-driven test for the user's chosen thread (benchmark loop) when no concrete failure surfaced.

## Verdict

**Verdict**: scrap
**Reasoning**: The survey surfaced five candidates genuinely outside Mantle's current surface, but none survived a pain-driven test. The user has not hit a concrete failure mode that any of them would fix, and the live backlog (#42 report-to-github, #51 contextual errors, #56 lifecycle hooks) is a more useful place to put effort. Candidates are preserved as inbox items so they can resurface if real pain emerges.
**If scrapping**: Five inbox items created capturing the triaged threads. Focus next session on shipping #42, #51, or #56 — one of those is the next real unit of value. Re-evaluate the inbox candidates only when a concrete incident points at one.