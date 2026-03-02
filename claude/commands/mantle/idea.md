You are guiding the user through Mantle's idea capture workflow. Your goal is to
help them articulate a structured idea and save it to `.mantle/idea.md`.

## Step 1 — Check for existing idea

Run `mantle save-idea --help` to confirm the CLI is available, then check
whether `.mantle/idea.md` already exists by reading the file.

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

After a successful save, tell the user:

> Idea captured! Next, run `/mantle:challenge` to stress-test your idea from
> multiple angles before investing in design.

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "idea"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).
