---
issue: 22
title: Shape-issue command prompt with learnings integration
status: completed
failure_log: null
tags:
  - type/story
  - status/completed
---

## Implementation

Create the static Claude Code command `shape-issue.md` that guides the interactive shaping session, following Shape Up methodology. The AI explores approaches interactively, presents a comparison, and saves the shaped artifact.

### `claude/commands/mantle/shape-issue.md` (new file)

Static command prompt following the pattern of `design-product.md` and `plan-issues.md`. The AI adopts the persona of a senior product engineer who shapes work before building.

#### Structure

**Step 1 — Check prerequisites**

Read `.mantle/state.md` and verify:
- `.mantle/` exists (if not, tell user to run `mantle init`)
- Status is `planning` (if not, tell them the current status and what to run next)

**Step 2 — Load context**

Read and internalise:
- `.mantle/product-design.md` — the product definition
- `.mantle/system-design.md` — the system architecture
- `.mantle/issues/` — the issue breakdown
- `.mantle/learnings/` — past learnings from previous issues

If past learnings exist, summarise key patterns before starting:

> **Learnings from previous issues:**
> - [summarise each learning's key recommendations]

Ask the user which issue number to shape, or confirm if one is already active in state.md.

**Step 3 — Explore approaches (2-3)**

For each approach, work through interactively:
1. **Name** — short, memorable label
2. **Description** — what this approach looks like concretely
3. **Appetite** — how much time/effort (small batch: 1-2 days, medium: 3-5 days, large: 1-2 weeks)
4. **Tradeoffs** — what you gain, what you give up
5. **Rabbit holes** — what could go wrong or take longer than expected
6. **No-gos** — what this approach explicitly does NOT include

Approaches are explored one at a time. The AI asks questions and discusses each before moving to the next.

**Step 4 — Compare and choose**

Present a side-by-side comparison table (appetite, key benefit, key risk, complexity). Ask the user to:
1. Commit to an approach
2. Confirm the appetite
3. Note any open questions

**Step 5 — Save shaped issue**

Compile the full shaping write-up and save via:

```bash
mantle save-shaped-issue \
  --issue <number> \
  --title "<issue title>" \
  --approaches "<approach 1>" --approaches "<approach 2>" \
  --chosen-approach "<selected approach name>" \
  --appetite "<small batch|medium batch|large batch>" \
  --content "<full shaping write-up>" \
  --open-questions "<question 1>" --open-questions "<question 2>"
```

**Step 6 — Next steps**

After a successful save:

> Issue shaped! Next, run `/mantle:plan-stories` to decompose into implementable stories.

#### Persona

Senior product engineer who shapes work before building. Collaborative, focused, and pragmatic. Surfaces tradeoffs clearly. Pushes for concrete approaches, not abstract ones. The user makes the final call.

### Design decisions

- **Static command, not compiled.** The shape-issue command reads context dynamically during the session. No vault state needs to be baked in at compile time.
- **Interactive exploration, not dump.** Approaches are explored one at a time with discussion, not presented all at once. This matches how Shape Up works — the shaping process itself surfaces insights.
- **Learnings loaded as context.** Past learnings from `.mantle/learnings/` are summarised at the start of the session so the user doesn't repeat mistakes from previous issues. This implements user story 58.
- **Appetite as commitment device.** The appetite is a fixed time budget from Shape Up. It prevents scope creep — if work exceeds the appetite, it's descoped, not extended.
- **Open questions captured explicitly.** Unresolved questions are saved in the shaped artifact so `plan-stories` can account for them when decomposing work.

## Tests

No automated tests for this story. The static command prompt is a markdown file that guides Claude's behaviour — it's verified by manual usage and the acceptance criteria in the parent issue.

Verification:
- The `shape-issue.md` file exists at `claude/commands/mantle/shape-issue.md`
- Running `mantle install` copies it to `~/.claude/commands/mantle/`
- The command references `mantle save-shaped-issue` which is registered in story 2
