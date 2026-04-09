---
issue: 18
title: Claude Code research command + researcher agent + vault template + help
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Create the Claude Code command prompt for `/mantle:research`, a dedicated researcher agent, a vault template for research notes, and update the help command. No code tests — static markdown only.

### claude/commands/mantle/research.md

Static prompt guiding Claude through the `/mantle:research` workflow.

1. **Check prerequisites** — Read `.mantle/` and `.mantle/idea.md`. If missing, direct user to run `mantle init` or `/mantle:idea` first.
2. **Load context** — Extract idea (problem + insight), challenge transcripts (if any), and existing research notes to avoid duplicate angles.
3. **Ask focus angle** — Present the five focus options (general, feasibility, competitive, technology, user-needs). Suggest uncovered angles based on existing research. Let user choose.
4. **Launch researcher subagent** — Use the Task tool to spawn a `researcher` agent (from `claude/agents/researcher.md`) with the idea context, focus angle, and any prior research as input.
5. **Save report** — Take the agent's output and save via `mantle save-research --focus <focus> --confidence <confidence> --content <report>`.
6. **Next steps** — Suggest another `/mantle:research` angle for uncovered focuses, or `/mantle:design-product` if research feels sufficient.

### claude/agents/researcher.md

Research analyst persona with clear rules and structured output.

**Persona**: Experienced research analyst validating early-stage product ideas.

**Tools**: Uses `WebSearch` and `WebFetch` to gather evidence.

**Rules**:
- Cite sources with URLs
- Distinguish evidence from absence of evidence
- Note disagreements between sources
- Flag when confidence is low due to limited data
- Do not fabricate or speculate beyond what sources support

**Output structure**:
- Summary (2-3 sentences)
- Key Findings (bulleted, with source citations)
- Feasibility Assessment
- Existing Solutions / Competitors
- Technology Options (if applicable)
- Risks & Unknowns
- Recommendation
- Confidence Rating (N/10 with justification)

### vault-templates/research.md

Empty frontmatter matching `ResearchNote` schema with body section placeholders:

```yaml
---
date:
author:
focus:
confidence:
idea_ref:
tags:
  - type/research
  - phase/research
---
```

Body sections with placeholder prompts matching the agent output structure.

### claude/commands/mantle/help.md (modify)

Add `/mantle:research` to the "Idea & Validation" section, after `/mantle:challenge`:

```
- `/mantle:research` — Research and validate an idea with web evidence
```

## Tests

No tests — static markdown files only.
