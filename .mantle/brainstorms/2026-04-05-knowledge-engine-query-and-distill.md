---
date: '2026-04-05'
author: 110059232+chonalchendo@users.noreply.github.com
title: knowledge-engine-query-and-distill
verdict: proceed
tags:
- type/brainstorm
---

## Brainstorm Summary

**Idea**: Knowledge engine — vault query and distillation
**Problem**: The vault accumulates structured knowledge (skills, learnings, decisions, sessions, research) but there is no way to query it or synthesize across it. Knowledge that isn't retrievable is knowledge that doesn't exist.
**Vision alignment**: Strong — directly serves the 'persistent memory' pillar of the product vision. This is what makes accumulated memory useful rather than write-only.

## Exploration

**Problem framing**: Users want to ask 'what do I know about X?' and get grounded answers from accumulated vault content. Also want to discover connections between topics they didn't know existed. Inspired by Karpathy's LLM Knowledge Bases pattern.

**Key insight**: Mantle already has structured query primitives (tags, skills, frontmatter filtering). The missing piece is a prompt orchestration layer for natural language questions, plus a distillation command that synthesizes topics into reusable knowledge notes.

**Scope**: Large paradigm shift overall, but scoped to Approach B (query + distill) for the first cut. Vault linting and mounting are separate future features.

## Challenges Explored

**Assumption surfacing**: 5 assumptions identified. Weakest: LLM accuracy of distillations (#3). Mitigated by source linking (wikilinks to every source note) and staleness tracking (metadata showing when sources have grown since last distillation).

**First-principles analysis**: Karpathy's auto-indexing pattern doesn't translate to Mantle's token-constrained environment. His setup uses API calls with unlimited budget. Mantle users are on Claude Pro/Max subscriptions with rate limits. Every LLM call must be user-triggered, not background processing.

**Architectural tension**: The LLM as ongoing vault maintainer introduces a new pattern — LLM writing to vault as side effect. Resolved by making all operations user-triggered: /mantle:query for Q&A, /mantle:distill for synthesis. No silent background processing.

**Token economics**: Auto-maintained indices would silently eat user token budgets. All knowledge engine operations must be explicitly invoked so users control their token spend.

## Approaches Considered

| Approach | Description | Key Trade-off |
|----------|-------------|---------------|
| A: Query-first | Just /mantle:query — prompt orchestrating vault search | Ships fast but answers are ephemeral, no compounding |
| B: Query + Distill | /mantle:query + /mantle:distill with knowledge notes filed back | Answers compound via reusable distillations. Medium implementation scope |
| C: Full knowledge toolkit | Query + distill + lint-vault + vault mounting | Full Karpathy loop but large scope, vault mounting is infrastructure change |

## Verdict

**Verdict**: proceed
**Reasoning**: Strong vision alignment. The scoped Approach B (query + distill) validates whether users actually interact with accumulated knowledge before investing in the full toolkit. Source linking and staleness tracking address the key accuracy concern. All operations are user-triggered, avoiding token budget issues.
**If proceeding**: Update issue 32 to narrow scope to query + distill only. Split into 2-3 sub-issues: (1) /mantle:query prompt with vault search orchestration, (2) /mantle:distill with knowledge note persistence, source linking, staleness metadata, (3) integration with existing commands (query reads distillations, distill suggests when raw notes accumulate). Vault linting and mounting become separate future issues.