---
title: Skill usability fixes (validation, tagging, Claude Code loading)
status: planned
slice: [core, claude-code, vault, tests]
story_count: 4
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

Three fixes to make skills created by `/mantle:add-skill` actually usable by Claude. Currently, skills are saved to the personal vault but never reach Claude Code's native skill loading mechanism, related skill links point to non-existent nodes, and the only tag applied is `type/skill` — making skills invisible to topic-based discovery.

This includes:

- **Validate related skill links** — During the add-skill workflow, check whether each `related_skills` entry exists in the vault. Warn the user about non-existent links and offer to create stub skill nodes or remove the link.
- **Add content-based tags** — AI suggests topic and domain tags during the add-skill workflow, reusing existing tags from `tags.md` where appropriate. Tags like `topic/python`, `domain/web` complement the existing `type/skill` tag and enable Obsidian-native discovery.
- **Compile vault skills to `.claude/skills/`** — Add a compilation step that syncs skills from the personal vault into Claude Code's native skill format (`.claude/skills/<skill-name>/SKILL.md` with proper YAML frontmatter, `user-invocable: false` for background knowledge, progressive disclosure for large skills). This bridges the gap between Mantle's vault-based storage and Claude Code's skill loading mechanism.
- **Prompt to fill stub skills on demand** — When a session starts and `skills_required` includes stub skills (0/10 proficiency), surface them in the resume briefing so the user can flesh them out in context. Stubs are filled when relevant, not speculatively.

Story 3 is the critical fix — without it, the other two are cosmetic improvements on skills that Claude never sees. Story 4 closes the loop on stub skills created by story 1.

## Acceptance criteria

- [ ] `/mantle:add-skill` validates each `related_skills` entry against existing vault skills
- [ ] Non-existent related skills trigger a warning with options: create stub, remove link, or keep as-is
- [ ] Skills receive content-based tags beyond `type/skill` (e.g., `topic/python`, `domain/web-development`)
- [ ] Content tags are suggested by the AI during the workflow, reusing existing tags from `tags.md` where appropriate
- [ ] New tags are appended to `tags.md` after user confirmation
- [ ] `mantle compile` syncs relevant skills from the vault to `.claude/skills/<skill-name>/SKILL.md`
- [ ] Compiled skills use Claude Code's native YAML frontmatter (`name`, `description`, `user-invocable: false`)
- [ ] Compiled SKILL.md contains only authored content (vault wikilinks stripped, vault metadata omitted)
- [ ] Skills exceeding 500 lines are split into SKILL.md + reference.md with cross-reference link
- [ ] Skill compilation is triggered by the SessionStart hook alongside existing command compilation
- [ ] Stale skills (removed from vault or no longer in `skills_required`) are cleaned up during compilation
- [ ] Stub skills (0/10 proficiency) in `skills_required` are surfaced in the resume briefing
- [ ] `/mantle:add-skill` Step 2 surfaces stubs alongside missing skills
- [ ] Tests verify link validation, tag derivation, skill compilation, and stub detection

## Blocked by

- Blocked by issue-17 (needs skill graph implementation)

## User stories addressed

- User story 40: Create skill nodes with metadata in personal vault (fix: links now validated)
- User story 42: Relevant skill nodes loaded during implementation (fix: skills now compiled to `.claude/skills/` for native loading)
- User story 40: Stub skills surfaced on demand when relevant to current work (fix: resume briefing prompts user to fill stubs)
