---
title: Project adoption command (/mantle:adopt)
status: planned
slice: [core, claude-code, agents, vault, tests]
story_count: 0
verification: null
tags:
  - type/issue
  - status/planned
---

## Parent PRD

product-design.md, system-design.md

## What to build

The `/mantle:adopt` Claude Code command that onboards an existing project into Mantle by analyzing the codebase, researching its domain landscape, and generating planning artifacts reverse-engineered from what already exists. This is the counterpart to the greenfield workflow (`/mantle:idea` through `/mantle:design-system`) — it bridges an already-built project into Mantle's structured workflow so the user can start planning issues and stories immediately.

`mantle init` creates the `.mantle/` directory and state machine. `/mantle:adopt` populates it with inferred context.

After adoption completes, the user has a populated `.mantle/` with product design, system design, and decision log entries — enough context for `/mantle:plan-issues` and `/mantle:plan-stories` to work effectively.

This includes:

- `claude/commands/mantle/adopt.md` — static command prompt that orchestrates the adoption workflow as an interactive session
- `claude/agents/codebase-analyst.md` — subagent that explores the codebase (architecture, dependencies, module boundaries, tech stack, config, CI/CD, existing docs)
- `claude/agents/domain-researcher.md` — subagent that researches the project's domain landscape (ecosystem, competitors, relevant standards, community patterns)
- `src/mantle/core/adopt.py` — adoption orchestration: artifact generation, state updates, directory setup
- State machine update: add `ADOPTED` status with transition `INIT → ADOPTED`, and transitions from ADOPTED to planning phases (same as from SYSTEM_DESIGN)

### Adoption phases

#### Phase 1: Codebase analysis (parallel agents)

Two subagents run concurrently:

**Codebase analyst** — explores what exists:
- Architecture and module boundaries
- Dependency graph and tech stack
- Existing documentation (READMEs, ADRs, inline docs, TODO/FIXME comments)
- CI/CD configuration and deployment targets
- Test coverage and testing patterns
- Configuration and environment setup

**Domain researcher** — explores the landscape:
- What ecosystem is this project in?
- Existing solutions and competitors in the space
- Relevant standards, protocols, or community conventions
- Dependency health (outdated deps, known vulnerabilities, maintenance status)

#### Phase 2: Interactive synthesis

The AI presents findings to the user and works through an interactive session:

1. **Architecture summary** — "Here's what I found. Does this match your understanding?" The user corrects misconceptions, fills in intent that isn't visible in code.
2. **Product design draft** — Inferred product-design.md: what does this project do, who is it for, what are its features, what's the genuine edge? The user refines.
3. **System design draft** — Inferred system-design.md: architecture, tech choices with rationale, API contracts, data model. Each decision logged with alternatives and confidence. The user refines.
4. **Considerations** — Optional observations clearly marked as "things to consider, not prescriptions": architectural patterns that could simplify things, dependencies that could be consolidated, testing gaps, documentation gaps. The user decides what to act on.

#### Phase 3: Artifact generation

Based on the interactive session, generate:
- `.mantle/product-design.md` — reverse-engineered product design
- `.mantle/system-design.md` — reverse-engineered system design
- `.mantle/decisions/` — initial decision log entries for key architectural choices already made
- State update to `ADOPTED`

### Design principles for adopt

- **Extract, don't prescribe** — The goal is to codify what already exists, not to redesign the project. The "considerations" section is clearly separated from the factual analysis.
- **Interactive, not dump-and-run** — Present findings incrementally. Let the user correct, refine, and fill gaps. The user knows their project better than any agent.
- **Honest about confidence** — Mark inferred sections with confidence levels. "I'm 90% sure this is a REST API" vs "I'm guessing this module handles auth based on the name."
- **Respect existing choices** — The user chose their stack for reasons. Considerations are framed as options, not criticism.

## Acceptance criteria

- [ ] `/mantle:adopt` is available in Claude Code and starts the adoption workflow
- [ ] `mantle init` must be run first (`.mantle/` directory exists) — adopt populates it, doesn't create it
- [ ] Codebase analyst subagent explores architecture, dependencies, tech stack, existing docs, CI/CD, and test patterns
- [ ] Domain researcher subagent investigates ecosystem, competitors, relevant standards, and dependency health
- [ ] Both agents run concurrently during Phase 1 for efficiency
- [ ] Phase 2 is interactive — the AI presents findings and the user refines before artifacts are generated
- [ ] Product design document generated at `.mantle/product-design.md` with the same schema as `/mantle:design-product` output
- [ ] System design document generated at `.mantle/system-design.md` with the same schema as `/mantle:design-system` output
- [ ] Initial decision log entries created in `.mantle/decisions/` for key architectural choices visible in the codebase
- [ ] Each decision log entry includes rationale (inferred), alternatives, confidence, and reversal cost
- [ ] Considerations section is clearly marked as optional and non-prescriptive
- [ ] State machine updated: `ADOPTED` status with transitions to planning phases
- [ ] Running `/mantle:adopt` when design docs already exist warns the user and asks for confirmation
- [ ] After adoption, `/mantle:plan-issues` and `/mantle:plan-stories` work against the generated artifacts
- [ ] Agent definitions installed to `~/.claude/agents/` via `mantle install`
- [ ] `/mantle:help` updated to include `/mantle:adopt` in the "Setup & Onboarding" phase group
- [ ] Tests verify artifact generation, state transitions, and schema compliance

## Blocked by

- Blocked by issue-02 (needs `.mantle/` directory, vault.py, and state.py)
- Should be implemented after issue-05 and issue-06 (product design and system design) since adopt generates the same artifact schemas

## User stories addressed

_New user stories (not in original PRD — extends onboarding for existing projects):_

- As a developer with an existing project, I want to run `/mantle:adopt` and have AI agents analyze my codebase and research my project's domain, so that I can onboard into Mantle's workflow without manually writing product and system design documents from scratch.
- As a developer with an existing project, I want the adoption process to be interactive — presenting findings for me to correct and refine — so that the generated artifacts reflect my actual intent, not just what the code implies.
- As a developer with an existing project, I want reverse-engineered product and system design documents that follow the same schema as Mantle's design commands, so that planning commands (`/mantle:plan-issues`, `/mantle:plan-stories`) work immediately after adoption.
- As a developer with an existing project, I want key architectural decisions already visible in my codebase to be logged automatically in `.mantle/decisions/` with inferred rationale, so that I have a decision history even for choices made before adopting Mantle.
- As a developer with an existing project, I want optional, non-prescriptive observations about potential improvements, so that I'm aware of opportunities without feeling judged for past decisions.
