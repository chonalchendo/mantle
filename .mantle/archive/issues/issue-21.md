---
title: Skill usability fixes (validation, tagging, Claude Code loading)
status: completed
slice:
- core
- claude-code
- vault
- tests
story_count: 4
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria:
- id: ac-01
  text: '`/mantle:add-skill` validates each `related_skills` entry against existing
    vault skills'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: 'Non-existent related skills trigger a warning with options: create stub,
    remove link, or keep as-is'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Skills receive content-based tags beyond `type/skill` (e.g., `topic/python`,
    `domain/web-development`)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Content tags are suggested by the AI during the workflow, reusing existing
    tags from `tags.md` where appropriate
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: New tags are appended to `tags.md` after user confirmation
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`mantle compile` syncs relevant skills from the vault to `.claude/skills/<skill-name>/SKILL.md`'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: 'Compiled skills use Claude Code''s native YAML frontmatter (`name`, `description`,
    `user-invocable: false`)'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-08
  text: Compiled SKILL.md contains only authored content (vault wikilinks stripped,
    vault metadata omitted)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-09
  text: Skills exceeding 500 lines are split into SKILL.md + reference.md with cross-reference
    link
  passes: false
  waived: false
  waiver_reason: null
- id: ac-10
  text: Skill compilation is triggered by the SessionStart hook alongside existing
    command compilation
  passes: false
  waived: false
  waiver_reason: null
- id: ac-11
  text: Stale skills (removed from vault or no longer in `skills_required`) are cleaned
    up during compilation
  passes: false
  waived: false
  waiver_reason: null
- id: ac-12
  text: Stub skills (0/10 proficiency) in `skills_required` are surfaced in the resume
    briefing
  passes: false
  waived: false
  waiver_reason: null
- id: ac-13
  text: '`/mantle:add-skill` Step 2 surfaces stubs alongside missing skills'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-14
  text: Tests verify link validation, tag derivation, skill compilation, and stub
    detection
  passes: false
  waived: false
  waiver_reason: null
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

- [ ] ac-01: `/mantle:add-skill` validates each `related_skills` entry against existing vault skills
- [ ] ac-02: Non-existent related skills trigger a warning with options: create stub, remove link, or keep as-is
- [ ] ac-03: Skills receive content-based tags beyond `type/skill` (e.g., `topic/python`, `domain/web-development`)
- [ ] ac-04: Content tags are suggested by the AI during the workflow, reusing existing tags from `tags.md` where appropriate
- [ ] ac-05: New tags are appended to `tags.md` after user confirmation
- [ ] ac-06: `mantle compile` syncs relevant skills from the vault to `.claude/skills/<skill-name>/SKILL.md`
- [ ] ac-07: Compiled skills use Claude Code's native YAML frontmatter (`name`, `description`, `user-invocable: false`)
- [ ] ac-08: Compiled SKILL.md contains only authored content (vault wikilinks stripped, vault metadata omitted)
- [ ] ac-09: Skills exceeding 500 lines are split into SKILL.md + reference.md with cross-reference link
- [ ] ac-10: Skill compilation is triggered by the SessionStart hook alongside existing command compilation
- [ ] ac-11: Stale skills (removed from vault or no longer in `skills_required`) are cleaned up during compilation
- [ ] ac-12: Stub skills (0/10 proficiency) in `skills_required` are surfaced in the resume briefing
- [ ] ac-13: `/mantle:add-skill` Step 2 surfaces stubs alongside missing skills
- [ ] ac-14: Tests verify link validation, tag derivation, skill compilation, and stub detection

## Blocked by

- Blocked by issue-17 (needs skill graph implementation)

## User stories addressed

- User story 40: Create skill nodes with metadata in personal vault (fix: links now validated)
- User story 42: Relevant skill nodes loaded during implementation (fix: skills now compiled to `.claude/skills/` for native loading)
- User story 40: Stub skills surfaced on demand when relevant to current work (fix: resume briefing prompts user to fill stubs)
