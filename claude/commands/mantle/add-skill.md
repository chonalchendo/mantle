Author a high-quality skill node — metadata plus dense, actionable knowledge —
and save it to the user's personal vault.

Skill nodes form an interconnected knowledge graph. The content gets loaded into
Claude's context during implementation, so it must be written *for Claude*, not
as a human tutorial. Quality is everything: dense, imperative, opinionated.

## Step 1 — Check prerequisites

Read `.mantle/config.md` and check for `personal_vault`.

- If not configured, tell the user to run `mantle init-vault <path>` first.
- If `.mantle/` does not exist, tell them to run `mantle init` first.

## Step 2 — Check for gaps and stubs

Read `.mantle/state.md` for `skills_required`. List existing skills in
`<vault>/skills/`. If there are required skills without matching nodes, show
them:

> Untracked skills detected:
>   - Python asyncio
>   - WebSocket protocol
>
> Want to start with one of these?

Also check for stub skills (0/10 proficiency) among required skills. If any
stubs exist, surface them:

> Stub skills that could be fleshed out:
>   - Docker compose (0/10)
>
> Want to fill one of these, or create a new skill?

If no gaps and no stubs, proceed directly to step 3.

## Step 3 — Gather skill metadata

Quick pass on the structural info. Ask for each in turn:

1. **Name** — What skill or technology? Be specific: "Python asyncio" not just
   "Python".
2. **Description** — One-line summary of what this skill covers and when it's
   relevant. Write in third person. Example: "Async Python patterns using
   asyncio. Use when building concurrent I/O-bound services or working with
   aiohttp/FastAPI."
3. **Proficiency** — Self-assessment 1–10. Brief calibration:
   - 1–3 = learning, following tutorials
   - 4–6 = can ship production code with it
   - 7–9 = deep expertise, can debug obscure issues
   - 10 = wrote the spec
4. **Related skills** — Other skills this connects to. Suggest from existing
   skill nodes if any are present.

   After the user provides related skills, note them for the save command.
   Obsidian will show unresolved wikilinks for skills that don't exist yet
   in the vault — this is fine and expected.

   Process each missing skill individually — the user may want different
   actions for different links.

5. **Projects** — Which projects use this skill? Suggest from known project
   names.

## Step 4 — Research the skill

Before authoring content, research the skill to complement the user's knowledge
with current expert thinking. This produces a persistent research note that
informs the skill content and remains available for future updates.

### 4a. Spawn the researcher agent

Use the Agent tool to spawn a `general-purpose` subagent with the following
prompt (fill in the values from step 3):

```
You are researching best practices and expert knowledge for a specific
technical skill. The research will be used to create a skill node — a
knowledge artifact loaded into Claude's context during implementation.

## Skill Under Investigation

Name: <name from step 3>
Description: <description from step 3>
User proficiency: <N/10>

## Research Focus

The goal is to find expert knowledge that complements the user's own
experience. Focus on:

- **Current best practices** — What do experts and official docs recommend?
- **Common patterns** — Idiomatic usage the community converges on.
- **Gotchas and pitfalls** — Non-obvious failure modes and footguns.
- **Decision criteria** — When to use this vs alternatives and trade-offs.
- **Recent changes** — New versions, deprecated patterns, shifted guidance.

Tailor depth to the user's proficiency:
- Low (1–3): cover fundamentals and common patterns they may not know.
- Mid (4–6): focus on intermediate patterns, edge cases, best practices.
- High (7–10): focus on advanced patterns, recent changes, niche gotchas.

## Instructions

Read the researcher agent instructions at claude/agents/researcher.md, then
conduct focused web research on this skill. Follow the rules and output
structure defined there. Cite all sources.
```

### 4b. Save the research

After the agent returns, save the research note:

```bash
mantle save-research \
  --focus "technology" \
  --confidence "<N/10 from agent>" \
  --content "<agent report>" \
  --no-state-update
```

### 4c. Draft and review with the user

Synthesise the research into a draft following the skill content structure (see
step 5). Write it in imperative form, for Claude's consumption. Then present
the draft to the user and ask them to:

1. **Remove** anything Claude already knows or that doesn't match their usage.
2. **Add** their own patterns, conventions, and hard-won knowledge — the things
   no amount of web research would surface. Their personal experience is what
   makes this node uniquely valuable.
3. **Correct** anything the research got wrong or that conflicts with their
   actual practice.
4. **Prioritise** — if the combined content exceeds ~150 lines, help them cut
   the least valuable parts.

The goal is a blend: expert knowledge as the foundation, personalised with the
user's real-world experience on top.

## Step 5 — Author skill content

Take the merged research + user knowledge and compose the final content. Use
this structure as a framework (not every section is required — some skills are
simple):

- **Context** (1–3 sentences) — What problem does this skill address? Why does
  it exist? Orients Claude immediately.
- **Core knowledge** — The patterns, conventions, and domain knowledge. Written
  in imperative form ("Use X for Y", not "You should use X"). Only include what
  Claude wouldn't already know — don't explain standard libraries or well-known
  concepts.
- **Examples** (if applicable) — Concrete code snippets or input/output pairs.
  2–3 examples is the sweet spot. Show the actual pattern, not a toy version.
- **Decision criteria** (if applicable) — When to use approach A vs B. "Use
  asyncio for I/O-bound concurrency. Use multiprocessing for CPU-bound work.
  Use threading only for legacy code that blocks on I/O."
- **Anti-patterns** (if applicable) — What to avoid, framed as what to do
  instead. 3–5 bullets max. "Use `asyncio.TaskGroup` instead of `gather()` for
  structured concurrency."

### Coaching principles

- Push past surface-level entries. "I know Python asyncio" is not useful.
  "Here's how I structure async code, here's what to watch out for with task
  groups, here's when I reach for asyncio vs threading" is useful.
- Challenge every token: would a senior engineer need this explained? If Claude
  already knows it, cut it. Focus on *your* patterns, *your* conventions,
  *your* hard-won knowledge.
- Explain the why, not just the what. "Use UTC timestamps consistently
  (timezone bugs are the #1 support issue)" beats "Use UTC timestamps."
- Aim for 50–150 lines. Under 50 probably isn't worth a separate node. Over
  150, consider splitting into multiple skills.
- Concrete over abstract. Show code, show the exact pattern. Avoid hand-waving.

Review the final draft with the user and iterate once before saving.

## Step 6 — Suggest content tags

Before saving, suggest content-based tags for the skill:

1. Read `.mantle/tags.md` to see the existing tag taxonomy
2. Based on the skill's name, description, and authored content, suggest
   `topic/` and `domain/` tags:
   - **`topic/<slug>`** — one tag matching the skill's subject (e.g.,
     `topic/python-asyncio`, `topic/docker-compose`)
   - **`domain/<area>`** — the broad domain (e.g., `domain/web`,
     `domain/concurrency`, `domain/database`)
3. Reuse existing tags from `tags.md` where they fit (e.g., if
   `domain/web` already exists, use it rather than creating `domain/web-dev`)
4. If proposing a new tag not in `tags.md`, note it as "(new)"
5. Present the suggested tags to the user for confirmation — they can add,
   remove, or edit tags before proceeding

After the user confirms, these tags will be passed to the save command via
`--tag` options. New tags are automatically appended to `tags.md`.

## Step 7 — Confirm and save

Show the full summary (metadata + content preview + tags), then run:

```bash
mantle save-skill \
  --name "<name>" \
  --description "<description>" \
  --proficiency "<N/10>" \
  --content "<authored content>" \
  --related-skills "<skill1>" \
  --related-skills "<skill2>" \
  --projects "<project1>" \
  --tag "topic/<slug>" \
  --tag "domain/<area>"
```

After saving, trigger recompilation so the new skill is immediately available
to Claude Code:

```bash
mantle compile
```

## Step 8 — Offer to continue

After saving, ask if they want to add another skill. If gaps were detected in
step 2, suggest the next untracked skill.

## Step 9 — Session logging

Before ending, write a session log:

```bash
mantle save-session --content "<body>" --command "add-skill"
```

Keep the log under ~200 words following the session log format (Summary, What
Was Done, Decisions Made, What's Next, Open Questions).
