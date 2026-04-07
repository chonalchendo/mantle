---
issue: 36
title: Required reading section in implement.md story prompts
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer reviewing AI-generated code, I want implementation agents to read specific skill anti-patterns before coding so that review issues are caught during implementation, not after.

## Depends On

Story 1 — requires skills_required on IssueNote to know which skills are relevant.

## Approach

Modify implement.md Step 4 (context brief per story) to inject a Required reading section listing the issue's skills_required. This directs agents to read specific compiled skills before implementing. Also update the build pipeline (build.md references) to pass issue number to compile during the build flow.

## Implementation

### claude/commands/mantle/implement.md (modify)

In Step 4 (Select relevant context per story), add instruction to read the issue's skills_required field and include a Required reading section in each story's context brief:

After the existing context brief instructions, add:

\`\`\`
**Required reading injection:** Read the issue file's \`skills_required\` frontmatter field. For each skill listed, add a \`## Required reading\` section to the story agent's prompt:

> ## Required reading
>
> Before implementing, read these compiled skills for domain-specific conventions and anti-patterns:
> - \`.claude/skills/{skill-slug}/SKILL.md\` — {skill name}
> - \`.claude/skills/{skill-slug}/SKILL.md\` — {skill name}
>
> Apply the patterns and avoid the anti-patterns described in these skills.

If the issue has no skills_required (empty or missing), skip this section — the agent will still see compiled skills in .claude/skills/ but won't be directed to read specific ones.
\`\`\`

This is a prompt-only change — no Python code modifications needed.

#### Design decisions

- **Prompt-level injection, not code**: The implement.md prompt is read by the orchestrator agent, which constructs per-story context briefs. Adding the Required reading instruction here is the simplest integration point — no code changes needed.
- **Skill slugs in paths**: The compiled skills use slug names matching the vault skill names, so the prompt can reference them directly.

## Tests

### tests/core/test_implement_prompt.py (new file — optional, skip if no testable code)

This story modifies only a prompt file (implement.md), not Python code. No automated tests are needed. The verification step will confirm the prompt content is correct.

Manual verification:
- Read implement.md and confirm the Required reading section is present in Step 4
- Confirm it references skills_required from the issue frontmatter
- Confirm it generates .claude/skills/{slug}/SKILL.md paths