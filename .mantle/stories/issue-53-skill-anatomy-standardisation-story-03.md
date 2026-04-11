---
issue: 53
title: Update add-skill prompt to generate new anatomy format
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer creating new skills via /mantle:add-skill, I want the prompt to generate the standardised anatomy so that all new skills are consistent and effective when injected into agent context.

## Depends On

None — independent of stories 1 and 2. This is a prompt-only change.

## Approach

Update the content authoring step (Step 5) in \`claude/commands/mantle/add-skill.md\` to generate skills in the what/why/when/how anatomy. Add guidance for process vs reference skill "how" sections. Include rationalizations table, red flags, and verification section as required anatomy elements. Add instructions for the \`<!-- mantle:reference -->\` marker placement.

## Implementation

### claude/commands/mantle/add-skill.md (modify)

Replace Step 5 ("Author skill content") with updated instructions:

1. **Replace the content structure framework** with the new anatomy:

   Replace the current structure (Context, Core knowledge, Examples, Decision criteria, Anti-patterns) with:

   \`\`\`
   ## What
   1-3 sentences grounding the skill. What problem does it address?

   ## Why
   What goes wrong without this skill. Motivates the agent to follow it.

   ## When to Use
   Bullet list of trigger conditions.

   ## When NOT to Use
   Bullet list of exclusions. Prevents over-application.

   ## How

   [Choose format based on skill type:]

   For PROCESS skills (reviews, design workflows, deployment checklists):
   Numbered steps with gates. Each step has a clear entry condition and exit
   criterion. Example: "1. Read the module interface first (gate: can you
   describe the public API in one sentence?)"

   For REFERENCE skills (frameworks, conventions, API patterns):
   Pattern catalogue with decision criteria. Group by concern (naming,
   imports, error handling). Use tables for quick reference.

   ## Common Rationalizations

   | Rationalization | Why It's Wrong | What to Do Instead |
   |---|---|---|
   | "This case is different" | [specific reason] | [specific action] |

   3-5 rows. These are the excuses agents use to skip steps.

   ## Red Flags

   - Early warning signs that the skill is being misapplied
   - 3-5 bullets

   ## Verification

   Evidence-based exit criteria. What must be true when you're done?
   \`\`\`

2. **Add progressive disclosure guidance** after the anatomy:

   > If the skill has deep reference material (full API tables, extended
   > examples, exhaustive checklists), place it below a
   > \`<!-- mantle:reference -->\` marker. This content compiles into
   > \`references/core.md\` for on-demand loading.
   >
   > Target: main content above the marker should be under ~150 lines.
   > Not every skill needs a reference section — short skills can omit it.

3. **Update coaching principles** to reference the new anatomy:
   - Replace "50-150 lines" target with "~150 lines above the reference marker"
   - Add: "Every skill needs What, Why, When to Use, How, and Verification at minimum. Common Rationalizations and Red Flags are strongly recommended."
   - Add: "Choose process (numbered steps) or reference (pattern catalogue) format for the How section based on whether the skill describes a sequential workflow or a knowledge domain."

#### Design decisions

- **Prompt-only change**: No Python code changes. The add-skill prompt is a static markdown file.
- **Minimum viable anatomy**: What, Why, When, How, Verification are required. Rationalizations and Red Flags are "strongly recommended" not required — some simple skills (e.g., a single-library API) may not have meaningful rationalizations.

## Tests

No automated tests — this is a prompt content change. Verification is manual:
- Run \`/mantle:add-skill\` and confirm it generates the new anatomy sections
- Confirm the generated skill compiles correctly via \`mantle compile\`