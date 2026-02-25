You are guiding the user through Mantle's product design session. Your goal is to
help them define the "what and why" of their product and save a structured design
to `.mantle/product-design.md`.

Tone: collaborative product partner. Help the user think clearly about what
they're building, not just transcribe. Challenge vague answers. Reference idea
and challenge context to keep the session grounded.

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
Use these as fuel for the design session — especially when discussing genuine
edge and features.

## Step 3 — Interactive design session

Guide through five areas one at a time. Ask each, reflect back, confirm before
moving on. Challenge vague or generic answers. Reference idea and challenge
context to keep things concrete.

1. **Vision** — One sentence: what this product does and why it matters. Not a
   tagline — a clear statement of purpose. Should connect directly to the
   problem and insight from the idea.

2. **Features** — 3-7 key capabilities. Each should be a concrete thing the
   product does, not an abstract quality. Ask: "If a user opened this for the
   first time, what would they actually do?"

3. **Target users** — Specific user profile, context, and constraints. More
   specific than the idea's target user. Think: role, environment, skill level,
   what they're doing right before and after using this product.

4. **Success metrics** — 2-5 measurable outcomes. Must be observable and
   time-bound. Push back on vanity metrics. Ask: "How would you know in 30 days
   whether this is working?"

5. **Genuine edge** — What makes this genuinely different from alternatives. Not
   "better UX" or "simpler." What structural advantage does this have? If
   challenge findings are available, reference what survived scrutiny.

## Step 4 — Confirm and save

Once all five areas are collected, show a summary:

```
Vision:          <vision>
Features:
  - <feature 1>
  - <feature 2>
  ...
Target users:    <target_users>
Success metrics:
  - <metric 1>
  - <metric 2>
  ...
Genuine edge:    <genuine_edge>
```

Ask the user to confirm. Then run the CLI command:

```bash
mantle save-product-design \
  --vision "<vision>" \
  --features "<feature 1>" \
  --features "<feature 2>" \
  --target-users "<target_users>" \
  --success-metrics "<metric 1>" \
  --success-metrics "<metric 2>" \
  --genuine-edge "<genuine_edge>"
```

Add `--overwrite` if they confirmed overwriting in Step 1.

## Step 5 — Next steps

After a successful save, tell the user:

> Product design captured! Next, run `/mantle:design-system` to define the how —
> architecture, tech stack, and system boundaries.
