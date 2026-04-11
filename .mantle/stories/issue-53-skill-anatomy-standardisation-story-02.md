---
issue: 53
title: Migrate 5 vault skills to what/why/when/how anatomy with reference marker
status: in-progress
failure_log: null
tags:
- type/story
- status/in-progress
---

## User Story

As a developer using Mantle skills during planning, I want high-use skills restructured as executable workflows with anti-rationalization guardrails so that the AI follows a process with checkpoints rather than interpreting reference prose.

## Depends On

Story 1 — the compiler must support the reference marker before migrated skills can compile correctly.

## Approach

Restructure 5 vault skill source files into the standardised what/why/when/how anatomy. Each skill gets the new structure above \`<!-- mantle:reference -->\` (under ~150 lines) and deep reference material below. Process skills (design-review, software-design-principles, cli-design-best-practices) get numbered workflow steps. Reference skills (cyclopts, python-project-conventions) get pattern catalogues. All 5 get Common Rationalizations and Red Flags sections.

This story modifies vault source files only (in the personal vault at \`~/test-vault/skills/\`). After migration, run \`mantle compile\` to verify compiled output reflects the new structure.

## Implementation

### Vault source files to migrate (5 files in ~/test-vault/skills/)

For each skill, restructure content below \`<!-- mantle:content -->\` into:

**Above \`<!-- mantle:reference -->\`** (~100-150 lines — the executable workflow):

\`\`\`markdown
## What

1-3 sentences grounding the skill.

## Why

What goes wrong without this skill — motivates the agent.

## When to Use

Bullet list of trigger conditions.

## When NOT to Use

Bullet list of exclusions — prevents over-application.

## How

### [For process skills: numbered steps with gates]
### [For reference skills: pattern catalogue with decision criteria]

## Common Rationalizations

| Rationalization | Why It's Wrong | What to Do Instead |
|---|---|---|

## Red Flags

- Checklist of early warning signs

## Verification

Evidence-based exit criteria — what to check before considering the skill applied.
\`\`\`

**Below \`<!-- mantle:reference -->\`** (deep material):
- Full API reference tables, extended checklists, exhaustive examples
- Content that's too detailed for the main workflow but valuable for deep dives

#### Migration plan per skill:

1. **design-review.md** (process skill — 150 lines):
   - "How" = numbered review workflow steps (read code, apply checklist, check red flags, write findings)
   - Move the full Red Flag Severity Matrix to reference section
   - Keep the Design Principles Checklist in main section (it IS the workflow)

2. **software-design-principles.md** (process skill — 186 lines):
   - "How" = numbered steps for applying principles to a design decision
   - Move extended principle explanations to reference section
   - Keep the core principles table in main section

3. **python-project-conventions.md** (reference skill — 132 lines):
   - "How" = pattern catalogue: naming, imports, docstrings, testing conventions
   - May not need reference marker if content fits in ~150 lines
   - Add rationalizations for common convention violations

4. **cli-design-best-practices.md** (reference skill — 95 lines):
   - "How" = pattern catalogue: command structure, argument design, output formatting
   - Short enough that all content may fit above the marker
   - Add rationalizations for common CLI anti-patterns

5. **cyclopts.md** (reference skill — 149 lines):
   - "How" = pattern catalogue: type-hint parsing, subcommands, validation, testing
   - Move full API examples to reference section
   - Keep decision criteria and core patterns in main section

#### Design decisions

- **Process vs reference distinction**: Skills with a natural sequential workflow (review, design) get numbered steps. Skills that are knowledge catalogues (conventions, framework APIs) get pattern tables. The anatomy allows both.
- **Preserve existing knowledge**: Restructure, don't rewrite. The knowledge content is already good — it just needs reorganisation into the new sections.

## Tests

### tests/core/test_skills.py (modify)

- **test_compile_migrated_skill_with_reference_marker**: take one migrated skill's content, compile it, verify SKILL.md has the workflow sections and references/core.md has the deep material
- **test_migrated_skill_main_section_under_150_lines**: verify each migrated skill's above-marker content is under 150 lines

### Manual verification (not automated)

- Run \`mantle compile\` after migration and inspect \`.claude/skills/*/SKILL.md\` to confirm new structure
- Verify skills still trigger correctly in Claude Code via native loader