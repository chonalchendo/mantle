---
issue: 35
title: Scout prompt — clone, analyze, synthesize, save
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer, I want to run /mantle:scout <repo-url> and have the AI analyze an external repo through the lens of my project's product vision and system design, so that I get targeted insights rather than generic observations.

## Depends On

Story 2 — needs save-scout CLI command to persist reports.

## Approach

Creates the scout.md prompt file following the established prompt orchestrator pattern (like implement.md). The prompt handles the full flow: clone to temp dir via Bash, compile project context inline, spawn parallel Agent subagents for each analysis dimension, synthesize results, save via mantle save-scout, and clean up the temp dir.

## Implementation

### claude/commands/mantle/scout.md (new file)

Create a static prompt command with this structure:

**Frontmatter:**
```yaml
---
argument-hint: <repo-url>
allowed-tools: Read, Bash, Agent, Glob, Grep
---
```

**Flow (prompt instructions):**

1. **Parse input** — Extract repo URL from $ARGUMENTS. If no URL provided, ask the user.

2. **Clone** — Run \`git clone --depth 1 <url> $(mktemp -d)\` via Bash. Capture the temp dir path. Depth-1 clone is sufficient for analysis — no history needed.

3. **Compile project context** — Read and summarize:
   - .mantle/product-design.md (vision, features, differentiators)
   - .mantle/system-design.md (architecture, modules, patterns)
   - .mantle/issues/ (current backlog — titles and status only)
   - .mantle/learnings/ (past implementation learnings)
   - Any compiled skills in .claude/skills/*/SKILL.md

4. **Parallel analysis** — Spawn 4-5 Agent subagents (subagent_type: "Explore"), each analyzing the cloned repo through a specific dimension with the compiled project context as lens:

   - **Architecture agent**: Module structure, dependency direction, layering patterns. "What architectural patterns does this repo use that are relevant to our system design?"
   - **Patterns agent**: Naming conventions, error handling, configuration management. "What coding patterns could we adopt or learn from?"
   - **Testing agent**: Test framework, fixture patterns, coverage approach. "What testing strategies does this repo use that we should consider?"
   - **CLI design agent** (if repo has a CLI): Command structure, argument patterns, help text UX. "What CLI patterns are better than ours?"
   - **Domain-specific agent**: Derived from our product design — "What domain-specific features or approaches in this repo are relevant to our product goals?"

   Each agent prompt must include:
   - The cloned repo path to analyze
   - The compiled project context (so analysis is through OUR lens)
   - Instruction to produce structured findings: pattern name, what they do, how it's relevant to us, recommendation (adopt/adapt/skip)

5. **Synthesize** — Combine agent results into a structured report:

   ```markdown
   # Scout Report: {repo-name}

   **Repository:** {url}
   **Analyzed:** {date}
   **Dimensions:** {list}

   ## Executive Summary
   [2-3 sentence summary of key findings relevant to our project]

   ## Findings by Dimension

   ### Architecture
   [Structured findings with recommendations]

   ### Patterns & Conventions
   [Structured findings with recommendations]

   ### Testing
   [Structured findings with recommendations]

   ### CLI Design
   [If applicable]

   ### Domain-Specific
   [Findings relevant to our product goals]

   ## Actionable Recommendations

   ### Adopt (high confidence, clear benefit)
   - [Recommendation tied to specific backlog gap or design opportunity]

   ### Adapt (needs modification for our context)
   - [Recommendation with adaptation notes]

   ### Skip (interesting but not relevant now)
   - [Pattern noted for future reference]

   ## Backlog Implications
   [Which existing issues or gaps in our backlog are informed by these findings?]
   ```

6. **Save** — Run \`mantle save-scout --repo-url "<url>" --repo-name "<name>" --dimensions "architecture" --dimensions "patterns" --dimensions "testing" --dimensions "cli-design" --dimensions "domain" --content "<report>"\`

7. **Cleanup** — Run \`rm -rf <tmpdir>\` via Bash.

8. **Report** — Display the executive summary and actionable recommendations to the user.

#### Design decisions

- **--depth 1 clone**: Analysis needs current state only, not history. Faster and smaller.
- **Explore agents, not general-purpose**: Explore agents are optimized for codebase analysis — exactly what each dimension agent does.
- **Project context as lens in every agent prompt**: This is the key differentiator. Each agent doesn't just analyze the repo generically — it analyzes through the lens of OUR product/system design.
- **Structured recommendation tiers**: Adopt/Adapt/Skip gives actionable clarity. Each recommendation links back to our backlog.

## Tests

No pytest tests for this story — it's a prompt file (markdown). The prompt will be validated through the verification step (Step 8) which checks all acceptance criteria end-to-end.

Manual validation: the prompt file exists at the correct path with correct frontmatter.