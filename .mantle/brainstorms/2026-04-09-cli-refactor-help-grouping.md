---
date: '2026-04-09'
author: 110059232+chonalchendo@users.noreply.github.com
title: cli-refactor-help-grouping
verdict: proceed
tags:
- type/brainstorm
---

## Brainstorm Summary

**Idea**: Refactor the mantle CLI surface — reduce the flat 48-command footprint
**Problem**: `mantle --help` dumps 48 commands in a single flat list. Hard to scan, hard to navigate, no mental grouping. The CLI surface has grown unbounded.
**Vision alignment**: **Weak (as originally scoped) → Moderate (as scoped down)**

## Exploration

- **Pain point**: Navigation — flat 48-item `--help` is hard to scan.
- **Initial user proposal**: "Core commands customised with flags" (no subcommands). E.g. collapse the 22 `save-*` family into one polymorphic `mantle save --type X`.
- **Scope**: User initially said Large — "rethink the whole surface."

## Challenges Explored

### 1. Flag explosion (first-principles)

Inspected three `save-*` signatures and confirmed they share **zero common required flags**:
- `save-idea`: problem, insight, target-user, success-criteria
- `save-brainstorm`: title, verdict, content
- `save-story`: issue, title, content

A polymorphic `mantle save --type X` forces one of three bad designs:
- **Union of all flags** → 40-flag wall in `--help`, silent accept of wrong-type flags
- **Generic `--field key=val`** → zero type safety, worst discoverability, reinvents YAML frontmatter
- **Discriminated union at runtime** → literally a subcommand wearing a `--type` costume

User acknowledged: "Honestly, maybe subcommands were fine." The flag-explosion trade-off killed the original design shape.

### 2. Conflict with existing design principle #8

Product design principle #8 says: *"One command, one job — Each command does one focused thing to give the AI optimal context... No overloaded multi-purpose commands."* Written about slash commands but the reasoning applies to CLI commands too — an LLM constructing a `mantle save ...` bash invocation inside a prompt benefits from a focused signature over a polymorphic one.

### 3. Opportunity cost

Backlog has 4 live issues (41 query recurring patterns, 42 report-to-github, 46/47 bug fixes). Three add user-visible value. A full CLI refactor is pure internal rearrangement — no workflow gets faster, no bug gets fixed. Cheapest fix to the actual navigation pain: **Cyclopts `Group()` annotations** (~3 hours, zero breaking change).

## Approaches Considered

| Approach | Description | Trade-off | Appetite |
|---|---|---|---|
| A. Inline `group=` on decorators | Add `group="..."` kwarg to each `@app.command`. Cyclopts auto-buckets. | Simplest, scattered strings, typo risk | Small (~2h) |
| **B. Central `Group` registry** ⭐ | One `groups.py` with `Group` objects, imported and referenced. | Typo-safe, single source of truth. | Small (~3h) |
| C. Split CLI into grouped modules | Move command registrations to `cli/commands/<group>.py`. | Scope creep dressed as annotation. | Medium (~1d) |

## Verdict

**Verdict**: **proceed** — but radically scoped down from the original proposal.

**What to do**: Add Cyclopts help-panel grouping (Approach B) across existing commands. Taxonomy of ~8 groups: Setup, Idea & Validation, Design, Planning, Implementation, Review & Verification, Capture, Knowledge. No command renames. No breaking changes. Zero prompt touches.

**What NOT to do**: Do NOT pursue the "core verbs + flags" shape. It violates principle #8 and forces a bad flag design. Do NOT do a full subcommand refactor right now — park it in the inbox and revisit only if help-grouping fails to solve the navigation pain.

**Priority**: Lower than issues 41 and 42 (which advance the knowledge engine and dogfooding). Schedule the help-grouping work as a small issue that can be slotted between 41 and 42.

**Reasoning**: The brainstorm worked as intended. The stated pain (navigation) is real, but the originally proposed fix (polymorphic commands with flags) had a first-principles flaw (flag explosion) and conflicted with an existing design principle. The cheapest fix addresses 100% of the stated pain with ~3 hours of work and zero risk.