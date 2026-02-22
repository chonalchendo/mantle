---
title: Skill graph (/mantle:add-skill)
status: planned
slice: [core, claude-code, vault, tests]
story_count: 0
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:add-skill` command for manually creating skill nodes in the personal vault, plus AI skill gap detection that suggests new nodes when it spots technologies used during implementation that aren't in the graph. Skill nodes use Obsidian wikilinks and YAML frontmatter to form an interconnected knowledge graph across projects.

This includes:
- `src/mantle/core/skills.py` — CRUD operations on skill nodes in personal vault, link detection (find related skills via wikilinks), gap suggestion logic (compare skills_required in state.md against existing skill nodes)
- `claude/commands/mantle/add-skill.md` — static command for creating/updating a skill node with metadata (proficiency, related skills, projects)
- `vault-templates/skill.md` — Obsidian note template for skill nodes
- Skill loading during implementation: relevant skills matched by `skills_required` in state.md are included in compiled context
- AI gap detection: during implementation, if a technology is used that has no matching skill node, suggest creating one

## Acceptance criteria

- [ ] `/mantle:add-skill` is available in Claude Code and creates a skill node in the personal vault
- [ ] Skill nodes include YAML frontmatter: type, proficiency, related skills (wikilinks), projects (wikilinks), last_used, tags
- [ ] Skill nodes are saved to `~/vault/skills/<skill-name>.md` (personal vault path from config)
- [ ] `core/skills.py` detects gaps: compares `skills_required` in state.md against existing skill nodes
- [ ] Gap detection suggests creating missing skill nodes
- [ ] Relevant skill nodes are loadable for inclusion in implementation context (matched by `skills_required`)
- [ ] Tests verify skill CRUD, link detection, gap suggestion logic, and skill loading

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and personal vault config)

## User stories addressed

- User story 40: Create skill nodes with metadata in personal vault
- User story 41: AI suggests skill nodes when detecting untracked technologies
- User story 42: Relevant skill nodes loaded during implementation
