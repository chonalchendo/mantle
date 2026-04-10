---
title: Rethink tag naming conventions for meaningful vault indexes
status: verified
slice:
- claude-code
- core
- cli
- tests
story_count: 2
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
- status/verified
---

## Parent PRD

product-design.md, system-design.md

## Why

Tags generated during skill authoring are too specific — they mirror the skill name verbatim (e.g. `topic-dbt-incremental`, `topic-dbt-schema-testing`) instead of creating meaningful clusters. This defeats the purpose of indexes: two dbt skills should share one `dbt` topic, not create separate near-empty indexes. Coarser-grained tags produce useful cross-references; overly-specific tags produce noise.

## What to build

Revise how tags are chosen during skill authoring so they use coarse-grained topic names that cluster related skills. Migrate existing vault tags to the new convention. Document the naming rules so future skills follow them automatically.

### Flow

1. Define a tag naming convention: tags should represent broad topics (e.g. `dbt`, `scraping`, `investment-philosophy`) rather than restating the skill title
2. Update the skill-authoring and add-skill prompts to include the convention as guidance for tag selection
3. Add a CLI migration command (or script) that renames overly-specific tags in existing vault notes to the new coarser convention
4. After migration, verify that vault indexes group related skills under shared topic headings

## Acceptance criteria

- [ ] Tags use coarse-grained topic names (e.g. `dbt` not `dbt-incremental`) — related skills share one topic tag
- [ ] Existing overly-specific tags are migrated to the new convention
- [ ] Tag naming convention is documented in the skill-authoring and/or add-skill prompt
- [ ] Vault indexes reflect the new tags — related skills are grouped under shared topics instead of 1:1 skill-to-index mappings

## Blocked by

None

## User stories addressed

- As a mantle user, I want vault tags to create meaningful topic clusters so that indexes help me discover related skills instead of duplicating skill names
- As a skill author, I want clear guidance on tag granularity so that I choose useful topic names without overthinking