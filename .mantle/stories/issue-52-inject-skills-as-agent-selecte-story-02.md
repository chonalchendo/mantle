---
issue: 52
title: Update shape-issue prompt with agent-curated skill selection
status: planned
failure_log: null
tags:
- type/story
- status/planned
---

## User Story

As a developer shaping an issue, I want the AI agent to automatically discover, select, and read the most relevant vault skills so that the shaped issue's code design is grounded in domain-specific patterns and conventions.

## Depends On

Story 1 — requires the enriched `mantle list-skills` output with descriptions.

## Approach

Rewrite the "Load skills" section in `shape-issue.md` to use agent-curated selection: run `mantle list-skills`, review descriptions, pick 2-4, read full `references/core.md` for each. Skills inform the shaped issue's code design — downstream stages (plan-stories, implement) consume that output rather than re-reading skills. Also remove the now-redundant "Required reading injection" from `implement.md`. This is a prompt-only story — no Python code changes.

## Implementation

### claude/commands/mantle/shape-issue.md (modify)

Replace the "Load skills" section (lines 69-83) with the following. Keep everything else in the file unchanged:

```markdown
### Load skills

Skills give you domain-specific knowledge (patterns, conventions, anti-patterns)
that grounds approach evaluation in project reality rather than generic advice.
Skills are loaded here — at the shaping stage where design decisions are made.
Downstream stages (plan-stories, implement) consume the shaped issue's code
design, which already reflects skill knowledge.

1. Run `mantle list-skills` to see available skills with descriptions.
2. **Select 2-4 skills** whose descriptions directly match the work in this
   issue. Choose skills you would actively consult during this work — not
   tangentially related ones. For example, a CLI issue needs `cyclopts` and
   `cli-design-best-practices`, not `streamlit`.
3. For each selected skill, Read `.claude/skills/{slug}/references/core.md`
   to load the full domain knowledge.
4. Apply skill knowledge when writing the code design section — include
   specific patterns, conventions, and anti-patterns from the skills.
   The code design is how skill knowledge flows to stories and implementation.

If `mantle list-skills` fails (vault not configured), skip this step and note
it — approach evaluation will rely on system design and codebase reading only.

> **Skills loaded:** {list of selected skills and why each was chosen, or
> "vault not configured — skipped"}
```

### claude/commands/mantle/implement.md (modify)

Remove the "Required reading injection" section (lines 159-177, from "**Required reading injection:**" through "won't be specifically directed to read them."). Replace with:

```markdown
**Skill context:** Skill knowledge is embedded in the shaped issue's code
design and flows into stories via their implementation sections. Do not
separately inject skill files — the story spec already carries the relevant
domain knowledge.
```

Keep all surrounding sections unchanged. The "Step 4 — Select relevant context per story" section still includes learnings, decisions, and the general skill scan (lines 137-139) — only the forced "Required reading" injection is removed.

### claude/commands/mantle/plan-stories.md (no changes)

No changes needed. plan-stories already reads the shaped issue (step 2, line 55), which contains skill-informed code design. Step 5c (skill gap detection and `mantle update-skills`) remains as-is — it handles gap detection after stories are written, which is still valuable.

#### Design decisions

- **Skills load only at shaping**: shaping is where design judgment happens. Stories and implementation execute decisions already made. Loading skills again is redundant token spend.
- **Removing Required reading injection**: stories carry skill knowledge via the shaped code design → story spec chain. The general skill scan in implement.md step 4 (lines 137-139) remains for optional context, but forced injection is removed.
- **plan-stories.md unchanged**: it reads the shaped issue which already contains skill-informed code design. Step 5c gap detection stays for identifying missing skills.

## Tests

No automated tests — these are prompt files, not Python code. Verification:
- Run `mantle compile` and confirm prompts compile without errors
- Verify the shape-issue.md "Load skills" section reads coherently in context
- Verify the implement.md section replacement doesn't break surrounding content