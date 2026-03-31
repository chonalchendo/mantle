---
allowed-tools: Read, Bash(mantle *)
---

Decompose the product into first-principles building blocks and save a structured
design to `.mantle/product-design.md`.

Think from first principles, not just list features. Challenge vague answers.
Reference idea and challenge context to keep the session grounded.

## Step 1 — Check prerequisites

Check whether `.mantle/` and `.mantle/idea.md` exist by reading them.

- If `.mantle/` does not exist, tell them to run `mantle init` first.
- If `idea.md` does not exist, tell them to run `/mantle:idea` first.
- If `.mantle/product-design.md` already exists, warn the user and ask whether
  they want to overwrite it. If they decline, stop here.

## Step 2 — Load context

Read `.mantle/idea.md` and extract:
- **Problem** — the specific pain or friction
- **Insight** — the non-obvious truth that enables a new solution
- **Target user** — who it's for
- **Success criteria** — how they'll know it worked

Check for challenge files in `.mantle/challenges/`. If any exist, read the most
recent one and extract key findings (assumptions surfaced, verdict, weaknesses).
Use these as fuel for the design session — especially when discussing principles
and building blocks.

Check for research files in `.mantle/research/`. If any exist, read them all and
extract key findings — technical feasibility, existing solutions, competitive
landscape, technology options, and risks. Research findings should directly inform
the prior art, building blocks, and principles discussions. Reference specific
research conclusions rather than making the user repeat what was already explored.

## Analysis scratchpad

Before synthesising context, challenging user answers, or making design
recommendations, use `<analysis>` blocks to organise your thinking. These
blocks are internal scratchpad — do NOT show them to the user. Strip them from
any saved output.

```
<analysis>
- What did the challenge/research establish that constrains this design choice?
- Is this answer a genuine principle or an aspiration disguised as one?
- What's missing from the building blocks list?
- Do the success metrics actually measure what matters?
</analysis>
```

Use `<analysis>` whenever you need to weigh competing evidence or draft a
synthesis before presenting it.

## Step 3 — Interactive design session

Guide through seven areas one at a time. Ask each, reflect back, confirm before
moving on. Challenge vague or generic answers. Reference idea, challenge, and
research context to keep things concrete and grounded in evidence.

1. **Vision** — One sentence: what this product does and why it matters. Not a
   tagline — a clear statement of purpose. Should connect directly to the
   problem and insight from the idea.

2. **Principles** — Fundamental truths about this problem space. What constraints
   are non-negotiable? What must be true for any solution to work? These are not
   goals — they are structural realities. Push back on aspirational statements
   disguised as principles.

3. **Building blocks** — Essential primitives. What are the smallest correct
   pieces that, if right, make everything else follow naturally? Think atoms, not
   molecules. Ask: "If you could only get three things exactly right, which three
   would make the rest inevitable?"

4. **Prior art** — What already exists that should be adopted or recombined? What
   patterns from other tools or technologies apply? What doesn't need to be built
   from scratch? Push back on reinventing the wheel.

5. **Composition** — How do the building blocks fit together? What's the product
   that emerges when you assemble the primitives with the prior art? This is
   where features become an output, not an input.

6. **Target users** — Specific user profile, context, and constraints. More
   specific than the idea's target user. Think: role, environment, skill level,
   what they're doing right before and after using this product.

7. **Success metrics** — 2-5 measurable outcomes. Must be observable and
   time-bound. Push back on vanity metrics. Ask: "How would you know in 30 days
   whether this is working?"

## Step 4 — Confirm and save

Once all seven areas are collected, show a summary:

```
Vision:          <vision>
Principles:
  - <principle 1>
  - <principle 2>
  ...
Building blocks:
  - <block 1>
  - <block 2>
  ...
Prior art:
  - <prior 1>
  - <prior 2>
  ...
Composition:     <composition>
Target users:    <target_users>
Success metrics:
  - <metric 1>
  - <metric 2>
  ...
```

Ask the user to confirm. Then run the CLI command:

```bash
mantle save-product-design \
  --vision "<vision>" \
  --principles "<principle 1>" \
  --principles "<principle 2>" \
  --building-blocks "<block 1>" \
  --building-blocks "<block 2>" \
  --prior-art "<prior 1>" \
  --prior-art "<prior 2>" \
  --composition "<composition>" \
  --target-users "<target_users>" \
  --success-metrics "<metric 1>" \
  --success-metrics "<metric 2>"
```

Add `--overwrite` if they confirmed overwriting in Step 1.

## Step 5 — Next steps

After a successful save, briefly assess this session before recommending next steps:

- Did the design session surface building blocks with unknown technical feasibility?
- Were there areas where you lacked evidence to make confident design choices?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:design-system` — default. Recommend in most cases to define the how — architecture, tech stack, and system boundaries.
- `/mantle:research` — recommend when the design session revealed building blocks that need technical investigation before system design can proceed.

**Default:** `/mantle:design-system` if nothing suggests otherwise.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "design-product"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).
