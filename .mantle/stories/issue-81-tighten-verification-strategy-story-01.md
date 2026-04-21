---
issue: 81
title: Reword verify.md Step 3 and build.md Step 8 verifier handoff to config-first
  precedence
status: completed
failure_log: null
tags:
- type/story
- status/completed
---

## User Story

As a maintainer, I want the verification-strategy handoff in `verify.md` and
`build.md` to state config.md-first precedence unambiguously so that
sub-agents don't skip the config.md check or invoke `mantle introspect-project`
on every verify call.

## Depends On

None — independent.

## Approach

Prose-only edit across two Claude Code command templates. Both sites currently
use a loose conditional ("If no verification strategy is configured") that
agents parse as "run introspect-project". Reword each site with an explicit
three-step precedence — check config.md first, use it verbatim if present, fall
back to introspect-project only if absent or empty. No code changes, no new CLI
surface, no test changes. The issue's slice is `claude-code` only.

## Implementation

### claude/commands/mantle/verify.md (modify)

Step 3 "Load verification strategy" (currently lines ~97–122) needs its
branching prose rewritten. Keep the introspect-project first-use flow body
(the numbered list and AskUserQuestion pattern) intact, but restructure the
section so the precedence is unambiguous.

Replace the existing Step 3 body (the paragraph "Read $MANTLE_DIR/config.md
directly…" plus the two `**If no strategy is found**` / `**If a strategy
is found**` branches) with precedence-first directive prose shaped like:

> 1. Check `$MANTLE_DIR/config.md` for a `verification_strategy` field
>    with a non-empty value.
> 2. If present, display it and use it verbatim for the rest of this run.
> 3. Only if absent or empty, fall back to `mantle introspect-project` as a
>    last-resort first-use flow — then nest the existing 6-step
>    introspect-project procedure here.

Use directive imperatives: "Check", "If present, use it verbatim", "Only
if absent or empty". Avoid loose conditionals like "If no strategy is
configured".

### claude/commands/mantle/build.md (modify)

Step 8 "Verify (agent)" (currently lines ~371–399) spawns a sub-agent with
override bullets. The offending bullet reads:

> - If no verification strategy is configured, run
>   `mantle introspect-project` …

Replace that bullet with precedence-first directive prose:

> - **Verification strategy precedence**: check
>   `$MANTLE_DIR/config.md` for a non-empty `verification_strategy` field
>   first. If present, use it verbatim. Only if absent or empty, run
>   `mantle introspect-project` as a last-resort fallback, then save the
>   generated strategy via
>   `mantle save-verification-strategy --strategy "<generated strategy>"`.

Keep the final bullet ("Don't ask the user to define a strategy…") but
reword it to match the precedence framing:

> - Do not ask the user to define a strategy — use the configured value if
>   present, otherwise introspection.

#### Design decisions

- **Nest the first-use flow under "only if"** rather than present it as a
  parallel branch. Agents read flat alternatives as "pick one"; nesting
  forces them to read "check config.md" before they can reach the fallback.
- **Do not touch `fix.md`**: its Step 8 already reads "Read config.md for
  the verification strategy" with no introspect-project fallback. It is
  directive enough.
- **Do not touch Step 7.5 (Strategy evolution)** in verify.md: that path
  intentionally starts from the current loaded strategy, not from config.md.

## Tests

None. These are prose templates consumed by Claude Code sub-agents, not code
paths. The acceptance-criteria verification in Step 8 of the build pipeline
will run a smoke `/mantle:verify` and `just check` against this project
(which has a configured `verification_strategy`) to confirm that
`mantle introspect-project` is not invoked (ac-03) and the repository
remains clean (ac-04).