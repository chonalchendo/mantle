---
title: Plug external skill libraries from GitHub repos into the vault
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
  text: A CLI exists to register a GitHub-hosted skill source (URL + optional branch
    + optional subdir).
  passes: false
  waived: false
  waiver_reason: null
- id: ac-02
  text: A refresh path clones/pulls registered sources into a local cache and links
    their skills into the vault's skill index.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-03
  text: Linked external skills are returned by skill listing/matching identically
    to local skills, with provenance (source, branch, commit) visible.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-04
  text: A name collision between two sources produces a clear error rather than silent
    override.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-05
  text: A test covers the end-to-end flow using a fixture git repo.
  passes: false
  waived: false
  waiver_reason: null
- id: ac-06
  text: '`just check` passes.'
  passes: false
  waived: false
  waiver_reason: null
---

## Parent PRD

product-design.md, system-design.md

## Why

Mantle's skill graph today is vault-local. At work there's a shared team library of Claude skills I want to integrate alongside my personal vault, and community skill repos (Anthropic skills, Matt Pocock skills, etc.) are worth pulling in rather than forking-and-drifting. Need a way to plug external skill libraries from a GitHub repo into the vault, refresh them periodically, and have the auto-matcher and compile step treat them as first-class skills.

## What to build

A skill-source registration mechanism, probably:

- `mantle skill-source add <git-url> [--branch X] [--subdir path]` to register a remote source.
- A fetch/refresh command (or a SessionStart / periodic hook) that clones or pulls the sources into a cache under `~/.mantle/` and links the skill files into the vault's skill index.
- Compile and auto-matcher treat linked skills identically to local ones, with provenance recorded so the source (local vs. external repo / branch / commit) is visible.
- Conflict handling when two sources define a skill with the same name — at minimum a clear error; ideally a namespacing convention.

Keep scope tight: read-only consumption of external sources. No bidirectional sync. No editing of external skills in place — edits require forking.

## Acceptance criteria

- [ ] ac-01: A CLI exists to register a GitHub-hosted skill source (URL + optional branch + optional subdir).
- [ ] ac-02: A refresh path clones/pulls registered sources into a local cache and links their skills into the vault's skill index.
- [ ] ac-03: Linked external skills are returned by skill listing/matching identically to local skills, with provenance (source, branch, commit) visible.
- [ ] ac-04: A name collision between two sources produces a clear error rather than silent override.
- [ ] ac-05: A test covers the end-to-end flow using a fixture git repo.
- [ ] ac-06: `just check` passes.

## Blocked by

None

## User stories addressed

- As a mantle user at work, I want my personal vault to pick up skills from the team's shared GitHub repo so I don't have to re-author them.
- As a mantle user, I want to try community skill libraries without forking them manually.
- As a maintainer, I want external skills to be recognisably external (provenance visible) so audits and conflicts are easy to reason about.