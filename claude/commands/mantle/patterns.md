---
description: Surface recurring themes and confidence trends from past learnings
allowed-tools: Bash(mantle show-patterns)
---

Surface recurring patterns from accumulated `.mantle/learnings/`.

## Step 1 — Run the analysis

Run:

    mantle show-patterns

Present the output verbatim to the user. Do not editorialise — the report is
already shaped.

## Step 2 — Offer a distillation

If the report shows three or more themes with at least two hits each, offer:

> This report groups {N} themes. Want to save an interpretation as a
> distillation so future planning sessions can start from it? Run
> `/mantle:distill patterns` if so.

## Output Format

Step 1 output is the verbatim `mantle show-patterns` report — pass through untouched.

If Step 2 triggers, one-line distillation offer:

- **Distillation offer:** Run `/mantle:distill patterns` to save an interpretation — reason: <N themes, M hits>

Anti-patterns:
- No rewriting, summarising, or editorialising the `mantle show-patterns` output
- No "I noticed" / "I see" / "let me" framing
- No triggering the distillation offer when fewer than 3 themes appear
- No trailing summary paragraph
- No emoji

## Session Logging

Before ending this session, write a session log:

    mantle save-session --content "<body>" --command "patterns"

Keep the log under ~200 words.
