---
issue: 9
title: Session logging rule and command closing instructions
status: done
failure_log: null
tags:
  - type/story
  - status/done
---

## Implementation

Create a standing rule for automatic session logging in non-command sessions, update the install flow to copy rules, and add session logging closing instructions to existing `/mantle:*` commands.

### claude/rules/session-logging.md

Standing rule that instructs Claude to write a session log at the end of every session in a Mantle project. Covers sessions where no `/mantle:*` commands are used.

```markdown
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
```

### src/mantle/cli/install.py (modify)

Update the install flow to also copy `claude/rules/` files to `~/.claude/rules/`. Add `"rules"` to the list of source directories that get installed alongside `"commands"`, `"agents"`, and `"hooks"`. The same copy-and-manifest logic used for other directories applies.

### claude/commands/mantle/*.md (modify)

Add a session logging closing instruction section to the end of each existing command. Append this block:

```markdown
## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "<command-name>"

Keep the log under ~200 words following the session log format (Summary, What Was Done, Decisions Made, What's Next, Open Questions).
```

Replace `<command-name>` with the actual command name for each file.

Commands to update (all existing commands that represent work sessions):

- `idea.md` — `--command idea`
- `challenge.md` — `--command challenge`
- `research.md` — `--command research`
- `design-product.md` — `--command design-product`
- `design-system.md` — `--command design-system`
- `revise-product.md` — `--command revise-product`
- `revise-system.md` — `--command revise-system`
- `adopt.md` — `--command adopt`

Do NOT add session logging to:

- `help.md` — Informational, not a work session
- `status.md.j2` / `resume.md.j2` — Compiled templates, informational only
- Commands that don't exist yet (plan-issues, shape-issue, plan-stories, implement, verify, review, retrospective) — these will include it when created

### Design decisions

- **Standing rule, not a hook.** A SessionEnd hook would be ideal but Claude Code doesn't support reliable session-end triggers. A standing rule in `.claude/rules/` is always loaded into context and reliably instructs Claude.
- **Skip trivial sessions.** The rule explicitly excludes trivially short sessions to prevent noise in the session log directory.
- **Only update existing commands.** Future commands (plan-issues, implement, etc.) will include session logging instructions when they're created in later issues.
- **Rules directory in install.** Treating `claude/rules/` the same as `claude/commands/` — the install command copies files and tracks them in the manifest.
- **Command name without prefix.** `--command idea` not `--command mantle:idea`. The `mantle:` prefix is a Claude Code slash command convention, not part of the command identity.

## Tests

### tests/cli/test_install.py (modify)

- **install**: copies `rules/session-logging.md` to `~/.claude/rules/`
- **install**: creates `~/.claude/rules/` directory if it doesn't exist
- **install**: rules files tracked in manifest
