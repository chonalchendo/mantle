---
title: Knowledge engine — vault compilation, query, distillation, and linting
status: planned
slice:
- core
- cli
- claude-code
- tests
story_count: 0
verification: null
blocked_by: []
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

The vault accumulates structured knowledge over time (skills, learnings, decisions, session logs, research) but there is no way to query it, synthesize across it, or maintain its quality. Knowledge that isn't retrievable is knowledge that doesn't exist.

Inspired by Karpathy's LLM Knowledge Bases pattern: raw data is collected, compiled by an LLM into a navigable wiki, then operated on via Q&A and linting — all viewable in Obsidian. Mantle already handles data ingest (structured artifacts from normal workflow). The missing layer is compilation, query, distillation, and maintenance.

## What to build

This is a milestone-sized feature. The vertical slices within it (in dependency order):

### 1. Vault-wide index maintenance
Auto-maintained summary/index files that the LLM keeps current. When a new learning, decision, or skill is saved, relevant indices update. This is the "compiled wiki" primitive.

### 2. Query command (/mantle:query)
Ask natural language questions against the vault. Reads indices + relevant notes, answers grounded in accumulated knowledge. Results optionally filed back into the vault as knowledge notes, enriching future queries.

### 3. Distillation (/mantle:distill)
Synthesize everything on a topic into 1-2 concise paragraphs. Cross-project connections surfaced. Output saved to vault as a knowledge note with wikilinks back to sources. Staleness tracking — distillations flag when source material has grown since last synthesis.

### 4. Vault linting and health checks
Periodic quality maintenance: find stale distillations, orphaned notes, inconsistent data, missing connections. Suggest new topics to explore. LLM-powered "health check" over the knowledge graph.

### 5. Vault mounting (future)
Link .mantle/ directories from multiple projects into the Obsidian personal vault so everything is browsable in one interconnected graph.

## Design considerations

- At Karpathy's scale (~100 articles, ~400K words), auto-maintained index files + summaries work without RAG or embeddings. Start simple.
- The LLM should be the primary author of compiled knowledge — users rarely edit it directly.
- Every query/exploration should "add up" — results filed back enrich the knowledge base.
- Cross-project queries are the key differentiator vs just reading .mantle/ files.

## Acceptance criteria

- [ ] TBD — this issue needs a brainstorm session to define the right entry point and scope before decomposing into concrete acceptance criteria

## Blocked by

None (but should be brainstormed before implementation)

## User stories addressed

- As a developer, I want to query my accumulated knowledge across projects so that past learnings inform current decisions
- As a developer, I want topic distillations that synthesize scattered notes into concise summaries so that I can quickly understand what I know about a domain
- As a developer, I want vault health checks so that my knowledge base stays accurate and well-connected over time