---
issue: 32
title: Knowledge engine — vault compilation, query, distillation, and linting
approaches:
- Prompt + Thin Core
- Core Search Aggregation
- Full Knowledge Engine
chosen_approach: Prompt + Thin Core
appetite: small batch
open_questions:
- Should distillations also search the personal vault, or just .mantle/?
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-06'
updated: '2026-04-06'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approaches

### A: Prompt + Thin Core (chosen)
Two new prompt files (query.md, distill.md) that orchestrate vault search using existing CLI tools. New core/knowledge.py for distillation note persistence with staleness metadata. CLI subcommands for saving/loading distillations. Query is purely prompt-orchestrated — no new Python search infrastructure.
- Appetite: small batch (1-2 days)
- Key benefit: Minimal code, leverages existing vault tools
- Key risk: Prompt-orchestrated search may be slower than Python-side aggregation
- Complexity: Low — follows brainstorm.py pattern exactly

### B: Core Search Aggregation
Same as A, plus a unified search_vault() function in core/knowledge.py that aggregates across all content types with Python-side filtering.
- Appetite: medium batch (3-5 days)
- Key benefit: Faster, more structured search
- Key risk: Over-engineering for current vault scale
- Complexity: Medium

### C: Full Knowledge Engine
Adds indexing, cross-reference graph, cached search results.
- Appetite: large batch (1-2 weeks)
- Key benefit: Scales to large vaults
- Key risk: Massive over-engineering, RAG-like complexity
- Complexity: High

## Rationale
Approach A satisfies all 7 ACs with minimum code. The vault is structured (frontmatter, tags, wikilinks) — Claude can search it effectively via existing CLI tools without Python search infrastructure. Distillations are the only new persistent artifact, requiring a thin core module.

## Code Design

### Strategy
New core/knowledge.py module with save/load pipeline for distillation notes. Frontmatter schema DistillationNote tracks topic, source_paths, source_count, and last_updated. Two prompt files (query.md, distill.md) handle all LLM orchestration. CLI subcommands (save-distillation, list-distillations, load-distillation) wire core to prompts. Distillations stored in .mantle/distillations/.

### Fits architecture by
- Core never imports CLI — prompts invoke mantle CLI via Bash tool
- Follows vault.read_note/write_note pattern (brainstorm, learning, challenge)
- .mantle/distillations/ follows existing directory convention
- Prompt orchestrates, AI implements — query and distill are prompt-driven

### Does not
- Add search indexing or embeddings (structured metadata suffices per design)
- Add background LLM calls (AC 7: user-triggered only)
- Modify existing vault modules (additive only)
- Add cross-project query (.mantle/ project scope first; personal vault skills already searchable)
- Build a Python search aggregation layer (prompt handles search orchestration)