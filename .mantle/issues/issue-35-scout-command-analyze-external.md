---
title: Scout command — analyze external repos through project context lens
status: approved
slice:
- core
- cli
- claude-code
- tests
story_count: 3
verification: null
blocked_by: []
tags:
- type/issue
- status/approved
---

## Parent PRD

product-design.md, system-design.md

## Why

Users frequently clone external GitHub repos to learn from them, but ad hoc analysis prompts miss the rich context Mantle already has (product design, system design, backlog, skills, learnings). This means generic observations instead of targeted insights aligned with the projects vision and current gaps. The scout command formalizes a common workflow — clone, analyze, report — and makes it significantly more useful by injecting compiled project context as the analysis lens.

## What to build

A `/mantle:scout` command that clones an external GitHub repo, analyzes it through the lens of the current projects product and system design, and saves a structured report to `.mantle/scouts/`.

### Flow

1. User runs `/mantle:scout <repo-url>`
2. Prompt orchestrator compiles project context: product design, system design, current backlog, learnings, skills
3. CLI clones the repo to a temp directory via `mantle scout <repo-url>`
4. Parallel agents analyze the repo across dimensions: architecture, patterns/conventions, testing approach, CLI design, and any domain-specific dimensions relevant to the project
5. Each agent receives the compiled project context as its analysis lens — "what in this repo is relevant to our project?"
6. Results are synthesized into a structured report with actionable recommendations tied to specific backlog gaps or design opportunities
7. Report is saved to `.mantle/scouts/` via `mantle save-scout` with YAML frontmatter (repo URL, date, author, tags)
8. Temp clone is cleaned up

## Acceptance criteria

- [ ] `mantle scout <repo-url>` clones the repo to a temp directory and cleans up after analysis
- [ ] Analysis is guided by compiled project context (product design, system design, backlog, learnings)
- [ ] Parallel agents analyze across multiple dimensions (architecture, patterns, testing, CLI design)
- [ ] Structured report saved to `.mantle/scouts/` with YAML frontmatter and queryable by `/mantle:query`
- [ ] Report includes actionable recommendations tied to specific backlog gaps or design opportunities

## Brainstorm reference

.mantle/brainstorms/2026-04-06-scout-command-external-repo-analysis.md

## Blocked by

None

## User stories addressed

- As a developer, I want to run `/mantle:scout <repo-url>` and have the AI analyze an external repo through the lens of my projects product vision and system design, so that I get targeted insights rather than generic observations.
- As a developer, I want scout reports persisted in `.mantle/scouts/` with structured metadata, so that findings are preserved and can inform future planning.
- As a developer, I want the analysis to surface actionable recommendations tied to my current backlog gaps, so that I know what is worth porting and why.