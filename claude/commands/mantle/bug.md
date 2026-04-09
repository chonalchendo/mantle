---
allowed-tools: Read, Bash(mantle *)
---

Quickly capture a structured bug report and save it to `.mantle/bugs/`.

Be helpful and efficient — capture the bug before context is lost. Don't make it
feel like filing a Jira ticket. If the user is clearly frustrated by the bug,
acknowledge it briefly and move on.

## Step 1 — Check prerequisites

First, resolve the project's .mantle/ directory:

    MANTLE_DIR=$(mantle where)

All subsequent `Read` and `Grep`/`Glob` calls in this prompt must use
`$MANTLE_DIR/...` in place of `.mantle/...`.

Run `mantle save-bug --help` to confirm the CLI is available, then check
whether `$MANTLE_DIR/bugs/` exists by reading `$MANTLE_DIR/state.md`.

- If `.mantle/` does not exist, tell the user to run `mantle init` first.
- If `.mantle/bugs/` does not exist, tell the user to create it: `mkdir .mantle/bugs/`

## Step 2 — Gather the bug

Have a brief conversation to capture five things:

1. **What happened?** — One-line summary of the bug. *(one sentence)*
2. **How to reproduce** — Steps or context. If the bug was just encountered in
   the current session, infer reproduction steps from the conversation context
   rather than asking the user to re-explain. *(bullet list or paragraph)*
3. **Expected vs actual** — What should have happened, and what actually
   happened. *(one sentence each)*
4. **Severity** — Suggest a severity based on the description:
   - **blocker** — Cannot proceed with current work, no workaround
   - **high** — Significant impact, workaround exists but is painful
   - **medium** — Noticeable but doesn't block progress
   - **low** — Minor annoyance, cosmetic, or edge case

   Present the suggestion and let the user confirm or adjust.
5. **Related context** — Which issue/story was being worked on (if any), and
   which files are involved. Both optional.

Minimise back-and-forth. If the user provides enough information in one message,
extract all fields and jump straight to confirmation — don't ask redundant
questions.

## Step 3 — Confirm and save

Once all fields are gathered, show a summary:

```
Summary:       <summary>
Severity:      <severity>
Description:   <description>
Reproduction:  <reproduction>
Expected:      <expected>
Actual:        <actual>
Related issue: <related_issue or "None">
Related files: <files or "None">
```

Ask the user to confirm. Then run:

```bash
mantle save-bug \
  --summary "<summary>" \
  --severity "<severity>" \
  --description "<description>" \
  --reproduction "<reproduction>" \
  --expected "<expected>" \
  --actual "<actual>" \
  --related-issue "<issue>" \
  --related-file "<file1>" --related-file "<file2>"
```

Omit `--related-issue` and `--related-file` if not provided.

## Step 4 — Next steps

After a successful save, tell the user:

> Bug captured! It will be surfaced next time you run `/mantle:plan-issues`.

If the bug is a **blocker**, additionally suggest:

> Since this is a **blocker**, consider addressing it in your current work
> session or running `/mantle:plan-issues` to create an issue for it now.

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "bug"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).
