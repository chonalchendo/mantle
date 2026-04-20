---
title: Skill graph (/mantle:add-skill)
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
- status/completed
acceptance_criteria:
- id: ac-01
  text: '`/mantle:add-skill` is available in Claude Code and creates a skill node
    in the personal vault'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-02
  text: 'Skill nodes include YAML frontmatter: type, proficiency, related skills (wikilinks),
    projects (wikilinks), last_used, tags'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-03
  text: Skill nodes are saved to `~/vault/skills/<skill-name>.md` (personal vault
    path from config)
  passes: true
  waived: false
  waiver_reason: null
- id: ac-04
  text: '`core/skills.py` detects gaps: compares `skills_required` in state.md against
    existing skill nodes'
  passes: true
  waived: false
  waiver_reason: null
- id: ac-05
  text: Gap detection suggests creating missing skill nodes
  passes: true
  waived: false
  waiver_reason: null
- id: ac-06
  text: Relevant skill nodes are loadable for inclusion in implementation context
    (matched by `skills_required`)
  passes: true
  waived: false
  waiver_reason: null
- id: ac-07
  text: Tests verify skill CRUD, link detection, gap suggestion logic, and skill loading
  passes: true
  waived: false
  waiver_reason: null
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

- [x] ac-01: `/mantle:add-skill` is available in Claude Code and creates a skill node in the personal vault
- [x] ac-02: Skill nodes include YAML frontmatter: type, proficiency, related skills (wikilinks), projects (wikilinks), last_used, tags
- [x] ac-03: Skill nodes are saved to `~/vault/skills/<skill-name>.md` (personal vault path from config)
- [x] ac-04: `core/skills.py` detects gaps: compares `skills_required` in state.md against existing skill nodes
- [x] ac-05: Gap detection suggests creating missing skill nodes
- [x] ac-06: Relevant skill nodes are loadable for inclusion in implementation context (matched by `skills_required`)
- [x] ac-07: Tests verify skill CRUD, link detection, gap suggestion logic, and skill loading

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory and personal vault config)

## User stories addressed

- User story 40: Create skill nodes with metadata in personal vault
- User story 41: AI suggests skill nodes when detecting untracked technologies
- User story 42: Relevant skill nodes loaded during implementation
