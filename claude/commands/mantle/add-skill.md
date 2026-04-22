---
allowed-tools: Read, Bash(mantle *), Agent
---

Author a high-quality skill node — metadata plus dense, actionable knowledge —
and save it to the user's personal vault.

Skill nodes form an interconnected knowledge graph. The content gets loaded into
Claude's context during implementation, so write it *for Claude*, not as a
human tutorial. Quality is everything: dense, imperative, opinionated.

Use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Check for gaps and stubs"
3. "Step 3 — Gather skill metadata"
4. "Step 4 — Research the skill"
5. "Step 5 — Author skill content"
6. "Step 6 — Suggest content tags"
7. "Step 7 — Confirm and save"
8. "Step 8 — Offer to continue"
9. "Step 9 — Session logging"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls must use `$MANTLE_DIR/...` in
place of `.mantle/...`.

Read `$MANTLE_DIR/config.md` and check for `personal_vault`.

- If not configured, tell the user to run `mantle init-vault <path>` first.
- If `.mantle/` does not exist, tell them to run `mantle init` first.

## Step 2 — Check for gaps and stubs

Read `$MANTLE_DIR/state.md` for `skills_required`. List existing skills in
`<vault>/skills/`. Show any required skills without matching nodes:

> Untracked skills detected:
>   - Python asyncio
>   - WebSocket protocol
>
> Want to start with one of these?

Also surface stub skills (0/10 proficiency) among required skills:

> Stub skills that could be fleshed out:
>   - Docker compose (0/10)
>
> Want to fill one of these, or create a new skill?

If no gaps and no stubs, proceed to Step 3.

## Step 3 — Gather skill metadata

Ask for each in turn:

1. **Name** — specific: "Python asyncio" not "Python".
2. **Description** — one-line, third person. Example: "Async Python patterns
   using asyncio for concurrent I/O-bound services."
3. **When to use** — trigger conditions for auto-invocation (when to activate,
   not what it is). Example: "Use when building concurrent I/O-bound services,
   working with aiohttp/FastAPI, or debugging async deadlocks." Leave blank if
   unsure — description will be used as fallback.
4. **Proficiency** — self-assessment 1–10:
   - 1–3 = learning, following tutorials
   - 4–6 = can ship production code
   - 7–9 = deep expertise, can debug obscure issues
   - 10 = wrote the spec
4. **Related skills** — suggest from existing skill nodes. Note them for the
   save command. Unresolved Obsidian wikilinks are expected. Process each
   missing skill individually.
5. **Projects** — which projects use this skill? Suggest from known names.

## Step 4 — Research the skill

### 4a. Spawn the researcher agent

Spawn a `general-purpose` subagent (fill values from Step 3):

```
You are researching best practices and expert knowledge for a specific
technical skill. The research will be used to create a skill node — a
knowledge artifact loaded into Claude's context during implementation.

## Skill Under Investigation

Name: <name from step 3>
Description: <description from step 3>
User proficiency: <N/10>

## Research Focus

Find expert knowledge that complements the user's own experience. Focus on:

- **Current best practices** — What do experts and official docs recommend?
- **Common patterns** — Idiomatic usage the community converges on.
- **Gotchas and pitfalls** — Non-obvious failure modes and footguns.
- **Decision criteria** — When to use this vs alternatives and trade-offs.
- **Recent changes** — New versions, deprecated patterns, shifted guidance.

Tailor depth to proficiency:
- Low (1–3): cover fundamentals and common patterns they may not know.
- Mid (4–6): focus on intermediate patterns, edge cases, best practices.
- High (7–10): focus on advanced patterns, recent changes, niche gotchas.

## Instructions

Read the researcher agent instructions at claude/agents/researcher.md, then
conduct focused web research on this skill. Follow the rules and output
structure defined there. Cite all sources.
```

### 4b. Save the research

```bash
mantle save-research \
  --focus "technology" \
  --confidence "<N/10 from agent>" \
  --content "<agent report>" \
  --no-state-update
```

### 4c. Draft and review with the user

Synthesise the research into a draft following the skill content structure
(Step 5). Write in imperative form for Claude's consumption. Present the draft
and ask the user to:

1. **Remove** anything Claude already knows or that doesn't match their usage.
2. **Add** their own patterns, conventions, and hard-won knowledge — what no
   web research would surface. Personal experience is what makes a node
   uniquely valuable.
3. **Correct** anything that conflicts with their actual practice.
4. **Prioritise** — if combined content exceeds ~150 lines, cut the least
   valuable parts.

## Step 5 — Author skill content

Compose the final content using the standard skill anatomy. Every skill must
follow this structure (required = mandatory; others strongly recommended):

```
## What (required)
1–3 sentences grounding the skill. What problem does it address? Why does it
exist?

## Why (required)
What goes wrong without this skill. Frame as consequences, not abstractions.

## When to Use (required)
Bullet list of trigger conditions.

## When NOT to Use (required)
Bullet list of exclusions — prevents over-application.

## How (required)

For PROCESS skills (reviews, design workflows, deployment checklists):
Numbered steps with gates. Each step has a clear entry condition and exit
criterion.

For REFERENCE skills (frameworks, conventions, API patterns):
Pattern catalogue with decision criteria. Group by concern. Use tables for
quick reference.

## Common Rationalizations (recommended)

| Rationalization | Why It's Wrong | What to Do Instead |
|---|---|---|
| "This case is different" | [specific reason] | [specific action] |

3–5 rows.

## Red Flags (recommended)

- Early warning signs that the skill is being misapplied
- 3–5 bullets

## Verification (required)

Evidence-based exit criteria. What must be true when you're done?
```

### Progressive disclosure

Place deep reference material (full API tables, extended examples, exhaustive
checklists) below a `<!-- mantle:reference -->` marker. This compiles into
`references/core.md` for on-demand loading. Main content above the marker
should be under ~150 lines. Short skills can omit the marker.

### Coaching principles

- Push past surface-level entries. "Here's how I structure async code, here's
  what to watch out for with task groups" beats "I know Python asyncio."
- Challenge every token: if Claude already knows it, cut it. Focus on *your*
  patterns, *your* conventions, *your* hard-won knowledge.
- Explain the why: "Use UTC timestamps consistently (timezone bugs are the #1
  support issue)" beats "Use UTC timestamps."
- Aim for ~150 lines above the reference marker. Under 50 probably isn't worth
  a separate node; over 150, move deep material below the marker.
- Every skill needs What, Why, When to Use, How, and Verification at minimum.
- Concrete over abstract — show code, show the exact pattern.

Review the final draft with the user and iterate once before saving.

## Step 6 — Suggest content tags

Read `$MANTLE_DIR/tags.md`, then run `mantle list-tags`.

Apply these rules when selecting tags:

### Reuse rule

If an existing tag covers the skill's subject area, reuse it. Do not create
a more specific variant of an existing tag.

### topic/ — coarse-grained subject areas

Choose a tag broad enough that other skills could share it.

- Good: `topic/scraping`, `topic/pydantic`, `topic/streamlit`, `topic/duckdb`
- Bad: `topic/playwright-web-scraping`, `topic/pydantic-discriminated-unions`

If the tag would only ever apply to one skill, it is too specific.

### domain/ — high-level disciplines

Broad enough to contain 3+ skills naturally.

- Good: `domain/data-engineering`, `domain/finance`, `domain/web`,
  `domain/devops`, `domain/python`, `domain/ai`
- Bad: `domain/scraping`, `domain/config-management`

### After selecting tags

If proposing a new tag not in `tags.md`, note it as "(new)". Present to the
user for confirmation — they can add, remove, or edit before proceeding.
New tags are automatically appended to `tags.md`.

## Step 7 — Confirm and save

Show the full summary (metadata + content preview + tags), then run:

```bash
mantle save-skill \
  --name "<name>" \
  --description "<description>" \
  --when-to-use "<trigger conditions>" \
  --proficiency "<N/10>" \
  --content "<authored content>" \
  --related-skills "<skill1>" \
  --related-skills "<skill2>" \
  --projects "<project1>" \
  --tag "topic/<slug>" \
  --tag "domain/<area>"
```

Omit `--when-to-use` if the user left it blank.

After saving, recompile:

```bash
mantle compile
```

## Step 8 — Offer to continue

Ask if they want to add another skill. If gaps were detected in Step 2,
suggest the next untracked skill.

## Step 9 — Session logging

```bash
mantle save-session --content "<body>" --command "add-skill"
```

Keep under ~200 words: Summary, What Was Done, Decisions Made, What's Next,
Open Questions.
