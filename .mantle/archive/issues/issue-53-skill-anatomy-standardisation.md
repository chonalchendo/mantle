---
title: Skill anatomy standardisation — executable workflows with anti-rationalization
  guardrails
status: approved
slice:
- claude-code
- tests
story_count: 3
verification: null
blocked_by: []
skills_required:
- CLI design best practices
- Design Review
- Designing Architecture
- DuckDB Best Practices and Optimisations
- DuckLake
- Earnings Transcript Data Sources
- EarningsCall.biz Scraping
- FRED Data Source
- Finnhub Data Source
- Finviz Data Source
- Lakehouse Architecture
- Macrotrends Data Source
- Medallion Architecture & Star Schema
- Mohnish Pabrai Investment Philosophy
- OpenRouter LLM Gateway
- Playwright Web Scraping
- Production Project Readiness
- Python 3.14
- Python Project Conventions
- Python package structure
- SQLMesh Best Practices
- Software Design Principles
- Tom Gayner Investment Philosophy
- beautifulsoup4-web-scraping
- claude-sdk-structured-analysis-pipelines
- cyclopts
- docker-compose-python
- edgartools
- fastapi
- httpx-async
- omegaconf
- pydantic-discriminated-unions
- pydantic-project-conventions
- streamlit
- streamlit-aggrid
tags:
- type/issue
- status/approved
---

## Parent PRD

product-design.md, system-design.md

## Why

Current Mantle skills in the vault are dense knowledge dumps — they work for native Claude Code trigger-based loading (where the agent reads them as reference material) but won't be effective when injected into planning and implementation contexts (issue 52). Four scout reports (agent-skills, oh-my-claudecode, rowboat, colin) converge on the same finding: skills need to be executable workflows with guardrails, not passive reference docs.

The agent-skills repo demonstrates the target anatomy: trigger metadata, numbered workflow steps with gates, a Common Rationalizations table (preventing agents from skipping steps), red flags checklist, and a verification section requiring evidence. Progressive disclosure keeps the main skill file under ~150 lines with deeper detail in separate reference files loaded on-demand.

This is a prerequisite for issue 52 (skill injection) — injecting current-format skills into planning prompts adds bulk without improving agent behaviour.

## What to build

1. **Define the standard SKILL.md anatomy** — a documented template for vault skill files covering:
   - Trigger metadata (when to activate)
   - When to Use / When NOT to Use (scoping)
   - Numbered workflow steps with gates (executable process)
   - Common Rationalizations table (anti-skip guardrails)
   - Red Flags checklist (early warning signs)
   - Verification section (evidence-based exit criteria)

2. **Migrate 3-5 high-use skills** as proof of concept — restructure their vault source files to the new anatomy. Candidates: `python-project-conventions`, `cyclopts`, `software-design-principles`, `design-review`, `cli-design-best-practices`.

3. **Update `/mantle:add-skill` prompt** to generate skills in the new anatomy format.

4. **Progressive disclosure** — main SKILL.md under ~150 lines. Deeper detail (full API references, extended checklists) in separate reference files within the same vault skill directory, linked from the main file.

All changes target vault source files. The compile pipeline (`mantle compile`) renders them to `.claude/skills/*/SKILL.md` as before.

### Flow

1. Define the standard anatomy template and document it
2. Pick 3-5 high-use skills from the vault
3. Restructure each skill's vault source to the new anatomy
4. Run `mantle compile` to verify compiled output in `.claude/skills/` reflects the new structure
5. Update the `/mantle:add-skill` prompt to generate the new format
6. Verify all compiled skills load correctly via Claude Code's native trigger mechanism

## Acceptance criteria

- [ ] A standard SKILL.md anatomy is defined and documented (trigger, workflow steps, rationalizations table, red flags, verification)
- [ ] 3-5 high-use skills migrated to the new format in the vault, compiled output reflects new structure
- [ ] Migrated skills are under ~150 lines with deeper detail in separate reference files
- [ ] `/mantle:add-skill` prompt updated to generate skills in the new anatomy
- [ ] `just check` passes

## Blocked by

None

## User stories addressed

- As a developer using Mantle skills during planning, I want skills structured as executable workflows so that the AI follows a process with checkpoints rather than interpreting reference prose.
- As a developer creating new skills via `/mantle:add-skill`, I want the prompt to generate the standardised anatomy so that all skills are consistent and effective when injected into agent context.
- As a developer reviewing AI agent output, I want skills to include anti-rationalization guardrails so that agents don't skip required steps with plausible-sounding excuses.