---
argument-hint: [issue-number]
allowed-tools: Read, Bash(mantle *)
---

Evaluate 2-3 approaches for the issue before decomposing into stories, following
Shape Up methodology.

Be collaborative, focused, and pragmatic. Explore the solution space rather than
jumping to implementation. Surface tradeoffs clearly and push for concrete
approaches, not abstract ones. The user makes the final call.

## Anti-Pattern: "This issue is too simple to shape"

Every issue goes through shaping. A single-file change, a config tweak, a
"straightforward" CRUD endpoint — all of them. "Simple" issues are where
unexamined assumptions cause the most wasted implementation effort. The shaping
can be brief (one approach with a short write-up for truly simple issues), but
you MUST explore approaches and get user approval.

If you catch yourself thinking "this is obvious, just implement it" — that is
the signal to shape more carefully, not less.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check prerequisites"
2. "Step 2 — Load context"
3. "Step 3 — Explore approaches"
4. "Step 4 — Compare and choose"
5. "Step 5 — Save shaped issue"
6. "Step 6 — Next steps"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check prerequisites

Check whether `.mantle/`, `.mantle/state.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first.
- Read `state.md` and verify status is `planning`. If not, tell them the current
  status and what step to run next.

## Step 2 — Load context

Read and internalise:
- `.mantle/product-design.md` — the product definition
- `.mantle/system-design.md` — the system architecture
- Any files in `.mantle/issues/` — the issue breakdown
- Any files in `.mantle/learnings/` — past learnings from previous issues

If past learnings exist, summarise key patterns before starting:

> **Learnings from previous issues:**
> - [summarise each learning's key recommendations]

If the user provided `$ARGUMENTS`, use that as the issue number.
Otherwise, ask the user which issue number they want to shape, or confirm if one
is already active in state.md.

## Step 3 — Explore approaches

### Conversation discipline

- **One question per message.** When exploring an approach, ask about one aspect
  at a time (e.g., appetite, then tradeoffs, then rabbit holes). Do not dump
  multiple questions in one message.
- **Prefer multiple choice.** When asking about appetite, scope decisions, or
  no-gos, present concrete options rather than open-ended questions.
- **Reflect back, then confirm.** After each answer, restate what you understood
  and confirm before moving on.

For each approach (aim for 2-3), work through:

1. **Name** — a short, memorable label
2. **Description** — what this approach looks like concretely
3. **Appetite** — how much time/effort this approach would take (small batch:
   1-2 days, medium batch: 3-5 days, large batch: 1-2 weeks)
4. **Tradeoffs** — what you gain, what you give up
5. **Rabbit holes** — what could go wrong or take longer than expected
6. **No-gos** — what this approach explicitly does NOT include

Work through approaches interactively. Ask the user questions. Don't dump all
approaches at once — explore one, discuss, then move to the next.

## Step 4 — Compare and choose

Present a side-by-side comparison:

| | Approach A | Approach B | Approach C |
|---|---|---|---|
| Appetite | ... | ... | ... |
| Key benefit | ... | ... | ... |
| Key risk | ... | ... | ... |
| Complexity | ... | ... | ... |

Use AskUserQuestion to let the user choose:

1. **Which approach?** — present each approach as an option with its key benefit
   as the description
2. **Confirm appetite** — present small/medium/large batch as options

Then ask (as free text) if there are any open questions to note before planning.

## Step 5 — Save shaped issue

Compile the full shaping write-up and save using the CLI:

```bash
mantle save-shaped-issue \
  --issue <number> \
  --title "<issue title>" \
  --approaches "<approach 1>" --approaches "<approach 2>" \
  --chosen-approach "<selected approach name>" \
  --appetite "<small batch|medium batch|large batch>" \
  --content "<full shaping write-up with all approaches, tradeoffs, rationale>" \
  --open-questions "<question 1>" --open-questions "<question 2>"
```

## Step 6 — Next steps

After a successful save, briefly assess this session before recommending next steps:

- Did shaping surface open questions about technical feasibility?
- Does the chosen approach align with the current system design, or does it change it?
- Were there unknowns that could benefit from targeted research?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:plan-stories` — default. Recommend when the issue is shaped and ready for decomposition into implementable stories.
- `/mantle:research` — recommend when shaping revealed unknown technical areas that should be investigated before committing to implementation.
- `/mantle:revise-system` — recommend when the chosen approach changes the system design in ways that should be documented first.

**Default:** `/mantle:plan-stories` if nothing suggests otherwise.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]
