---
issue: 53
title: Skill anatomy standardisation — executable workflows with anti-rationalization
  guardrails
approaches:
- Vault-native anatomy with marker-based split
chosen_approach: Vault-native anatomy with marker-based split
appetite: medium batch
open_questions:
- None
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-11'
updated: '2026-04-11'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Chosen Approach: Vault-native anatomy with marker-based split

### Description

Restructure vault skill content (below `<!-- mantle:content -->`) into a standardised what/why/when/how anatomy. Add a new `<!-- mantle:reference -->` marker to explicitly control progressive disclosure. The compiler splits at the marker: content above becomes `SKILL.md` body, content below becomes `references/core.md`. Skills without the marker fall back to existing line-count heuristic (backwards compatible).

The what/why/when/how pattern is designed as a one-shot teaching document for AI agents:
- **What** — 1-3 sentences grounding the skill
- **Why** — what goes wrong without it (motivates the agent)
- **When to Use / When NOT to Use** — scoping (prevents over-application)
- **How** — the executable knowledge:
  - For process skills: numbered workflow steps with gates
  - For reference skills: pattern catalogue with decision criteria
  - Common Rationalizations table (anti-skip guardrails)
  - Red Flags checklist (early warning signs)
  - Verification (evidence-based exit criteria)

Deep reference material (full API tables, extended examples, exhaustive checklists) goes below `<!-- mantle:reference -->` and compiles into `references/core.md`.

### Tradeoffs

**Gains:**
- Simplest path — minimal Python changes (one new split function, one constant, update to `_write_compiled_skill`)
- Backwards compatible — un-migrated skills compile exactly as before
- Compiled `SKILL.md` now contains the workflow inline instead of just a pointer, making skills immediately useful when triggered
- Flexible anatomy — "how" can be numbered steps (process skills) or pattern catalogue (reference skills)

**Gives up:**
- No programmatic validation that a skill follows the anatomy — it's a content convention enforced by the `add-skill` prompt
- Migration is manual per-skill — 30+ skills remain in old format until migrated

### Rabbit holes

- Force-fitting reference skills (cyclopts, httpx-async) into numbered workflow steps — the anatomy must allow pattern catalogues as an alternative "how" format
- Over-splitting existing skills where the content naturally fits in <150 lines — not every skill needs a `<!-- mantle:reference -->` marker

### No-gos

- No schema validation of anatomy sections
- No migration of all 35+ skills — only 5 as proof of concept
- No changes to frontmatter fields
- No changes to index note generation or tag handling

### Side-effect impact scan

- `_write_compiled_skill()` changes output format when marker is present: `SKILL.md` gets inline content instead of bare pointer. This affects what Claude sees when a skill triggers. No downstream commands consume compiled skill files — they're read-only by Claude Code's native loader.
- Vault source file changes affect `mantle compile` output. The SessionStart hook calls `mantle compile --if-stale`, which will recompile migrated skills on next session start. No ordering dependency issues.

## Code Design

### Strategy

**Compiler change** (`core/skills.py`):
- New constant: `_REFERENCE_MARKER = "<!-- mantle:reference -->"`
- New function: `_split_on_reference_marker(content: str) -> tuple[str, str]` — splits at marker
- `_write_compiled_skill()`: check for marker first; if present, above-marker content goes into `SKILL.md` body, below-marker into `references/core.md`. If absent, fall back to existing `_PROGRESSIVE_DISCLOSURE_THRESHOLD` heuristic
- `_ESSENTIAL_HEADINGS` and `_split_content_for_disclosure()` remain as fallback — not removed

**`add-skill.md` prompt**: Update content authoring step to generate what/why/when/how anatomy. Include guidance for process vs reference skill "how" sections. Always generate rationalizations table, red flags, verification. Place `<!-- mantle:reference -->` before deep material.

**Vault skill migrations** (5 skills): `design-review`, `software-design-principles`, `python-project-conventions`, `cli-design-best-practices`, `cyclopts`. Restructure content into anatomy, move detailed tables/examples below `<!-- mantle:reference -->`.

### Fits architecture by

- Python changes scoped to `core/skills.py` — honours core-never-imports-cli boundary
- Extends `<!-- mantle:content -->` marker convention with `<!-- mantle:reference -->` — same pattern
- Compiled output stays in `.claude/skills/<slug>/` with same directory structure
- Vault source files remain single `.md` files — no structural change
- `add-skill.md` is a static prompt — prompt-only change
- Backwards compatible with un-migrated skills

### Does not

- Does not add programmatic validation of anatomy sections
- Does not change frontmatter fields (when_to_use, description, proficiency, etc.)
- Does not migrate all 35+ skills — only 5 as proof of concept
- Does not change `compile_skills()` function signature or public API
- Does not remove existing line-count heuristic — becomes fallback path
- Does not change index note generation or tag handling