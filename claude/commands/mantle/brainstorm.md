---
description: Use when you want to explore and validate a new feature idea against your existing product vision
allowed-tools: Read, Bash(mantle *)
---

Explore and validate a feature idea for an existing project. Combine structured
exploration with selective challenge techniques, scaled to the idea's complexity.
The goal is to determine whether this idea serves the vision — not to rubber-stamp it.

Be rigorous but efficient. One question per message. Scale challenge depth to the
idea's scope. Don't over-process small features.

## Iron Laws

These rules are absolute. There are no exceptions.

1. **NO rubber-stamping.** Every idea must survive a vision alignment check.
2. **NO skipping the vision check.** Even "obvious" features can be scope creep.
3. **NO premature verdicts.** Complete the exploration before judging.

### Red Flags — thoughts that mean STOP

| Thought | Reality |
|---------|---------|
| "This obviously fits the vision, skip the check" | Obvious-seeming features are where scope creep hides. |
| "The user seems excited, I'll be positive" | Excitement does not equal alignment. Check the vision. |
| "This is a small feature, no need for challenge" | Small features still get assumption surfacing. Scale the depth, don't skip it. |
| "I've already formed my opinion" | Complete all steps before synthesising. Early opinions bias the process. |

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Load context"
3. "Step 3 — Explore the idea"
4. "Step 4 — Vision alignment check"
5. "Step 5 — Selective challenge"
6. "Step 6 — Propose approaches"
7. "Step 7 — Synthesise and save"
8. "Step 8 — Next steps"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Record the stage:

    mantle stage-begin brainstorm

First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.

Read `$MANTLE_DIR/state.md` and verify:

- `.mantle/` exists. If not, tell the user to run `mantle init` first.
- `$MANTLE_DIR/product-design.md` exists. If not, tell the user to run
  `/mantle:design-product` first — brainstorm requires a vision to evaluate
  against.

## Step 2 — Load context

Read and internalise:

- `$MANTLE_DIR/product-design.md` — the stubborn vision (what and why).
  Extract: vision statement, target user, success metrics, design principles.
- `$MANTLE_DIR/system-design.md` — the flexible details (how). Note
  architecture boundaries.
- `$MANTLE_DIR/issues/` — existing backlog (for overlap and conflict
  detection). Read all issue files.
- `$MANTLE_DIR/brainstorms/` — past brainstorms including scrapped ideas
  (avoid retreading rejected ideas without new evidence). Read all brainstorm
  files if the directory exists.
- `$MANTLE_DIR/learnings/` — past learnings that may inform this brainstorm.

Display context summary:

> **Product vision**: {one-line vision from product-design.md}
> **Existing issues**: {count} in backlog
> **Past brainstorms**: {count} ({scrapped count} scrapped)

If past brainstorms exist for a similar topic, flag it:

> **Note**: A similar idea was brainstormed on {date} and {verdict}.
> [Brief reason.]

## Step 3 — Explore the idea

Interactive conversation, one question at a time:

1. What's the idea? (let the user describe it freely — open-ended)
2. What problem does this solve for the target user defined in
   product-design.md? (focus question)
3. What's the non-obvious insight — why now, why this approach? (depth question)
4. How big is this? Present as multiple choice:
   - **Small feature** — single issue, 1-3 stories, touches one slice
   - **Medium capability** — 1-2 issues, new module or significant extension
   - **Large paradigm shift** — multiple issues, rethinks a core assumption

### Rules

- **One question per message.** Do not dump multiple questions.
- **Prefer multiple choice** where appropriate.
- **Reflect back and confirm** before moving on.
- **3-5 exchanges total** for exploration.

## Step 4 — Vision alignment check

The non-negotiable step. Use `<analysis>` scratchpad to reason through:

- Does this idea directly serve the vision statement in product-design.md?
- Does it advance any of the success metrics?
- Does it conflict with any design principles?
- Does it duplicate or conflict with any existing issue?
- Is this the most important thing to work on right now, given the current
  backlog?
- Would the target user (as defined in product-design.md) actually want this?

```
<analysis>
- Vision alignment evidence for/against
- Which existing issues overlap or conflict
- Priority relative to current backlog
- Target user relevance
</analysis>
```

Present the alignment assessment honestly:

> **Vision alignment**: {Strong / Moderate / Weak / Misaligned}
> **Rationale**: {1-2 sentences connecting the idea to (or disconnecting it
> from) the vision}
> **Existing overlap**: {None / Partial overlap with issue-NN / Duplicate of
> issue-NN}
> **Priority assessment**: {High — addresses gap in current backlog / Medium —
> nice to have / Low — backlog has more pressing items}

If alignment is Weak or Misaligned, be direct but respectful. Explain why and
suggest what to focus on instead.

## Step 5 — Selective challenge

Scale challenge depth based on the idea's size (from step 3):

- **Small features** (1-3 exchanges): Assumption surfacing only. Name 2-3
  assumptions, ask which ones the user is least confident about, push on those.

- **Medium capabilities** (3-5 exchanges): Assumption surfacing +
  first-principles analysis + devil's advocate. Weave between lenses based on
  conversation flow.

- **Large paradigm shifts** (5-8 exchanges): All five lenses (assumption
  surfacing, first-principles, devil's advocate, pre-mortem, competitive
  analysis). Full treatment.

### Rules

- **Follow threads.** When a response is weak or hand-wavy, push harder on
  that specific point. Don't let them off the hook.
- **Don't accept hand-wavy answers.** If the response uses "should",
  "probably", "I think", or "in theory" — push harder.
- **Acknowledge strong responses** briefly and move on to the next attack
  vector.
- **Be specific.** "What about competition?" is weak. "Tool X already does
  this with Y users — why would someone use your approach?" is strong.

## Step 6 — Propose 2-3 lightweight approaches

For ideas that survived the vision check and challenge (likely "proceed" or
"research" verdicts):

- Name each approach in 1-2 words
- One-line description of what it looks like
- Key trade-off (what you gain vs what you give up)
- Rough appetite (small / medium / large)

This is NOT full shaping — just enough to understand feasibility and scope.
Skip this step entirely if the verdict is clearly "scrap".

## Analysis scratchpad

Before synthesising findings, drafting verdicts, or making recommendations, use
`<analysis>` blocks to organise your thinking. These blocks are internal
scratchpad — do NOT show them to the user. Strip them from any saved output.

```
<analysis>
- Which assumptions held up? Which cracked under pressure?
- What pattern emerged across the challenge?
- Where was the user's response weakest?
- What's the honest verdict?
</analysis>
```

Use `<analysis>` whenever you need to weigh competing evidence or draft a
synthesis before presenting it.

## Step 7 — Synthesise and save

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

## Step 8 — Next steps

After a successful save, briefly assess this session before recommending
next steps:

- What was the verdict and how confident is the assessment?
- Were there high-risk assumptions that remain unvalidated?
- Does the idea require technical investigation before committing?

**Verdict-aware recommendations:**

- **proceed** — "**Recommended:** `/mantle:add-issue` — create the issue while
  context is fresh"
- **research** — "**Recommended:** `/mantle:research` — investigate: [list
  specific questions from verdict]"
- **scrap** — "This idea doesn't align with the vision. Consider focusing on
  [suggest most relevant existing issue from backlog]"

Present one clear recommendation with a reason, then mention alternatives
briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you
> observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]

## Output Format

One line per section of the brainstorm verdict:

- **Verdict**: <proceed / research / scrap> — <one-sentence reasoning>
- **Alignment**: <Strong / Moderate / Weak / Misaligned> — <one-sentence rationale>

Anti-patterns:
- No "I noticed" / "I'll do X next" framing
- No restating the idea description already presented
- No trailing summary paragraph after the verdict
- No emoji

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "brainstorm"

Keep the log under ~200 words following the session log format (Summary, What
Was Done, Decisions Made, What's Next, Open Questions).
