---
issue: 49
title: Rethink tag naming conventions for meaningful vault indexes
approaches:
- 'Prompt-only: rewrite add-skill step 6 guidance to encourage coarse-grained tags.
  Simplest change but no reference list for the LLM to check against.'
- 'Taxonomy-first with scoring: pre-populate tags.md + add core scoring function that
  flags overly-specific tags. Over-engineered for this problem.'
- 'Taxonomy-aware prompt: rewrite step 6 to check existing tags.md first, reuse existing
  coarse tags, only create new ones when nothing fits. Both topic/ and domain/ use
  coarse names. Manual migration for existing tags.'
chosen_approach: Taxonomy-aware prompt
appetite: small batch
open_questions:
- What's the right initial seed list for domain/ tags? User mentioned data-engineering,
  data-science — need to enumerate the full set during implementation.
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-10'
updated: '2026-04-10'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen approach: Taxonomy-aware prompt

Rewrite the add-skill prompt's step 6 to make the LLM taxonomy-aware: check tags.md first, reuse existing coarse-grained tags, only create new ones when nothing fits. Apply the same coarse-grained rule to both topic/ and domain/ prefixes. Migrate existing tags manually.

### Why this approach

The root cause is the prompt guidance saying "one topic tag matching the skill's subject" — which naturally produces 1:1 mappings like topic/dbt-incremental. The fix is prompt-level: tell the LLM to prefer existing tags and use coarse names. No scoring engine or validation code needed — the LLM's judgment is sufficient when given clear rules and a reference list.

### Rejected alternatives

- **Prompt-only (A)**: Too simple — without checking the existing taxonomy, the LLM might still invent overly-specific tags even with better guidance.
- **Taxonomy-first with scoring (B)**: Over-engineered — adding a core scoring function for tag specificity is unnecessary complexity. The LLM can make this judgment given good examples.

## Code design

### Strategy

Two changes:

1. **Rewrite step 6 in `claude/commands/mantle/add-skill.md`** — Replace current guidance with taxonomy-aware rules:
   - Check tags.md first, reuse existing tags where they fit
   - Only create new tags when nothing in the taxonomy covers the skill's domain
   - New tags must be coarse-grained: topic/ tags represent broad subjects (e.g. dbt, scraping, investment), domain/ tags represent high-level disciplines (e.g. data-engineering, finance, devops)
   - Explicit good/bad examples for both prefixes
   - Remove "one tag matching the skill's subject" phrasing

2. **Manual tag migration** — Update existing vault skills' frontmatter and tags.md to use coarser conventions. Run mantle compile to regenerate index notes. One-time task, not automated.

### Fits architecture by

- Prompt change stays in claude/commands/mantle/ — no core code touched
- Manual migration uses existing vault.write_note() / tags.add_tags() pathways
- Index regeneration via existing generate_index_notes() called by mantle compile

### Does not

- Does not add a migrate-tags CLI command (one-time task, not permanent tooling)
- Does not add runtime tag validation or scoring logic
- Does not change core/tags.py or core/skills.py
- Does not modify how compile_skills() works
- Does not add a tag suggestion API