---
title: Cross-repo project context and cross-project initiative tagging
status: planned
slice:
- core
- cli
- tests
story_count: 0
verification: null
blocked_by: []
skills_required: []
tags:
- type/issue
- status/planned
acceptance_criteria:
- id: ac-01
  text: A shaped issue document exists exploring 2–3 approaches to cross-repo initiative
    identity, with tradeoffs.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: The chosen approach is decomposed into stories so implementation can proceed
    in vertical slices.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: At minimum, issues can be tagged with an initiative identifier that works
    consistently across repos (the lightweight primitive).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: A list/query path exists to find all issues across repos carrying the same
    initiative tag.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

At work, initiatives routinely cut across multiple repos (dbt, workflows, unitycatalog/terraform, AWS compute/landing/datalake). Today each repo's `.mantle/` is an island: context, learnings, and issue history don't cross the boundary, so agents working on repo B can't see what repo A already decided, and a single initiative that spans three repos fractures into three disconnected issue lists.

Two inbox items converge on one feature shape — a coarse-grained initiative identity that links related work across repos — so they're shaped together rather than built twice:

1. **Cross-repo project context** — let a mantle project span multiple repos, sharing context efficiently when work cuts across boundaries.
2. **Cross-project tagging** — tag issues that belong to a larger initiative so related work in separate mantle projects can be discovered and tracked together.

The second is the lightweight primitive; the first is the richer feature built on top.

## What to build

This is shape-phase work; the goal here is to frame the problem, not pre-commit to a mechanism. Expected directions to evaluate in /mantle:shape-issue:

- A named "initiative" identifier that repos opt into (e.g. in config.md), with list/search commands that query across opted-in repos.
- A global index (under `~/.mantle/` or similar) that maps initiative → member repos → their issue/learning files.
- Shared learnings surface: an agent on repo B can see decisions logged for the same initiative on repo A.

Open questions to work through at shape time:

- Does the global storage mode (issue 43/44) already provide a natural home for cross-repo indexes, or does this need a new layer?
- Is "initiative" a first-class entity with a design doc, or just a tag?
- What's the minimum viable surface — tag-only first, then layer cross-repo queries — versus a full cross-repo product design?

## Acceptance criteria

- [ ] ac-01: A shaped issue document exists exploring 2–3 approaches to cross-repo initiative identity, with tradeoffs.
- [ ] ac-02: The chosen approach is decomposed into stories so implementation can proceed in vertical slices.
- [ ] ac-03: At minimum, issues can be tagged with an initiative identifier that works consistently across repos (the lightweight primitive).
- [ ] ac-04: A list/query path exists to find all issues across repos carrying the same initiative tag.
- [ ] ac-05: `just check` passes.

## Blocked by

- Interacts with global storage mode (issues 43/44) — ensure the cross-repo feature composes with global storage rather than duplicating it.

## User stories addressed

- As a mantle user working across multiple work repos, I want to tag issues as part of a shared initiative so I can see all related work in one place.
- As a mantle user asking an agent to implement something in repo B, I want it to see decisions already logged for the same initiative in repo A so it doesn't re-derive or contradict them.
- As a maintainer, I want initiative identity to be a thin, composable primitive rather than a parallel project system.

## Source inbox items

- `2026-04-09-cross-repomulti-repo-project-c.md`
- `2026-04-20-cross-project-tagging-for-issu.md`