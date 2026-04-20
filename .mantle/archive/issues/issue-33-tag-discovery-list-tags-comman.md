---
title: Tag discovery — list-tags command and filtering flow
status: approved
slice:
- core
- cli
- claude-code
- tests
story_count: 2
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: '`mantle list-tags` CLI command exists and prints all known tags'
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: Tags are collected from both `.mantle/tags.md` AND vault skill frontmatter,
    surfacing undeclared tags
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Output is grouped by prefix (topic/, domain/, type/, etc.) for easy scanning
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: Claude-code layer references the list-tags → list-skills --tag workflow
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: Covered by unit tests for core logic and CLI output
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

The LLM can filter skills by tag via `mantle list-skills --tag <tag>`, but has no way to discover what tags exist. This forces guessing, which defeats the purpose of tag-based skill filtering. A `list-tags` command closes the loop: discover tags → pick relevant ones → filter skills.

## What to build

A `mantle list-tags` CLI command that collects tags from both `.mantle/tags.md` (the declared taxonomy) and actual vault skill frontmatter (real usage), merges them, and displays grouped by prefix. Update the claude-code layer so compiled commands or skill descriptions reference the `list-tags` → `list-skills --tag` workflow.

### Flow

1. LLM runs `mantle list-tags` to see all available tags grouped by prefix (topic/, domain/, etc.)
2. LLM identifies relevant tag(s) for its current task
3. LLM runs `mantle list-skills --tag <tag>` to find skills matching that tag
4. Undeclared tags (present in skill frontmatter but missing from tags.md) are surfaced separately so the user can maintain the taxonomy

## Acceptance criteria

- [ ] ac-01: `mantle list-tags` CLI command exists and prints all known tags
- [ ] ac-02: Tags are collected from both `.mantle/tags.md` AND vault skill frontmatter, surfacing undeclared tags
- [ ] ac-03: Output is grouped by prefix (topic/, domain/, type/, etc.) for easy scanning
- [ ] ac-04: Claude-code layer references the list-tags → list-skills --tag workflow
- [ ] ac-05: Covered by unit tests for core logic and CLI output

## Blocked by

None

## User stories addressed

- As an LLM, I want to discover available tags so that I can filter skills by the most relevant tag
- As a user, I want to see which tags exist across my taxonomy and vault so that I can maintain consistency