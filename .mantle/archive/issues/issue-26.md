---
title: Auto-detect skills_required from issue and story content
status: completed
slice:
- core
- claude-code
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria:
- id: ac-01
  text: Function exists to extract skill references from issue/story markdown content
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Extracted skills are matched against vault skill names (slug-normalized)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: skills_required in state.md is auto-updated when stories are saved
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: /mantle:build auto-updates skills_required before implementation begins
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Existing manually-added skills are preserved (additive update)
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: Compilation is triggered after skills_required changes
  passes: false
  waived: false
  waiver_reason: null
- id: ac-07
  text: Issue frontmatter supports optional skills_required field
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Users must manually maintain the skills_required field in state.md, which is tedious and often stale. Stories already list their technologies explicitly — the system should extract skill requirements automatically so the right vault knowledge is always compiled into Claude's context.

## What to build

Auto-update skills_required when stories are planned or when /mantle:build runs:

1. Extract technology/skill references from issue and story content
2. Match against vault skill names/tags
3. Update skills_required in state.md automatically
4. Trigger recompilation so .claude/skills/ reflects the current work

Additionally, add an optional skills_required field to issue frontmatter so switching issues automatically loads the right skills.

Key design decisions:
- Detect from stories/issues (explicit technology references), not generic keyword matching
- Keep skills_required as the single source of truth for compilation
- Auto-update is additive — don't remove skills the user manually added
- Recompilation happens via existing compile pipeline

## Acceptance criteria

- [ ] ac-01: Function exists to extract skill references from issue/story markdown content
- [ ] ac-02: Extracted skills are matched against vault skill names (slug-normalized)
- [ ] ac-03: skills_required in state.md is auto-updated when stories are saved
- [ ] ac-04: /mantle:build auto-updates skills_required before implementation begins
- [ ] ac-05: Existing manually-added skills are preserved (additive update)
- [ ] ac-06: Compilation is triggered after skills_required changes
- [ ] ac-07: Issue frontmatter supports optional skills_required field

## Blocked by

None

## User stories addressed

- As a developer, I want the right vault skills loaded automatically so I don't have to manually manage skills_required