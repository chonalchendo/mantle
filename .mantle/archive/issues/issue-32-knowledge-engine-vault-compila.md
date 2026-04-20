---
title: Knowledge engine — vault compilation, query, distillation, and linting
status: approved
slice:
- core
- cli
- claude-code
- tests
story_count: 3
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: '`/mantle:query` prompt searches vault content (skills, learnings, decisions,
    sessions) and answers natural language questions'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Query results cite source notes with file paths so users can verify
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: '`/mantle:distill` synthesizes a topic into a knowledge note saved to the
    vault'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Distillation notes include wikilinks to every source note used
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Distillation notes include staleness metadata (source count, last updated
    date)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`/mantle:query` reads existing distillations to enrich answers'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: All operations are user-triggered — no background token spend
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

The vault accumulates structured knowledge over time (skills, learnings, decisions, session logs, research) but there is no way to query it or synthesize across it. Knowledge that isn't retrievable is knowledge that doesn't exist.

Users want to ask "what do I know about X?" and get grounded answers from accumulated vault content. They also want to discover connections between topics they didn't know existed, and distill scattered notes into concise summaries.

## What to build

### 1. Query command (/mantle:query)

Thin prompt that orchestrates vault search using existing Mantle tools (tags, skills, frontmatter filtering, grep). User asks a natural language question, the prompt searches the vault for relevant notes (skills, learnings, decisions, sessions, research, distillations), then the LLM synthesizes an answer grounded in the retrieved content.

- Searches across the personal vault and current project's `.mantle/`
- Uses existing CLI tools (`mantle list-skills`, tag filtering, file reading)
- Results optionally filed back into the vault as knowledge notes

### 2. Distillation command (/mantle:distill)

User-triggered synthesis of everything on a topic into 1-2 concise paragraphs. Output saved as a knowledge note in the vault.

- Source linking — every distillation includes wikilinks to every source note so the user can verify
- Staleness tracking — metadata records which notes were synthesized and when, flags when new source material exists since last distillation
- Distillations become queryable — `/mantle:query` reads existing distillations, making future queries on the same topic faster and richer
- Distillations compound — each re-run incorporates new sources since the last synthesis

## Design considerations

- All operations are user-triggered — no background LLM calls that silently consume token budgets
- No RAG or embeddings needed — Mantle's structured metadata (frontmatter, tags, wikilinks) provides sufficient signal for retrieval at current vault scale
- Distillation addresses LLM accuracy concerns: source links let users verify, staleness tracking prevents outdated summaries from being trusted blindly
- Cross-project queries are the key differentiator vs just reading `.mantle/` files

## Acceptance criteria

- [ ] ac-01: `/mantle:query` prompt searches vault content (skills, learnings, decisions, sessions) and answers natural language questions
- [ ] ac-02: Query results cite source notes with file paths so users can verify
- [ ] ac-03: `/mantle:distill` synthesizes a topic into a knowledge note saved to the vault
- [ ] ac-04: Distillation notes include wikilinks to every source note used
- [ ] ac-05: Distillation notes include staleness metadata (source count, last updated date)
- [ ] ac-06: `/mantle:query` reads existing distillations to enrich answers
- [ ] ac-07: All operations are user-triggered — no background token spend

## Brainstorm reference

.mantle/brainstorms/2026-04-05-knowledge-engine-query-and-distill.md

## Blocked by

None

## User stories addressed

- As a developer, I want to query my accumulated knowledge across projects so that past learnings inform current decisions
- As a developer, I want topic distillations that synthesize scattered notes into concise summaries so that I can quickly understand what I know about a domain