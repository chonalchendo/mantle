---
description: Identify the fundamental building blocks needed to implement the idea and research whether each one is viable.
context: fork
allowed-tools: Read, Bash(mantle *), Agent
---

Identify the fundamental building blocks needed to implement the idea and
research whether each one is viable.

This is first-principles research. The challenge session (`/mantle:challenge`)
stress-tests the idea and surfaces what must be true for it to work — the
assumptions, constraints, uncertainties, and weaknesses. Research picks up where
challenge leaves off: it takes those findings and gathers evidence for or
against each one.

## Step 1 — Check prerequisites

Check whether `.mantle/` and `.mantle/idea.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first.
- If `idea.md` does not exist, tell them to run `/mantle:idea` first.
- If no challenge transcript exists in `.mantle/challenges/`, recommend running
  `/mantle:challenge` first — the challenge output is the primary input for
  deriving building blocks. Proceed if the user wants to skip.

## Step 2 — Load context

Read `.mantle/idea.md` and extract:
- **Problem** — the specific pain or friction
- **Insight** — the non-obvious truth that enables a new solution
- **Target user** — who it's for
- **Success criteria** — how they'll know it worked

Read all challenge transcripts in `.mantle/challenges/`. Extract:
- **Assumptions surfaced** — what must be true (with confidence levels)
- **First-principles analysis** — the true constraints, stripped of convention
- **What survived** — aspects that held up under scrutiny
- **Weaknesses found** — areas that need evidence
- **Key uncertainties** — what remains unknown
- **"Would change my mind if"** — specific evidence that would flip the verdict

Read any existing research notes in `.mantle/research/` (to build on, not repeat).

## Analysis scratchpad

Before synthesising findings, choosing focus areas, or making recommendations,
use `<analysis>` blocks to organise your thinking. These blocks are internal
scratchpad — do NOT show them to the user. Strip them from any saved output.

```
<analysis>
- What are the strongest/weakest assumptions from the challenge?
- Which building block carries the most risk?
- What evidence would resolve the biggest uncertainty?
- How do prior research findings narrow the search space?
</analysis>
```

Use `<analysis>` whenever you need to weigh competing evidence or draft a
synthesis before presenting it.

## Step 3 — Derive building blocks

The building blocks come from the challenge output. Each assumption that must
hold, each constraint identified through first-principles analysis, and each
uncertainty flagged — these are the things that need evidence.

Working with the user, synthesise the challenge findings into a numbered list of
building blocks. A building block is an irreducible capability or condition the
solution depends on. For each one, name:

- **What it is** (one line)
- **Where it came from** (which challenge finding — assumption, constraint,
  uncertainty, or weakness)
- **What we need to know** (the specific question research should answer)

If no challenge transcript exists, derive building blocks directly from the idea
by asking:
- What must be true for this to work?
- What does the system need to be able to do?
- What existing tools, protocols, or platforms does this depend on?

Ask the user to confirm or adjust the list before proceeding.

## Step 4 — Choose focus

If this is the first `/mantle:research` run, suggest starting with the building
block that carries the most risk — the one where the challenge flagged lowest
confidence or where "would change my mind if" points to findable evidence.

If prior research exists, suggest the next uncovered building block. Present the
list and let the user choose. Map their choice to one of the focus categories
for the CLI:

- **feasibility** — Can this building block actually work? Technical proof.
- **technology** — What specific tools/libraries/APIs implement this block?
- **competitive** — Has someone already built this block? Can we use or learn from it?
- **user-needs** — Does the target user actually need/want what this block provides?
- **general** — Broad landscape research when a block spans multiple concerns.

## Step 5 — Launch researcher agent

Use the Agent tool to spawn a subagent (subagent_type: "researcher") with
the following prompt:

```
Research the viability of a specific building block for an early-stage product
idea.

## Idea Context

Problem: <problem from idea.md>
Insight: <insight from idea.md>
Target user: <target_user from idea.md>

## Challenge Findings

<Relevant excerpts: the assumption/constraint/uncertainty this block addresses,
the confidence level assigned during challenge, and what evidence was requested>

## Building Block Under Investigation

<name and description of the chosen building block>

Where it came from: <which challenge finding>
What we need to know: <the specific research question>

## Focus: <chosen focus category>

<Include any prior research summaries that relate to this block>
```

## Step 6 — Save report

After the agent returns, extract:
- The full report (for --content)
- The confidence rating (for --confidence, in N/10 format)

Save by running:

```bash
mantle save-research --focus "<focus>" --confidence "<N/10>" --content "<report>"
```

## Step 7 — Next steps

After a successful save, review the building block list and tell the user:

- Which blocks now have research coverage and what the evidence says
- Which blocks remain unresearched (suggest the highest-risk one next)
- Whether any challenge assumptions have been confirmed or refuted
- Whether the evidence so far supports proceeding to design

Then assess this session before recommending next steps:

- How many building blocks still lack research, especially high-risk ones?
- What is the overall confidence level across researched blocks?
- Did any findings contradict earlier challenge assumptions?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:research` — recommend when unresearched high-risk building blocks remain, especially those flagged during challenge.
- `/mantle:design-product` — recommend when enough evidence exists to proceed with confidence.
- `/mantle:challenge` — recommend rarely, when research uncovered information that fundamentally changes earlier challenge assumptions and they should be re-evaluated.

**Default:** `/mantle:research` if unresearched blocks remain; `/mantle:design-product` once coverage is sufficient.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "research"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).
