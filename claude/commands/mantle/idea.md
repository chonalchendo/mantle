---
allowed-tools: Read, Bash(mantle *)
---

Capture a structured idea through conversation and save it to `.mantle/idea.md`.

Before starting, use TaskCreate to create a task for each step:

1. "Step 1 — Check for existing idea"
2. "Step 2 — Gather the idea"
3. "Step 3 — Confirm and save"
4. "Step 4 — Next steps"

As you start each step, use TaskUpdate to set it to `in_progress`. When
complete, use TaskUpdate to set it to `completed`.

## Step 1 — Check for existing idea

First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.

Run `mantle save-idea --help` to confirm the CLI is available, then check
whether `$MANTLE_DIR/idea.md` already exists by reading the file.

- If it exists, warn the user and ask whether they want to overwrite it.
- If they decline, stop here.
- If `.mantle/` does not exist, tell them to run `mantle init` first.

## Step 2 — Gather the idea

Have a short conversation to capture four things:

1. **Problem** — What specific pain or friction exists? Be concrete — name the
   situation, who feels it, and why current solutions fall short. *(one or two
   sentences)*
2. **Insight** — What non-obvious truth makes a new solution possible? This is
   the lever — the thing most people miss. *(one or two sentences)*
3. **Target user** — Who is this for? Be specific — role, context, skill level.
4. **Success criteria** — How will you know this worked? List 2–5 measurable
   outcomes.

Ask for each one in turn. Reflect back what you heard and confirm before
moving on. Keep the tone curious and encouraging — challenge vague answers
gently.

## Step 3 — Confirm and save

Once all four are collected, show a summary:

```
Problem:          <problem>
Insight:          <insight>
Target user:      <target_user>
Success criteria:
  - <criterion 1>
  - <criterion 2>
  ...
```

Ask the user to confirm. Then run the CLI command:

```bash
mantle save-idea \
  --problem "<problem>" \
  --insight "<insight>" \
  --target-user "<target_user>" \
  --success-criteria "<criterion 1>" \
  --success-criteria "<criterion 2>"
```

Add `--overwrite` if they confirmed overwriting in Step 1.

## Step 4 — Next steps

After a successful save, briefly assess this session before recommending next steps:

- Does the idea involve technology or domains the user seems unfamiliar with?
- Did the user express uncertainty about whether something is technically feasible?
- How well-formed is the problem/insight — is it concrete or still fuzzy?

**Valid next commands** (recommend the best fit, not all of them):

- `/mantle:challenge` — default. Recommend when the idea is well-formed and ready for stress-testing.
- `/mantle:research` — recommend when the idea depends on unfamiliar technology or the user expressed uncertainty about feasibility. Research gathers evidence before investing in design.
- `/mantle:design-product` — recommend only when the user has very high confidence and wants to move fast. Note that skipping validation carries risk.

**Default:** `/mantle:challenge` if nothing suggests otherwise.

Present one clear recommendation with a reason, then mention alternatives briefly:

> **Recommended next step:** `/mantle:<command>` — [reason based on what you observed in this session]
>
> Other options: [brief list of alternatives with one-line descriptions]

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "idea"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).
