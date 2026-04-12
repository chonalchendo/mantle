---
description: Use when you need to validate whether the building blocks of an idea or issue are technically viable before designing
context: fork
allowed-tools: Read, Bash(mantle *), Agent
---

Identify the fundamental building blocks needed to implement the idea (or
issue) and research whether each one is viable.

This command has two modes:

- **Idea mode** (default) — first-principles research for an early-stage
  product idea. The challenge session (`/mantle:challenge`) stress-tests the
  idea and surfaces what must be true for it to work — assumptions,
  constraints, uncertainties, weaknesses. Research picks up where challenge
  leaves off and gathers evidence for or against each one.
- **Issue mode** (when called with an issue number, e.g. `/mantle:research 54`)
  — technical research for a specific planned issue. The issue's
  "Acceptance Criteria" and "Prerequisites" sections become the building
  blocks. No `idea.md` or challenge transcript is required. Saved as
  `.mantle/research/issue-<NN>-<focus>.md`.

**Mode detection:** if `$ARGUMENTS` parses as an integer matching an issue
file under `.mantle/issues/` or `.mantle/archive/issues/`, use issue mode.
Otherwise use idea mode. Ask the user if ambiguous.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Load context"
3. "Step 3 — Derive building blocks"
4. "Step 4 — Choose focus"
5. "Step 5 — Launch researcher agent"
6. "Step 6 — Save report"
7. "Step 7 — Next steps"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.

Check whether `.mantle/` exists. If not, tell them to run `mantle init` first.

**Mode-specific prerequisites:**

- **Idea mode:** require `$MANTLE_DIR/idea.md`. If missing, tell the user to
  run `/mantle:idea` first. If no challenge transcript exists in
  `$MANTLE_DIR/challenges/`, recommend `/mantle:challenge` first (the
  challenge output is the primary input for deriving building blocks).
  Proceed if the user wants to skip.
- **Issue mode:** require the issue file at
  `$MANTLE_DIR/issues/issue-<NN>-*.md` (or under `archive/issues/`). If
  missing, tell the user the issue number was not found. No `idea.md` or
  challenge transcript is required. If the issue is already shaped
  (`$MANTLE_DIR/shaped/issue-<NN>-shaped.md`), load it too — open questions
  and rabbit holes from shaping make excellent research targets.

## Step 2 — Load context

**Idea mode:** Read `$MANTLE_DIR/idea.md` and extract:
- **Problem** — the specific pain or friction
- **Insight** — the non-obvious truth that enables a new solution
- **Target user** — who it's for
- **Success criteria** — how they'll know it worked

Read all challenge transcripts in `$MANTLE_DIR/challenges/`. Extract:
- **Assumptions surfaced** — what must be true (with confidence levels)
- **First-principles analysis** — the true constraints, stripped of convention
- **What survived** — aspects that held up under scrutiny
- **Weaknesses found** — areas that need evidence
- **Key uncertainties** — what remains unknown
- **"Would change my mind if"** — specific evidence that would flip the verdict

**Issue mode:** Read the issue file (live or archived) and extract:
- **Title** and **Goal / Problem** — what the issue is trying to solve
- **Acceptance Criteria** — the observable outcomes the implementation must
  satisfy
- **Prerequisites** — any questions the issue body lists as requiring
  investigation before shaping
- **Context / Depends On** — constraints that shape the approach

If a shaped-issue file exists (`$MANTLE_DIR/shaped/issue-<NN>-shaped.md`),
also load it and extract the **Open Questions** and **Rabbit holes** from
the chosen approach — these are first-class research targets.

Read any existing research notes in `$MANTLE_DIR/research/` (to build on, not repeat).

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

**Issue mode:** the building blocks come from the issue body. Specifically:
- Each **Prerequisites** question is a building block (already phrased as a
  research question).
- Each **Acceptance Criterion** that depends on an unknown technical
  capability is a building block.
- Each open question or rabbit hole from the shaped issue (if any) is a
  building block.

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
# Idea mode:
mantle save-research --focus "<focus>" --confidence "<N/10>" --content "<report>"

# Issue mode (skips idea.md requirement, names file issue-<NN>-<focus>.md):
mantle save-research --issue <NN> --focus "<focus>" --confidence "<N/10>" --content "<report>"
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
