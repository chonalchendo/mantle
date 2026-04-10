---
issue: 49
title: Rewrite add-skill step 6 with taxonomy-aware tag guidance
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a skill author, I want clear guidance on tag granularity so that I choose useful coarse-grained topic names without overthinking.

## Depends On

None — independent.

## Approach

Rewrite Step 6 in \`claude/commands/mantle/add-skill.md\` to make the LLM taxonomy-aware. The current guidance says "one tag matching the skill's subject" which produces 1:1 mappings like \`topic/dbt-incremental\`. The new guidance instructs the LLM to check existing tags first, prefer reuse over creation, and use coarse-grained names for both \`topic/\` and \`domain/\` prefixes. Include explicit good/bad examples.

## Implementation

### claude/commands/mantle/add-skill.md (modify)

Replace the existing Step 6 section (lines 207-225) with taxonomy-aware guidance:

1. **Read existing tags first** — check \`\$MANTLE_DIR/tags.md\` and run \`mantle list-tags\` to see the full taxonomy before suggesting anything.

2. **Reuse rule** — if an existing tag covers the skill's subject area, reuse it. Do not create a new tag that is a more specific variant of an existing one.

3. **Coarse-grained topic/ rules:**
   - Topic tags represent broad subjects that cluster multiple related skills
   - Good: \`topic/scraping\`, \`topic/pydantic\`, \`topic/streamlit\`, \`topic/duckdb\`
   - Bad: \`topic/playwright-web-scraping\`, \`topic/pydantic-discriminated-unions\`, \`topic/streamlit-aggrid\`, \`topic/macrotrends-scraping\`
   - Rule of thumb: if the tag would only ever apply to one skill, it is too specific

4. **Coarse-grained domain/ rules:**
   - Domain tags represent high-level disciplines, not techniques or sub-specialties
   - Good: \`domain/data-engineering\`, \`domain/finance\`, \`domain/web\`, \`domain/devops\`, \`domain/python\`, \`domain/ai\`
   - Bad: \`domain/scraping\`, \`domain/config-management\`, \`domain/qualitative-analysis\`, \`domain/financial-data\`
   - Rule: a domain should be broad enough to contain 3+ skills naturally

5. **Remove** the phrase "one tag matching the skill's subject" — this is the root cause of overly-specific tags.

6. Keep the existing user confirmation flow and "(new)" annotation for new tags.

#### Design decisions

- **Prompt-only change**: no runtime validation, no scoring engine. The LLM's judgment is sufficient when given clear rules and examples.
- **Good/bad examples**: concrete examples are more effective than abstract rules for LLM guidance.

## Tests

No Python code changes — this is a prompt file modification. Verification will check the prompt content against acceptance criteria.