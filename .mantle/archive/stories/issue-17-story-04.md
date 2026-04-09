---
issue: 17
title: Claude Code command + vault template
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Create the static Claude Code command prompt and Obsidian vault template. The command is the primary interface for skill creation — it guides the user through authoring real skill content that will be loaded into Claude's context during implementation. Research found that content quality is everything: dense, imperative, written for Claude, not a human tutorial.

### Research context

Key findings from `.mantle/research/2026-03-02-skill-effectiveness.md`:
- The `description` field determines whether a skill gets activated. Write in third person, include both what and when.
- Content should be 50–150 lines of dense, high-signal knowledge.
- Challenge every token: "Would a senior engineer need this explained?" If not, cut it.
- Explain the why, not just the what. Concrete over abstract. Show code and examples.
- Recommended content structure: context/purpose → core knowledge → examples → decision criteria → anti-patterns.
- Anti-patterns: over-explaining what Claude already knows, offering too many options, vague descriptions, dump-and-run monologues.

### claude/commands/mantle/add-skill.md

Static prompt guiding Claude through the `/mantle:add-skill` workflow:

1. **Check prerequisites** — Confirm `.mantle/` exists and personal vault is configured (read `.mantle/config.md` for `personal_vault`). If vault not configured, tell user to run `mantle init-vault <path>` first.

2. **Check for gaps** — Read `state.md` for `skills_required`. List existing skills in `<vault>/skills/`. If there are untracked skills, show them and suggest starting with those.

3. **Gather skill metadata** — Quick pass on the structural info:
   - **Name** — What skill or technology? Be specific: "Python asyncio" not just "Python".
   - **Description** — One-line summary of what this skill covers and when it's relevant. Write in third person. Example: "Async Python patterns using asyncio. Use when building concurrent I/O-bound services or working with aiohttp/FastAPI."
   - **Proficiency** — Self-assessment 1-10. Brief calibration: 1-3 = learning, 4-6 = can ship with it, 7-9 = deep expertise, 10 = wrote the spec.
   - **Related skills** — Other skills this connects to. Suggest from existing skill nodes if any.
   - **Projects** — Which projects use this skill? Suggest from known project names.

4. **Author skill content** — This is the substance of the node and the hardest part to get right. The content gets loaded into Claude's context during implementation, so it must be written *for Claude*, not as a human tutorial.

   Guide the user through writing dense, actionable knowledge. Use the recommended structure as a framework, but don't force every section — some skills are simple:

   - **Context** (1–3 sentences) — What problem does this skill address? Why does it exist? Orients Claude immediately.
   - **Core knowledge** — The patterns, conventions, and domain knowledge. Written in imperative form ("Use X for Y", not "You should use X"). Only include what Claude wouldn't already know — don't explain standard libraries or well-known concepts.
   - **Examples** (if applicable) — Concrete code snippets or input/output pairs. 2–3 examples is the sweet spot. Show the actual pattern, not a toy version.
   - **Decision criteria** (if applicable) — When to use approach A vs B. "Use asyncio for I/O-bound concurrency. Use multiprocessing for CPU-bound work. Use threading only for legacy code that blocks on I/O."
   - **Anti-patterns** (if applicable) — What to avoid, framed as what to do instead. 3–5 bullets max. "Use `asyncio.TaskGroup` instead of `gather()` for structured concurrency."

   **Coaching principles:**
   - Push past surface-level entries. "I know Python asyncio" is not useful. "Here's how I structure async code, here's what to watch out for with task groups, here's when I reach for asyncio vs threading" is useful.
   - Challenge every token: would a senior engineer need this explained? If Claude already knows it, cut it. Focus on *your* patterns, *your* conventions, *your* hard-won knowledge.
   - Explain the why, not just the what. "Use UTC timestamps consistently (timezone bugs are the #1 support issue)" beats "Use UTC timestamps."
   - Aim for 50–150 lines. Under 50 probably isn't worth a separate node. Over 150, consider splitting into multiple skills.
   - Concrete over abstract. Show code, show the exact pattern. Avoid hand-waving.

   Compose the content as a cohesive markdown body. Use subheadings within the content as needed. Review the draft with the user and iterate once before saving.

5. **Confirm and save** — Show the full summary (metadata + content), then run:

   ```bash
   mantle save-skill \
     --name "<name>" \
     --description "<description>" \
     --proficiency "<N/10>" \
     --content "<authored content>" \
     --related-skills "<skill1>" \
     --related-skills "<skill2>" \
     --projects "<project1>"
   ```

6. **Offer to continue** — After saving, ask if they want to add another skill. If gaps were detected in step 2, suggest the next untracked skill.

7. **Session logging** — Before ending, write a session log:

   ```bash
   mantle save-session --content "<body>" --command "add-skill"
   ```

### vault-templates/skill.md

Template with frontmatter fields and placeholder body. The content section makes it clear this is for real knowledge, not just metadata:

```markdown
---
name: ""
description: ""
type: skill
proficiency: "/10"
related_skills: []
projects: []
last_used:
author: ""
created:
updated:
updated_by: ""
tags:
  - type/skill
---

## Related Skills

_Link related skills with [[wikilinks]]._

## Projects

_Link projects that use this skill with [[wikilinks]]._

## Context

_What problem does this skill address? Why does it exist? (1–3 sentences)_

## Core Knowledge

_The patterns, conventions, and domain knowledge you actually use.
Written in imperative form. Only what Claude wouldn't already know._

## Examples

_Concrete code snippets or patterns. Show the real thing, not a toy version._

## Decision Criteria

_When to use this vs alternatives. The decision logic._

## Anti-patterns

_What to avoid, framed as what to do instead. 3–5 bullets max._
```

## Tests

No tests — static markdown files only.
