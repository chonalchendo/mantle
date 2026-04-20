---
title: Reduce update-skills false positives from description-overlap matching
status: approved
slice:
- core
- tests
story_count: 1
verification: null
blocked_by: []
skills_required:
- DuckLake
- Howard Marks Investment Philosophy
- Nick Sleep Investment Philosophy
- Python 3.14
- Python Project Conventions
- Python package structure
- cyclopts
- dirty-equals
- inline-snapshot
- omegaconf
- pydantic-project-conventions
- python-314
tags:
- type/issue
- status/approved
acceptance_criteria:
- id: ac-01
  text: Shaped doc reports the per-issue diff (skills added/removed) for the chosen
    rule against issues 40-63.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: No false positive of the type "DuckLake on a CLI fix" or "Nick Sleep on a
    CLI grouping issue" in the test corpus.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Unit test pins the new matching rule against a fixture issue with known expected
    matches.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

`core/skills.py:776-778` uses a description-word-overlap rule (3+ non-stopword tokens) that produces false positives in `update-skills --issue NN`. Concrete cases:
- Issue 45 (a one-function fix) matched DuckLake, cyclopts, CLI design, Python package structure — DuckLake has zero relevance (inbox 2026-04-09).
- Issue 48 (CLI grouping) matched 'Nick Sleep Investment Philosophy' on 3 common tokens (scale/lens/etc) (inbox 2026-04-12).

False positives pollute `skills_required` and downstream compile output. Two inbox items report the same defect.

## What to build

Pick one (shape to decide):
- **(a) Drop the description-overlap rule.** Rely on name + slug + tag matching. Safest; needs evaluation across past issues to confirm no true positives are lost.
- **(b) Raise threshold from 3 → 5-6 tokens.** Bandaid; may still miss IDF-weighted semantics.
- **(c) IDF-weight tokens.** Most robust; scope creep.

Shaping should evaluate (a) against the past 20 issues' `skills_required` to measure true-positive loss before committing.

## Acceptance criteria

- [ ] ac-01: Shaped doc reports the per-issue diff (skills added/removed) for the chosen rule against issues 40-63.
- [ ] ac-02: No false positive of the type "DuckLake on a CLI fix" or "Nick Sleep on a CLI grouping issue" in the test corpus.
- [ ] ac-03: Unit test pins the new matching rule against a fixture issue with known expected matches.
- [ ] ac-04: `just check` passes.

## Blocked by

None.

## User stories addressed

- As a Mantle user running `update-skills`, I want only relevant skills selected so my compiled context is not bloated with unrelated domain knowledge.