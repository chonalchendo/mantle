# Session Logging

When working in a project with a `.mantle/` directory, write a session log at the end of every session.

## When to log

At the end of every session — whether or not `/mantle:*` commands were used.

## How to log

Run:

    mantle save-session --content "<body>" [--command <name> ...]

## Body format

Keep the log under ~200 words. Use this structure:

    ## Summary
    One or two sentences summarising what happened this session.

    ## What Was Done
    - Key accomplishments (bulleted list)

    ## Decisions Made
    - Decisions and their brief rationale (or "None")

    ## What's Next
    - Immediate next steps

    ## Open Questions
    - Unresolved questions (or "None")

## Commands used

Include `--command <name>` for each `/mantle:*` command used during the session. Use just the command name without the `mantle:` prefix (e.g., `--command idea`, `--command challenge`).

## Skip conditions

Do not write a session log if:

- The session was trivially short (a single question/answer with no project work)
- The `.mantle/` directory doesn't exist in the current project
