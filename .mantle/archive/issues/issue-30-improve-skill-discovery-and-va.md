---
title: Improve skill discovery and vault navigation
status: completed
slice:
- core
- cli
- claude-code
- tests
story_count: 3
verification: null
blocked_by: []
tags:
- type/issue
- status/completed
---

## Parent PRD

product-design.md, system-design.md

## Why

Skill discovery during the build pipeline (Step 3) relies on name/slug string matching, which misses skills relevant by topic but not by exact name. Additionally, the Obsidian vault lacks navigable index notes for browsing skills by topic — the user's preferred vault organisation pattern uses index notes rather than tag-based grouping.

## What to build

Two complementary improvements to how skills are discovered and navigated:

1. **Tag-based filtering for list-skills** — Add a `--tag` flag to `mantle list-skills` so agents and users can filter skills by topic or domain tags (e.g., `list-skills --tag domain/concurrency`).

2. **Improved update-skills matching** — Extend `detect_skills_from_content()` to match on skill tags and descriptions, not just name/slug. This catches relevant skills that aren't mentioned by exact name in issue content.

3. **Auto-generated index notes** — During `mantle compile`, generate index notes in the personal vault from the tag taxonomy. Skills tagged `domain/concurrency` produce a navigable index note that lists all matching skills as wikilinks. These are derived from existing tags so they stay in sync automatically with zero maintenance.

### Flow

1. User adds skills with topic/domain tags (existing workflow, unchanged)
2. `mantle list-skills --tag domain/web` returns only skills tagged with that domain
3. `mantle update-skills --issue NN` now also matches skills whose tags or description relate to the issue content
4. `mantle compile` generates index notes in the vault (e.g., `indexes/domain-concurrency.md`) listing all matching skills as wikilinks
5. User browses indexes in Obsidian to navigate the skill graph by topic

## Acceptance criteria

- [ ] `list-skills` accepts a `--tag` filter and returns only skills matching that tag
- [ ] `update-skills` matches on skill tags and description, not just name/slug
- [ ] `mantle compile` auto-generates index notes in the vault from the tag taxonomy
- [ ] Generated index notes list skills as Obsidian wikilinks for graph navigation
- [ ] Build pipeline Step 3 works unchanged (backwards compatible)
- [ ] Existing manually-created vault notes are not overwritten by generated indexes

## Blocked by

None

## User stories addressed

- As a developer using the build pipeline, I want skill discovery to find relevant skills by topic so that implementation agents have better domain knowledge
- As a vault user, I want auto-generated index notes so I can browse skills by topic in Obsidian without manual maintenance