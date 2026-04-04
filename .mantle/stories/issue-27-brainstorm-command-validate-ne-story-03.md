---
issue: 27
title: Claude Code brainstorm.md slash command
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a developer mid-project, I want to run `/mantle:brainstorm` and have an interactive session that explores my idea, checks it against my product vision, selectively challenges it, and produces a verdict — so I can decide whether to add it to my backlog.

## Depends On

Story 2 (the command invokes `mantle save-brainstorm` via Bash tool).

## Approach

Create a static markdown command following the structure of `challenge.md` — with step-based task tracking, conversational interaction rules, and CLI invocation for persistence. The key innovation is the vision alignment check (step 3) and scaled rigor (step 4), which don't exist in any current command. Uses the `analysis` scratchpad pattern from `challenge.md` for internal reasoning.

## Implementation

### claude/commands/mantle/brainstorm.md (new file)

**Frontmatter:**
```yaml
---
description: Use when you want to explore and validate a new feature idea against your existing product vision
allowed-tools: Read, Bash(mantle *)
---
```

**Preamble:**

Explore and validate a feature idea for an existing project. Combine structured exploration with selective challenge techniques, scaled to the idea's complexity. The goal is to determine whether this idea serves the vision — not to rubber-stamp it.

Be rigorous but efficient. One question per message. Scale challenge depth to the idea's scope. Don't over-process small features.

**Iron Laws** (adapted from challenge.md):
1. NO rubber-stamping. Every idea must survive a vision alignment check.
2. NO skipping the vision check. Even "obvious" features can be scope creep.
3. NO premature verdicts. Complete the exploration before judging.

**Red Flags table** (same format as challenge.md):

| Thought | Reality |
|---------|---------|
| "This obviously fits the vision, skip the check" | Obvious-seeming features are where scope creep hides |
| "The user seems excited, I'll be positive" | Excitement ≠ alignment. Check the vision. |
| "This is a small feature, no need for challenge" | Small features still get assumption surfacing. Scale the depth, don't skip it. |

**Task tracking:** Before starting, use TaskCreate for steps 1-8. Update status as each step begins/completes.

**Step 1 — Check prerequisites:**
Read `.mantle/state.md` and verify:
- `.mantle/` exists. If not, tell the user to run `mantle init` first.
- `.mantle/product-design.md` exists. If not, tell the user to run `/mantle:design-product` first — brainstorm requires a vision to evaluate against.

**Step 2 — Load context:**
Read and internalise:
- `.mantle/product-design.md` — the stubborn vision (what and why). Extract: vision statement, target user, success metrics, design principles.
- `.mantle/system-design.md` — the flexible details (how). Note architecture boundaries.
- `.mantle/issues/` — existing backlog (for overlap and conflict detection)
- `.mantle/brainstorms/` — past brainstorms including scrapped ideas (avoid retreading rejected ideas without new evidence)
- `.mantle/learnings/` — past learnings that may inform this brainstorm

Display context summary:
> **Product vision**: {one-line vision from product-design.md}
> **Existing issues**: {count} in backlog
> **Past brainstorms**: {count} ({scrapped count} scrapped)

If past brainstorms exist for a similar topic, flag it:
> **Note**: A similar idea was brainstormed on {date} and {verdict}. [Brief reason.]

**Step 3 — Explore the idea:**
Interactive conversation, one question at a time:
1. What's the idea? (let the user describe it freely — open-ended)
2. What problem does this solve for the target user defined in product-design.md? (focus question)
3. What's the non-obvious insight — why now, why this approach? (depth question)
4. How big is this? Present as multiple choice:
   - **Small feature** — single issue, 1-3 stories, touches one slice
   - **Medium capability** — 1-2 issues, new module or significant extension
   - **Large paradigm shift** — multiple issues, rethinks a core assumption

Rules:
- One question per message
- Prefer multiple choice where appropriate
- Reflect back and confirm before moving on
- 3-5 exchanges total for exploration

**Step 4 — Vision alignment check:**
The non-negotiable step. Use `<analysis>` scratchpad to reason through:
- Does this idea directly serve the vision statement in product-design.md?
- Does it advance any of the success metrics?
- Does it conflict with any design principles?
- Does it duplicate or conflict with any existing issue?
- Is this the most important thing to work on right now, given the current backlog?
- Would the target user (as defined in product-design.md) actually want this?

Present the alignment assessment honestly:
> **Vision alignment**: {Strong / Moderate / Weak / Misaligned}
> **Rationale**: {1-2 sentences connecting the idea to (or disconnecting it from) the vision}
> **Existing overlap**: {None / Partial overlap with issue-NN / Duplicate of issue-NN}
> **Priority assessment**: {High — addresses gap in current backlog / Medium — nice to have / Low — backlog has more pressing items}

If alignment is Weak or Misaligned, be direct but respectful. Explain why and suggest what to focus on instead.

**Step 5 — Selective challenge:**
Scale challenge depth based on the idea's size (from step 3):

- **Small features** (1-3 exchanges): Assumption surfacing only. Name 2-3 assumptions, ask which ones the user is least confident about, push on those.
- **Medium capabilities** (3-5 exchanges): Assumption surfacing + first-principles analysis + devil's advocate. Weave between lenses based on conversation flow.
- **Large paradigm shifts** (5-8 exchanges): All five lenses from challenge.md (assumption surfacing, first-principles, devil's advocate, pre-mortem, competitive analysis). Full treatment.

Same rules as challenge.md step 3:
- Follow threads when a response is weak
- Don't accept hand-wavy answers ("should work", "probably fine")
- Acknowledge strong responses and move on
- Be specific, not generic

**Step 6 — Propose 2-3 lightweight approaches:**
For ideas that survived the vision check and challenge (likely "proceed" or "research" verdicts):
- Name each approach in 1-2 words
- One-line description of what it looks like
- Key trade-off (what you gain vs what you give up)
- Rough appetite (small/medium/large)

This is NOT full shaping — just enough to understand feasibility and scope. Skip this step entirely if the verdict is clearly "scrap".

**Step 7 — Synthesise and save:**

Use `<analysis>` scratchpad to weigh evidence before presenting.

Format the full brainstorm as:

```markdown
## Brainstorm Summary

**Idea**: {title}
**Problem**: {what it solves}
**Vision alignment**: {Strong/Moderate/Weak/Misaligned}

## Exploration

[Key Q&A exchanges — condensed, not raw transcript]

## Challenges Explored

[Which lenses were applied and key findings from each]

## Approaches Considered

| Approach | Description | Key Trade-off |
|----------|-------------|---------------|
| A | ... | ... |
| B | ... | ... |

## Verdict

**Verdict**: {proceed / research / scrap}
**Reasoning**: [2-3 sentences explaining the verdict]
**If proceeding**: [what the issue should focus on, which approach looks promising]
**If researching**: [specific questions to answer before proceeding]
**If scrapping**: [why this doesn't serve the vision, what to focus on instead]
```

Save by running:
```bash
mantle save-brainstorm \
  --title "<idea title slug>" \
  --verdict "<proceed|research|scrap>" \
  --content "<full brainstorm content above>"
```

**Step 8 — Next steps:**
Verdict-aware recommendations:
- proceed → "**Recommended:** `/mantle:add-issue` — create the issue while context is fresh"
- research → "**Recommended:** `/mantle:research` — investigate: [list specific questions from verdict]"
- scrap → "This idea doesn't align with the vision. Consider focusing on [suggest most relevant existing issue from backlog]"

Present one clear recommendation, then mention alternatives briefly.

## Analysis scratchpad

Before synthesising findings, drafting verdicts, or making vision alignment assessments, use `<analysis>` blocks to organise thinking. These blocks are internal scratchpad — do NOT show them to the user. They are stripped by `sanitize.strip_analysis_blocks()` when saving.

```
<analysis>
- Vision alignment evidence for/against
- Which assumptions held up? Which cracked?
- What pattern emerged from the challenge?
- Honest verdict assessment
</analysis>
```

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "brainstorm"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).

#### Design decisions

- **`allowed-tools: Read, Bash(mantle *)`**: Same restriction as challenge.md — can read project files and invoke mantle CLI, nothing else. No web search (that's what `/mantle:research` is for after a "research" verdict).
- **No `context: fork`**: Unlike challenge.md which forks, brainstorm runs in main conversation so the user can continue working after it completes (e.g., immediately run `/mantle:add-issue`).
- **Analysis scratchpad**: Uses `<analysis>` blocks for internal reasoning before presenting vision alignment and verdict. Stripped by sanitize module when saving.
- **Vision alignment is non-negotiable**: Even if all other steps scale down for small features, the vision check always runs at full depth. This is the killer feature.