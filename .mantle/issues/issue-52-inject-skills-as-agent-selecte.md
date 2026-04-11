---
title: Inject skills as agent-selected context into shaping and story planning
status: planned
slice:
- claude-code
- tests
story_count: 0
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- Designing Architecture
- DuckDB Best Practices and Optimisations
- OpenRouter LLM Gateway
- Production Project Readiness
- Python package structure
- SQLMesh Best Practices
- claude-sdk-structured-analysis-pipelines
- cyclopts
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
- streamlit
- streamlit-aggrid
tags:
- type/issue
- status/planned
---

## Parent PRD

product-design.md, system-design.md

## Why

Skills are compiled to .claude/skills/ for native Claude Code loading, but the shape-issue and plan-stories prompts don't instruct the agent to discover and leverage relevant domain knowledge during planning. The AI shapes approaches and decomposes stories without explicitly consulting the skill graph — missing domain patterns, conventions, and lessons that could improve planning quality. When a skill gap exists, there's no prompt-level mechanism to fill it before proceeding.

## What to build

Update shape-issue and plan-stories prompts to instruct the agent to discover, select, and leverage relevant skills — and fill gaps by creating new skills when needed.

1. **Skill discovery step in prompts** — shape-issue.md and plan-stories.md instruct the agent to run `mantle list-skills` to discover available skills relevant to the current issue.
2. **Agent-driven selection** — the agent selects which skills are applicable based on the issue's domain and technology requirements.
3. **Gap-filling** — if the agent identifies a skill gap (needed domain knowledge not in the graph), it creates the skill via `/mantle:add-skill` before proceeding.
4. **Story-level skill tagging** — selected skills are recorded in each story's metadata (e.g., `skills: [cyclopts, cli-design-best-practices]`) so the story implementer agent naturally triggers those skills via Claude Code's native loading.

### Flow

1. User runs `/mantle:shape-issue` or `/mantle:plan-stories` for an issue
2. Agent runs `mantle list-skills` to discover available skills
3. Agent selects relevant skills for the issue's domain
4. If a skill gap is identified, agent runs `/mantle:add-skill` to create it
5. Agent proceeds with shaping/planning, informed by skill content
6. Each story includes a `skills` field listing relevant skill names
7. When `/mantle:implement` runs, story implementer agents naturally trigger those skills via Claude Code's native skill loading mechanism

## Acceptance criteria

- [ ] shape-issue and plan-stories prompts instruct the agent to discover relevant skills via `mantle list-skills`
- [ ] Agent selects applicable skills and can create missing ones via `/mantle:add-skill` during the session
- [ ] Selected skill content is recorded in each story's metadata via a `skills` field
- [ ] A story implemented with skill references naturally triggers those skills via Claude Code's native loading
- [ ] `just check` passes

## Blocked by

None

## User stories addressed

- As a developer shaping an issue, I want the AI to automatically discover and leverage relevant domain skills so that approaches are informed by accumulated project knowledge.
- As a developer planning stories, I want each story tagged with relevant skills so that the story implementer agent has the right domain context loaded automatically.
- As a developer working in a new domain area, I want the AI to identify and fill skill gaps during planning so that implementation has the knowledge it needs from the start.