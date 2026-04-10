---
issue: 49
title: Migrate existing vault skill tags to coarser conventions
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a mantle user, I want vault tags to create meaningful topic clusters so that indexes help me discover related skills instead of duplicating skill names.

## Depends On

Story 1 — the migration follows the naming rules defined in the prompt rewrite.

## Approach

Update the frontmatter tags in existing vault skill files to use coarser-grained topic/ and domain/ tags. This is a manual content migration across 35 vault skill files. After updating frontmatter, run \`mantle compile\` to regenerate index notes reflecting the new tag groupings.

## Implementation

### /Users/conal/test-vault/skills/*.md (modify — 10 files need tag changes)

**Topic tag migrations** — update the \`tags:\` frontmatter section in each file:

| Skill file | Old tag | New tag |
|---|---|---|
| earningscallbiz-scraping.md | topic/earningscall-biz-scraping | topic/scraping |
| macrotrends-data-source.md | topic/macrotrends-scraping | topic/scraping |
| playwright-web-scraping.md | topic/playwright-web-scraping | topic/scraping |
| streamlit-aggrid.md | topic/streamlit-aggrid | topic/streamlit |
| pydantic-discriminated-unions.md | topic/pydantic-discriminated-unions | topic/pydantic |

**Domain tag migrations** — update domain/ tags for consistency:

| Skill file | Old tag | New tag |
|---|---|---|
| earningscallbiz-scraping.md | domain/scraping | domain/web |
| beautifulsoup4-web-scraping.md | (already domain/web) | (no change) |
| earnings-transcript-data-sources.md | (already domain/financial-data) | domain/finance |
| finnhub-data-source.md | (already domain/financial-data) | domain/finance |
| finviz-data-source.md | (already domain/financial-data) | domain/finance |
| fred-data-source.md | (already domain/financial-data) | domain/finance |
| macrotrends-data-source.md | domain/financial-data | domain/finance |
| mohnish-pabrai-investment-philosophy.md | domain/qualitative-analysis | domain/finance |
| tom-gayner-investment-philosophy.md | domain/qualitative-analysis | domain/finance |
| omegaconf.md | domain/config-management | domain/python |
| pydantic-project-conventions.md | domain/finance | domain/python |

After all frontmatter updates:

1. Run \`mantle compile\` to regenerate compiled skills and index notes
2. Run \`mantle list-tags\` to verify the new tag landscape shows fewer, broader tags

#### Design decisions

- **Merge domain/financial-data into domain/finance**: financial-data is a subset of finance; one broader tag is more useful for clustering.
- **Merge domain/scraping into domain/web**: scraping is a technique within the web domain, not a separate discipline.
- **Merge domain/qualitative-analysis into domain/finance**: investment philosophy skills belong in the finance domain.
- **Merge domain/config-management into domain/python**: omegaconf is a Python config library, belongs with Python tooling.
- **Fix pydantic-project-conventions domain**: was incorrectly tagged domain/finance, should be domain/python.

## Tests

No Python code changes — this is a vault content migration. Verification will check that:
- \`mantle list-tags\` shows fewer, coarser tags
- Related skills share topic tags (e.g., 3 scraping skills all have topic/scraping)
- No overly-specific topic tags remain