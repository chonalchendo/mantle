# Mantle token audit — 2026-04-22

Measured with tiktoken (encoding: cl100k_base, ~97% Claude BPE proxy).

## Before

### mantle

| Rank | File | Tokens | % of total |
| ---- | ---- | ------:| ----------:|
| 1 | build | 4,112 | 8.2% |
| 2 | implement | 2,935 | 5.8% |
| 3 | scout | 2,837 | 5.6% |
| 4 | verify | 2,815 | 5.6% |
| 5 | plan-stories | 2,535 | 5.0% |
| 6 | shape-issue | 2,384 | 4.7% |
| 7 | design-system | 2,378 | 4.7% |
| 8 | brainstorm | 2,298 | 4.6% |
| 9 | add-skill | 2,276 | 4.5% |
| 10 | research | 2,276 | 4.5% |
| 11 | design-product | 2,080 | 4.1% |
| 12 | adopt | 2,062 | 4.1% |
| 13 | plan-issues | 2,036 | 4.1% |
| 14 | refactor | 1,842 | 3.7% |
| 15 | review | 1,824 | 3.6% |
| 16 | challenge | 1,754 | 3.5% |
| 17 | simplify | 1,665 | 3.3% |
| 18 | add-issue | 1,568 | 3.1% |
| 19 | fix | 1,345 | 2.7% |
| 20 | retrospective | 1,097 | 2.2% |
| 21 | revise-product | 987 | 2.0% |
| 22 | revise-system | 949 | 1.9% |
| 23 | idea | 896 | 1.8% |
| 24 | query | 836 | 1.7% |
| 25 | bug | 830 | 1.7% |
| 26 | distill | 770 | 1.5% |
| 27 | help | 513 | 1.0% |
| 28 | patterns | 183 | 0.4% |
| 29 | inbox | 159 | 0.3% |

**Total (mantle):** 50,242 tokens across 29 file(s).

**Top 3 candidates for rewrite (mantle):** build.md, implement.md, scout.md

### skills

| Rank | File | Tokens | % of total |
| ---- | ---- | ------:| ----------:|
| 1 | john-templeton-investment-philosophy | 4,496 | 4.7% |
| 2 | howard-marks-investment-philosophy | 3,882 | 4.1% |
| 3 | import-linter | 3,609 | 3.8% |
| 4 | nick-sleep-investment-philosophy | 3,555 | 3.7% |
| 5 | openrouter-llm-gateway | 3,533 | 3.7% |
| 6 | ducklake | 3,040 | 3.2% |
| 7 | medallion-architecture--star-schema | 2,989 | 3.1% |
| 8 | dirty-equals | 2,875 | 3.0% |
| 9 | tailwind-css-v4 | 2,791 | 2.9% |
| 10 | mohnish-pabrai-investment-philosophy | 2,767 | 2.9% |
| 11 | software-design-principles | 2,536 | 2.6% |
| 12 | claude-sdk-structured-analysis-pipelines | 2,529 | 2.6% |
| 13 | lakehouse-architecture | 2,516 | 2.6% |
| 14 | sqlmesh-best-practices | 2,507 | 2.6% |
| 15 | pydantic-discriminated-unions | 2,480 | 2.6% |
| 16 | inline-snapshot | 2,397 | 2.5% |
| 17 | openapi-typescript--openapi-fetch | 2,241 | 2.3% |
| 18 | beautifulsoup4-web-scraping | 2,184 | 2.3% |
| 19 | shadcn-svelte | 2,181 | 2.3% |
| 20 | cyclopts | 2,121 | 2.2% |
| 21 | sveltekit-2--svelte-5 | 2,116 | 2.2% |
| 22 | production-project-readiness | 2,114 | 2.2% |
| 23 | httpx-async | 2,006 | 2.1% |
| 24 | design-review | 1,961 | 2.0% |
| 25 | tom-gayner-investment-philosophy | 1,945 | 2.0% |
| 26 | omegaconf | 1,913 | 2.0% |
| 27 | docker-compose-python | 1,822 | 1.9% |
| 28 | python-project-conventions | 1,795 | 1.9% |
| 29 | earnings-transcript-data-sources | 1,713 | 1.8% |
| 30 | python-314 | 1,684 | 1.8% |
| 31 | macrotrends-data-source | 1,629 | 1.7% |
| 32 | duckdb-best-practices-and-optimisations | 1,592 | 1.7% |
| 33 | fred-data-source | 1,525 | 1.6% |
| 34 | finnhub-data-source | 1,475 | 1.5% |
| 35 | playwright-web-scraping | 1,372 | 1.4% |
| 36 | finviz-data-source | 1,291 | 1.3% |
| 37 | earningscallbiz-scraping | 1,262 | 1.3% |
| 38 | designing-architecture | 1,253 | 1.3% |
| 39 | cli-design-best-practices | 1,209 | 1.3% |
| 40 | edgartools | 1,108 | 1.2% |
| 41 | streamlit | 1,081 | 1.1% |
| 42 | fastapi | 1,052 | 1.1% |
| 43 | streamlit-aggrid | 982 | 1.0% |
| 44 | python-package-structure | 938 | 1.0% |
| 45 | pydantic-project-conventions | 858 | 0.9% |
| 46 | apache-iceberg-table-management | 825 | 0.9% |

**Total (skills):** 95,750 tokens across 46 file(s).

**Top 3 candidates for rewrite (skills):** john-templeton-investment-philosophy.md, howard-marks-investment-philosophy.md, import-linter.md

**Total (all surfaces):** 145,992 tokens across 75 files.

## After

### mantle

| Rank | File | Before | After | Saved | % saved |
| ---- | ---- | ------:| -----:| -----:| -------:|
| 1 | build | 4,112 | 3,343 | 769 | 18.7% |
| 2 | verify | 2,815 | 2,919 | -104 | -3.7% |
| 3 | plan-stories | 2,535 | 2,609 | -74 | -2.9% |
| 4 | shape-issue | 2,384 | 2,474 | -90 | -3.8% |
| 5 | design-system | 2,378 | 2,456 | -78 | -3.3% |
| 6 | brainstorm | 2,298 | 2,395 | -97 | -4.2% |
| 7 | research | 2,276 | 2,367 | -91 | -4.0% |
| 8 | add-skill | 2,276 | 2,356 | -80 | -3.5% |
| 9 | design-product | 2,080 | 2,190 | -110 | -5.3% |
| 10 | adopt | 2,062 | 2,157 | -95 | -4.6% |
| 11 | plan-issues | 2,036 | 2,121 | -85 | -4.2% |
| 12 | implement | 2,935 | 1,972 | 963 | 32.8% |
| 13 | refactor | 1,842 | 1,935 | -93 | -5.0% |
| 14 | review | 1,824 | 1,919 | -95 | -5.2% |
| 15 | challenge | 1,754 | 1,860 | -106 | -6.0% |
| 16 | scout | 2,837 | 1,800 | 1,037 | 36.6% |
| 17 | simplify | 1,665 | 1,750 | -85 | -5.1% |
| 18 | add-issue | 1,568 | 1,650 | -82 | -5.2% |
| 19 | fix | 1,345 | 1,440 | -95 | -7.1% |
| 20 | retrospective | 1,097 | 1,203 | -106 | -9.7% |
| 21 | revise-product | 987 | 1,063 | -76 | -7.7% |
| 22 | revise-system | 949 | 1,025 | -76 | -8.0% |
| 23 | idea | 896 | 994 | -98 | -10.9% |
| 24 | query | 836 | 945 | -109 | -13.0% |
| 25 | distill | 770 | 846 | -76 | -9.9% |
| 26 | bug | 830 | 830 | 0 | 0.0% |
| 27 | help | 513 | 513 | 0 | 0.0% |
| 28 | patterns | 183 | 316 | -133 | -72.7% |
| 29 | inbox | 159 | 159 | 0 | 0.0% |

### skills

| Rank | File | Before | After | Saved | % saved |
| ---- | ---- | ------:| -----:| -----:| -------:|
| 1 | nick-sleep-investment-philosophy | 3,555 | 3,555 | 0 | 0.0% |
| 2 | openrouter-llm-gateway | 3,533 | 3,533 | 0 | 0.0% |
| 3 | ducklake | 3,040 | 3,040 | 0 | 0.0% |
| 4 | medallion-architecture--star-schema | 2,989 | 2,989 | 0 | 0.0% |
| 5 | john-templeton-investment-philosophy | 4,496 | 2,885 | 1,611 | 35.8% |
| 6 | dirty-equals | 2,875 | 2,875 | 0 | 0.0% |
| 7 | howard-marks-investment-philosophy | 3,882 | 2,793 | 1,089 | 28.1% |
| 8 | tailwind-css-v4 | 2,791 | 2,791 | 0 | 0.0% |
| 9 | mohnish-pabrai-investment-philosophy | 2,767 | 2,767 | 0 | 0.0% |
| 10 | import-linter | 3,609 | 2,718 | 891 | 24.7% |
| 11 | software-design-principles | 2,536 | 2,536 | 0 | 0.0% |
| 12 | claude-sdk-structured-analysis-pipelines | 2,529 | 2,529 | 0 | 0.0% |
| 13 | lakehouse-architecture | 2,516 | 2,516 | 0 | 0.0% |
| 14 | sqlmesh-best-practices | 2,507 | 2,507 | 0 | 0.0% |
| 15 | pydantic-discriminated-unions | 2,480 | 2,480 | 0 | 0.0% |
| 16 | inline-snapshot | 2,397 | 2,397 | 0 | 0.0% |
| 17 | openapi-typescript--openapi-fetch | 2,241 | 2,241 | 0 | 0.0% |
| 18 | beautifulsoup4-web-scraping | 2,184 | 2,184 | 0 | 0.0% |
| 19 | shadcn-svelte | 2,181 | 2,181 | 0 | 0.0% |
| 20 | cyclopts | 2,121 | 2,121 | 0 | 0.0% |
| 21 | sveltekit-2--svelte-5 | 2,116 | 2,116 | 0 | 0.0% |
| 22 | production-project-readiness | 2,114 | 2,114 | 0 | 0.0% |
| 23 | httpx-async | 2,006 | 2,006 | 0 | 0.0% |
| 24 | design-review | 1,961 | 1,961 | 0 | 0.0% |
| 25 | tom-gayner-investment-philosophy | 1,945 | 1,945 | 0 | 0.0% |
| 26 | omegaconf | 1,913 | 1,913 | 0 | 0.0% |
| 27 | docker-compose-python | 1,822 | 1,822 | 0 | 0.0% |
| 28 | python-project-conventions | 1,795 | 1,795 | 0 | 0.0% |
| 29 | earnings-transcript-data-sources | 1,713 | 1,713 | 0 | 0.0% |
| 30 | python-314 | 1,684 | 1,684 | 0 | 0.0% |
| 31 | macrotrends-data-source | 1,629 | 1,629 | 0 | 0.0% |
| 32 | duckdb-best-practices-and-optimisations | 1,592 | 1,592 | 0 | 0.0% |
| 33 | fred-data-source | 1,525 | 1,525 | 0 | 0.0% |
| 34 | finnhub-data-source | 1,475 | 1,475 | 0 | 0.0% |
| 35 | playwright-web-scraping | 1,372 | 1,372 | 0 | 0.0% |
| 36 | finviz-data-source | 1,291 | 1,291 | 0 | 0.0% |
| 37 | earningscallbiz-scraping | 1,262 | 1,262 | 0 | 0.0% |
| 38 | designing-architecture | 1,253 | 1,253 | 0 | 0.0% |
| 39 | cli-design-best-practices | 1,209 | 1,209 | 0 | 0.0% |
| 40 | edgartools | 1,108 | 1,108 | 0 | 0.0% |
| 41 | streamlit | 1,081 | 1,081 | 0 | 0.0% |
| 42 | fastapi | 1,052 | 1,052 | 0 | 0.0% |
| 43 | streamlit-aggrid | 982 | 982 | 0 | 0.0% |
| 44 | python-package-structure | 938 | 938 | 0 | 0.0% |
| 45 | pydantic-project-conventions | 858 | 858 | 0 | 0.0% |
| 46 | apache-iceberg-table-management | 825 | 825 | 0 | 0.0% |

## Delta summary

- **mantle**: top-3 saved 591 tokens (6.2%), total saved 635 tokens (1.3% reduction).
- **skills**: top-3 saved 0 tokens (0.0%), total saved 3,591 tokens (3.8% reduction).
- **Overall:** 4,226 tokens saved (2.9% reduction).
