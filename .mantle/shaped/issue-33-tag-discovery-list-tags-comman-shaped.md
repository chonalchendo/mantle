---
issue: 33
title: Tag discovery — list-tags command and filtering flow
approaches:
- 'Minimal: tags.py scan on demand'
- 'Split source: tags.py + skills.py separate collection'
chosen_approach: 'Minimal: tags.py scan on demand'
appetite: small batch
open_questions:
- none
author: 110059232+chonalchendo@users.noreply.github.com
created: '2026-04-05'
updated: '2026-04-05'
updated_by: 110059232+chonalchendo@users.noreply.github.com
tags:
- type/shaped
- phase/shaping
---

## Approach A — Minimal: tags.py scan on demand (CHOSEN)

Add `collect_all_tags(project_dir)` to `core/tags.py` that:
1. Calls existing `load_tags()` for taxonomy tags from `.mantle/tags.md`
2. Iterates vault skills via `skills.list_skills()` + `skills.load_skill()` to extract frontmatter tags
3. Returns a `TagCollection` (dataclass or named tuple) with `taxonomy_tags`, `vault_tags`, and `undeclared` (vault - taxonomy)
4. Groups results by prefix using existing `_section_for_tag()`

Add `list-tags` CLI command to `cli/main.py` that prints grouped output with undeclared tags flagged.

Update claude-code layer (help.md) to reference the list-tags → list-skills --tag workflow.

**Appetite**: 1 session. Small batch.

**Tradeoffs**: Loads every skill file on each call — fine for ~30 skills, would need caching for 100+.

**Rabbit holes**: None. The vault is small and both `load_tags()` and `list_skills()` already exist.

**No-gos**: No tag autocomplete, no fuzzy matching, no caching layer.

## Approach B — Split source: tags.py + skills.py separate collection

Keep tag collection split: `tags.py` reads taxonomy, `skills.py` gets a new `collect_skill_tags()` function, `tags.py` merges both. Better separation but more indirection for a simple feature.

**Not chosen** — the indirection isn't justified for this scope.

## Code design

### Strategy

Extend `core/tags.py` with:
- `TagSummary` dataclass: `taxonomy: set[str]`, `vault: set[str]`, `undeclared: set[str]`, `by_prefix: dict[str, list[str]]`
- `collect_all_tags(project_dir: Path) -> TagSummary` — merges taxonomy + vault skill tags, computes undeclared, groups by prefix

Extend `cli/main.py` with:
- `list_tags_command(path)` — calls `tags.collect_all_tags()`, prints grouped output

Update `claude/commands/mantle/help.md` to add `list-tags` to the skill/knowledge section.

### Fits architecture by

- Core logic stays in `core/tags.py` — thin module per system-design.md
- `tags.py` imports from `core/skills.py` for vault tag scanning (core-to-core is fine)
- CLI is a thin wrapper per architecture rule
- `_section_for_tag()` already handles prefix → section mapping

### Does not

- Does not add tag autocomplete or fuzzy matching
- Does not cache tag results across calls
- Does not modify how `list-skills --tag` works (it already works correctly)
- Does not add tags to state.md or change the tag taxonomy format
- Does not validate tag format (existing behavior)